import json
import os
from collections import defaultdict
from pathlib import Path
from threading import Lock

from flask import Flask, abort, jsonify, render_template, request, send_from_directory, url_for
from PIL import Image, ImageOps, UnidentifiedImageError

BASE_DIR = Path(__file__).resolve().parent
DEMO_SAMPLES_DIR = BASE_DIR / "demo_samples"
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

# Detectores independientes: cada uno fue entrenado para una zona distinta.
MODEL_PATHS = {
    "piel": BASE_DIR / "model" / "piel" / "best.pt",
    "orejas": BASE_DIR / "model" / "orejas" / "best.pt",
}
MODEL_LABELS = {"piel": "Piel", "orejas": "Orejas", "general": "Clasificador general Colab"}
COLAB_MODEL_PATH = BASE_DIR / "model" / "colab" / "huellitas_best.keras"
COLAB_LABELS_PATH = BASE_DIR / "model" / "colab" / "class_names_es.json"
COLAB_LABELS = json.loads(COLAB_LABELS_PATH.read_text(encoding="utf-8"))["output_order_from_notebook"]
COLAB_INPUT_SIZE = tuple(json.loads(COLAB_LABELS_PATH.read_text(encoding="utf-8"))["input_size"])
COLAB_MODEL_CACHE = None
MODEL_CACHE = {}
MODEL_LOCK = Lock()
INFERENCE_LOCK = Lock()
IMAGE_SIZE = 416
CONFIDENCE_THRESHOLD = 0.10
IOU_THRESHOLD = 0.45
MAX_DETECTIONS = 20

# Explicaciones breves y educativas; no sustituyen una evaluación veterinaria.
CLASS_INFO = {
    "acne_felino": {
        "nombre": "Acné felino",
        "descripcion": "Suele aparecer como puntos negros o granitos, sobre todo en el mentón. Otras afecciones pueden parecerse.",
        "fuente": "https://vcahospitals.com/know-your-pet/chin-acne-in-cats",
    },
    "tina": {
        "nombre": "Tiña",
        "descripcion": "Infección por hongos dermatofitos que puede afectar piel y pelo; a veces deja zonas redondas sin pelo o descamadas.",
        "fuente": "https://www.vet.cornell.edu/departments-centers-and-institutes/cornell-feline-health-center/health-information/feline-health-topics/ringworm-serious-readily-treatable-affliction",
    },
    "demodicosis": {
        "nombre": "Demodicosis",
        "descripcion": "Un aumento de ácaros Demodex puede inflamar la piel y causar áreas con pérdida de pelo o descamación.",
        "fuente": "https://www.msdvetmanual.com/es/propietarios-de-perros/trastornos-de-la-piel-de-los-perros/infestaci%C3%B3n-por-%C3%A1caros-sarna-acariasis-en-los-perros",
    },
    "sarna_sarcoptica": {
        "nombre": "Sarna sarcóptica",
        "descripcion": "Ácaros contagiosos pueden causar picor intenso, costras y pérdida de pelo. La confirmación requiere revisión veterinaria.",
        "fuente": "https://www.msdvetmanual.com/dog-owners/skin-disorders-of-dogs/mite-infestation-mange-acariasis-scabies-in-dogs",
    },
    "pulgas": {
        "nombre": "Pulgas",
        "descripcion": "Las picaduras pueden irritar la piel; algunos animales reaccionan a la saliva de las pulgas con picor y lesiones.",
        "fuente": "https://www.msdvetmanual.com/integumentary-system/fleas-and-flea-allergy-dermatitis/fleas-in-dogs-and-cats",
    },
    "hotspot": {
        "nombre": "Lesión tipo hot spot",
        "descripcion": "Zona de piel irritada y húmeda que puede aparecer tras rascarse o lamerse repetidamente; es importante revisar su causa.",
        "fuente": "https://www.msdvetmanual.com/integumentary-system/pyoderma/pyoderma-in-dogs-and-cats",
    },
    "acaros_oido": {
        "nombre": "Ácaros del oído",
        "descripcion": "Parásitos del oído externo que pueden provocar rascado, sacudidas de cabeza e inflamación, especialmente en gatos.",
        "fuente": "https://www.msdvetmanual.com/dog-owners/skin-disorders-of-dogs/mite-infestation-mange-acariasis-scabies-in-dogs",
    },
    "otitis": {
        "nombre": "Otitis",
        "descripcion": "Inflamación del conducto auditivo externo. Puede tener causas distintas y necesita examen del oído para identificarlas.",
        "fuente": "https://www.msdvetmanual.com/ear-disorders/otitis-externa/otitis-externa-in-animals",
    },
    "enrojecimiento_hematoma_auricular": {
        "nombre": "Enrojecimiento o hematoma auricular",
        "descripcion": "La clase del modelo agrupa ambos aspectos. Un hematoma es una hinchazón con sangre o líquido bajo la piel del pabellón; la imagen no confirma su causa.",
        "fuente": "https://www.msdvetmanual.com/ear-disorders/diseases-of-the-pinna/auricular-hematomas-in-animals",
    },
}

FEATURED_SAMPLES = (
    ("piel", "tina_01.jpg", "Piel", "Tiña"),
    ("orejas", "acaros_oido_01.jpg", "Orejas", "Ácaros del oído"),
)


def cargar_modelo(categoria):
    """Carga cada YOLO una sola vez, cuando se solicita esa categoría."""
    if categoria in MODEL_CACHE:
        return MODEL_CACHE[categoria]

    ruta = MODEL_PATHS[categoria]
    if not ruta.is_file():
        raise FileNotFoundError(f"Falta el checkpoint de {MODEL_LABELS[categoria].lower()}.")

    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            "Falta Ultralytics. Instala las dependencias con: pip install -r requirements.txt"
        ) from exc

    with MODEL_LOCK:
        if categoria not in MODEL_CACHE:
            MODEL_CACHE[categoria] = YOLO(str(ruta))
    return MODEL_CACHE[categoria]



def cargar_clasificador_colab():
    """Carga de forma diferida el clasificador MobileNetV2 exportado desde Colab."""
    global COLAB_MODEL_CACHE
    if COLAB_MODEL_CACHE is not None:
        return COLAB_MODEL_CACHE
    if not COLAB_MODEL_PATH.is_file():
        raise FileNotFoundError("Falta model/colab/huellitas_best.keras.")
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise RuntimeError("Falta TensorFlow. Instala las dependencias de requirements.txt.") from exc
    with MODEL_LOCK:
        if COLAB_MODEL_CACHE is None:
            model = tf.keras.models.load_model(COLAB_MODEL_PATH, compile=False)
            salida = model.output_shape[-1]
            if salida != len(COLAB_LABELS):
                raise RuntimeError(
                    f"El checkpoint produce {salida} clases, pero class_names_es.json contiene {len(COLAB_LABELS)}."
                )
            COLAB_MODEL_CACHE = model
    return COLAB_MODEL_CACHE


def clasificar_con_colab(imagen):
    """Predice las tres etiquetas con mayor puntaje para la imagen completa."""
    import tensorflow as tf

    model = cargar_clasificador_colab()
    alto, ancho = COLAB_INPUT_SIZE
    imagen_redimensionada = imagen.resize((ancho, alto), Image.Resampling.BILINEAR)
    lote = tf.keras.utils.img_to_array(imagen_redimensionada, dtype="float32")
    lote = tf.expand_dims(lote, axis=0)
    with INFERENCE_LOCK:
        puntajes = model.predict(lote, verbose=0)[0]
    if len(puntajes) != len(COLAB_LABELS):
        raise RuntimeError("La salida del modelo no coincide con el mapa de etiquetas del notebook.")
    indices = sorted(range(len(puntajes)), key=lambda indice: float(puntajes[indice]), reverse=True)[:3]
    resultados = []
    for indice in indices:
        clase = COLAB_LABELS[indice]
        resultados.append({
            "clase": clase["label_es"],
            "clase_origen": clase["source"],
            "especie": clase["species"],
            "confianza": float(puntajes[indice]),
            "descripcion": (
                f"Etiqueta de entrenamiento: {clase['source']}. El clasificador evalúa la imagen completa; "
                "este resultado no localiza una lesión ni confirma una enfermedad."
            ),
            "fuente": "",
        })
    return resultados


def info_clase(nombre):
    clave = str(nombre).strip().lower()
    return CLASS_INFO.get(clave, {
        "nombre": clave.replace("_", " ").capitalize(),
        "descripcion": "El detector marcó una región parecida a esta clase. La imagen por sí sola no confirma una enfermedad.",
        "fuente": "",
    })


@app.route("/")
def index():
    muestras = []
    for categoria, filename, titulo, etiqueta in FEATURED_SAMPLES:
        if (DEMO_SAMPLES_DIR / categoria / filename).is_file():
            muestras.append({
                "categoria": categoria,
                "titulo": titulo,
                "etiqueta": etiqueta,
                "imagen": url_for("foto_muestra", categoria=categoria, filename=filename),
            })
    return render_template("index.html", muestras=muestras)


@app.route("/demo-samples/<categoria>/<path:filename>")
def foto_muestra(categoria, filename):
    if categoria not in MODEL_PATHS:
        abort(404)
    carpeta = DEMO_SAMPLES_DIR / categoria
    if not carpeta.is_dir():
        abort(404)
    return send_from_directory(carpeta, filename, max_age=3600)


@app.errorhandler(413)
def archivo_demasiado_grande(_error):
    return jsonify(error="La imagen supera el límite de 8 MB."), 413


@app.route("/predict", methods=["POST"])
def predict():
    categoria = (request.form.get("categoria") or "").strip().lower()
    if categoria == "dientes":
        return jsonify(error="El módulo dental aún no está disponible: falta un dataset etiquetado y un modelo validado."), 422
    if categoria not in MODEL_PATHS and categoria != "general":
        return jsonify(error="Selecciona piel, orejas o el clasificador general de Colab."), 400

    archivo = request.files.get("imagen")
    if not archivo or archivo.filename == "":
        return jsonify(error="No se envió ninguna imagen."), 400

    try:
        with Image.open(archivo.stream) as original:
            imagen = ImageOps.exif_transpose(original).convert("RGB")
            imagen.load()
    except (UnidentifiedImageError, OSError, ValueError):
        return jsonify(error="No pude leer la imagen. Usa un archivo JPG, PNG o WebP válido."), 400

    if categoria == "general":
        try:
            resultados = clasificar_con_colab(imagen)
        except FileNotFoundError as exc:
            return jsonify(error=str(exc)), 503
        except RuntimeError as exc:
            return jsonify(error=str(exc)), 503
        except Exception:
            app.logger.exception("Falló el clasificador de Colab")
            return jsonify(error="No se pudo ejecutar el clasificador de Colab. Revisa el checkpoint y TensorFlow."), 500
        return jsonify(
            demo=False,
            modo="clasificacion",
            categoria="general",
            zona=MODEL_LABELS["general"],
            detecciones=[],
            resultados=resultados,
            cantidad=len(resultados),
            mensaje="El clasificador compara la foto completa con 28 categorías. Son puntajes del modelo, no probabilidades ni diagnósticos.",
            puntaje_es_probabilidad=False,
            umbral=None,
        )

    try:
        model = cargar_modelo(categoria)
        with INFERENCE_LOCK:
            prediccion = model.predict(
                source=imagen,
                imgsz=IMAGE_SIZE,
                conf=CONFIDENCE_THRESHOLD,
                iou=IOU_THRESHOLD,
                max_det=MAX_DETECTIONS,
                verbose=False,
            )[0]
    except FileNotFoundError as exc:
        return jsonify(error=str(exc)), 503
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 503
    except Exception:
        app.logger.exception("Falló la inferencia del modelo %s", categoria)
        return jsonify(error="No se pudo ejecutar el modelo. Revisa sus dependencias e inténtalo de nuevo."), 500

    detecciones = []
    agrupadas = {}
    cajas = prediccion.boxes
    if cajas is not None and len(cajas):
        coords = cajas.xyxy.cpu().tolist()
        ids_clase = cajas.cls.int().cpu().tolist()
        puntajes = cajas.conf.cpu().tolist()
        for coords_xyxy, class_id, score in zip(coords, ids_clase, puntajes):
            raw_name = prediccion.names[int(class_id)]
            info = info_clase(raw_name)
            score = float(score)
            detecciones.append({
                "clase": info["nombre"],
                "confianza": score,
                "caja": [round(float(value), 1) for value in coords_xyxy],
            })
            if info["nombre"] not in agrupadas or score > agrupadas[info["nombre"]]["confianza"]:
                agrupadas[info["nombre"]] = {
                    "clase": info["nombre"],
                    "confianza": score,
                    "descripcion": info["descripcion"],
                    "fuente": info["fuente"],
                }

    resultados = sorted(agrupadas.values(), key=lambda item: item["confianza"], reverse=True)
    mensaje = (
        f"Se detectaron {len(detecciones)} regiones visuales para revisar."
        if detecciones
        else "No se detectaron regiones de las clases que reconoce este modelo. Esto no significa que la mascota esté sana."
    )
    return jsonify(
        demo=False,
        categoria=categoria,
        zona=MODEL_LABELS[categoria],
        detecciones=detecciones,
        resultados=resultados,
        cantidad=len(detecciones),
        mensaje=mensaje,
        puntaje_es_probabilidad=False,
        umbral=CONFIDENCE_THRESHOLD,
    )


if __name__ == "__main__":
    host = os.environ.get("PATOO_HOST", "0.0.0.0")
    port = int(os.environ.get("PATOO_PORT", "5000"))
    app.run(host=host, port=port, debug=False)
