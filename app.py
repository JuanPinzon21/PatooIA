import io
import json
import os

import numpy as np
from PIL import Image
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB máx.

RUTA_MODELO = "model/patoo_model.keras"
RUTA_CLASES = "model/class_names.json"
UMBRAL = 0.5  # por debajo de esto la app dice "no estoy seguro"

model = None
class_names = []
if os.path.exists(RUTA_MODELO) and os.path.exists(RUTA_CLASES):
    from tensorflow import keras
    model = keras.models.load_model(RUTA_MODELO)
    with open(RUTA_CLASES, encoding="utf-8") as f:
        class_names = json.load(f)


def preparar(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((224, 224))
    arr = np.array(img, dtype="float32")
    # IMPORTANTE: debe ser el mismo preprocesamiento del entrenamiento.
    # Si el modelo ya incluye Rescaling(1/255), no dividas aquí.
    return np.expand_dims(arr, 0)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    archivo = request.files.get("imagen")
    if not archivo or archivo.filename == "":
        return jsonify(error="No se envió ninguna imagen."), 400

    if model is None:  # modo demo
        demo = [("Dermatitis", 0.78), ("Hypersensitivity", 0.12), ("Skin Allergy in Dog", 0.06)]
        return jsonify(
            demo=True,
            confiable=True,
            resultados=[{"clase": c, "confianza": p} for c, p in demo],
        )

    try:
        probs = model.predict(preparar(archivo.read()), verbose=0)[0]
    except Exception:
        return jsonify(error="No pude leer la imagen. Prueba con otra (JPG o PNG)."), 400

    top3 = np.argsort(probs)[::-1][:3]
    resultados = [{"clase": class_names[i], "confianza": float(probs[i])} for i in top3]
    return jsonify(demo=False, confiable=resultados[0]["confianza"] >= UMBRAL, resultados=resultados)


if __name__ == "__main__":
    app.run(debug=True)