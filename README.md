# PatooIA

Prototipo Flask para explorar imágenes de piel y orejas de perros y gatos con dos detectores YOLO11 independientes.

## Modelos incluidos

- `model/piel/best.pt`: Patoo piel YOLO11n v3_auto, entrenado para 6 clases.
- `model/orejas/best.pt`: Patoo orejas YOLO11n v2, entrenado para 3 clases.

La interfaz permite elegir la zona que se va a analizar. El módulo dental aparece como próximo porque el material compartido no contiene un dataset dental anotado ni un modelo entrenado para esa zona. El reporte de orejas V3 tiene 49 imágenes aprobadas, 41 excluidas y 56 marcadas para revisión; conviene cerrar esa revisión antes de sumar esos datos a un nuevo entrenamiento.

Los CSV de entrenamiento muestran estos resultados de validación (no son una evaluación clínica ni una prueba independiente):

| Modelo | Precisión | Recall | mAP50 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: |
| Piel v3_auto | 0.603 | 0.545 | 0.571 | 0.365 |
| Orejas v2 | 0.678 | 0.602 | 0.637 | 0.265 |

## Ejecutar en Windows

Desde esta carpeta, abre PowerShell y ejecuta:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe app.py
```

Después abre `http://127.0.0.1:5000` en el navegador. La primera instalación puede tardar porque PyTorch y Ultralytics ocupan espacio.

## Añadir el módulo dental

1. Conseguir imágenes de bocas y dientes de perros y gatos con permiso de uso y licencia documentada.
2. Definir etiquetas concretas con revisión veterinaria (por ejemplo, placa/cálculo, gingivitis y dientes fracturados). Incluir diversidad de animales, edades, iluminación y dispositivos.
3. Anotar cajas de cada hallazgo en formato YOLO; separar train/valid/test por animal o fuente para evitar que fotos casi iguales caigan en particiones distintas.
4. Entrenar un detector dental independiente y medirlo en un test que no se haya usado para entrenar ni ajustar umbrales.
5. Añadir su checkpoint y activar la opción `dientes` solo después de revisar errores por clase y con asesoría veterinaria.

No se deben mezclar fotos de piel, orejas y dientes como si fueran una sola tarea: cada zona necesita datos, clases y evaluación propios. Revisa y conserva las licencias de cada fuente antes de redistribuir datasets o checkpoints.

## Alcance

Los puntajes son salidas del detector, no probabilidades clínicas. “Sin regiones detectadas” no significa que la mascota esté sana. El prototipo no reemplaza una evaluación veterinaria.




## Ensayo rápido para la presentación

1. Instala dependencias y levanta Flask con los comandos de arriba.
2. Abre `http://127.0.0.1:5000`.
3. Selecciona **Piel** y prueba esta imagen del split `test`:
   `..\..\dataset\piel\piel_final_v3_auto\test\images\dog_skin_diseases_80a51789_00339.jpg` (etiqueta de referencia: `tina`).
4. Selecciona **Orejas** y prueba esta imagen del split `test`:
   `..\..\dataset\orejas\orejas_final_v2_limpio\test\images\feline_dermaaid_0f2162ae48_13_jpg.rf.9b3c27c07bd8b4de5cff064441c96d09.jpg` (etiqueta de referencia: `acaros_oido`).
5. Guarda una captura de cada resultado para la presentación. Si una imagen no coincide con la etiqueta, muéstralo como limitación del prototipo y no cambies el umbral solo para forzar el resultado.

Estas dos imágenes están en `test`: úsalas para la demostración, no las agregues al entrenamiento. Al presentar, di “región/clase sugerida por el detector”, no “diagnóstico” ni “probabilidad”.

## Posible fuente para explorar después de la presentación

El conjunto [Cat Dental Object Detection Dataset](https://universe.roboflow.com/final-year-project-6yujd/cat-dental-anz2r) reporta 315 imágenes, clases `gingivitis` y `plaque`, y licencia CC BY 4.0. Su página no explica la procedencia ni la revisión veterinaria de las etiquetas, así que no se incluye en el entrenamiento actual. Descárgalo solo para inspección y confirma anotaciones, licencia y calidad antes de combinarlo. Es solo para gatos; aún harían falta datos dentales caninos revisados.

## Mostrar la app en un teléfono

La app se sirve en la red local para una presentación; no es necesario instalarla desde una tienda.

1. Conecta el portátil y el teléfono a la misma red Wi-Fi.
2. Inicia Flask desde la carpeta PatooIA con `.\venv\Scripts\python.exe app.py`.
3. En el portátil ejecuta `ipconfig` y busca la dirección IPv4 del adaptador Wi-Fi, por ejemplo `192.168.1.25`.
4. En el teléfono abre `http://192.168.1.25:5000` sustituyendo la dirección por la del portátil. Si Windows pregunta, permite Python en redes privadas.
5. En la página puedes tocar las muestras de piel/orejas o usar **Tomar foto** desde el teléfono.

Usa una red privada y deja Flask abierto solo durante la demostración. El servidor de desarrollo no es para publicar la app en Internet.

## Carpeta local de muestras

`demo_samples/` tiene 18 copias del split `test`: dos por cada una de las 6 clases de piel y dos por cada una de las 3 clases de orejas. La página muestra una muestra destacada de cada zona para que también se pueda probar desde el teléfono. El resto está separado por carpeta y clase; `demo_samples/LEEME_PRUEBAS.txt` registra el archivo original y su etiqueta.

La carpeta está ignorada por Git para no redistribuir imágenes sin verificar las licencias. Las etiquetas son referencias del dataset; una predicción distinta no convierte el resultado en diagnóstico ni demuestra que el modelo esté correcto.

