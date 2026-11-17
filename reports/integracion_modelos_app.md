# Estado de integración de PatooIA

La aplicación quedó en la raíz del repositorio: Flask en `app.py`, vista en `templates/index.html`, estilos en `static/css/style.css` e interacción en `static/js/main.js`. Se mantuvo el layout del repositorio, el entorno `venv` y las muestras que ya existían.

## Modelos conectados

- `model/piel/best.pt`: piel v3_auto (6 clases).
- `model/orejas/best.pt`: orejas v4 (3 clases).
- `model/ojos/best.pt`: ojos v1 (4 clases).
- `model/dental/best.pt`: dental v2 (2 clases).
- `model/colab/huellitas_best.keras`: clasificador general experimental (28 etiquetas).

La página principal y `/predict` respondieron HTTP 200 para las cinco opciones mediante el entorno virtual de PatooIA. Es una comprobación de integración e inferencia básica, no de precisión clínica.

## Métricas de test ejecutadas en esta integración

| Modelo | Imágenes | P | R | mAP50 | mAP50–95 |
|---|---:|---:|---:|---:|---:|
| Piel v3_auto | 357 | 0.567 | 0.491 | 0.524 | 0.316 |
| Orejas v4 | 44 | 0.723 | 0.620 | 0.612 | 0.267 |
| Ojos v1 | 291 | 0.863 | 0.801 | 0.915 | 0.615 |
| Dental v2 | 140 | 0.448 | 0.443 | 0.402 | 0.206 |

Las métricas nuevas de piel y orejas se guardaron en `reports/evaluaciones/*_test/metricas_test.json` y sus matrices/curvas en las mismas carpetas. Las imágenes `val_batch*.jpg` se excluyen de Git para no redistribuir fotos de test.

## Límites

- Dental v1 y v2 comparten exactamente el mismo test, así que el resultado dental no es un test independiente nuevo.
- Orejas v4 reutiliza el test de la línea anterior; la cifra no es independiente de v3.
- Piel tiene 1,629/361/357 imágenes train/valid/test. No hubo hashes de imagen idénticos entre sus splits, pero eso no descarta fotos parecidas del mismo animal.
- Las etiquetas son provisionales y no están validadas clínicamente. La app orienta sobre clases/regiones a investigar; no diagnostica.
- Los datasets completos no se requieren para ejecutar la página. Las muestras locales de `demo_samples/` siguen ignoradas por Git por revisión de licencias.

## Preparación para hosting

Se añadió un `Procfile` de Gunicorn con un worker y dos threads, y se añadió Gunicorn a `requirements.txt` solo para sistemas distintos de Windows. La app escucha el `$PORT` asignado por el proveedor. En una medición local de carga de los cinco modelos, el proceso usó aproximadamente 525 MB RSS; el consumo real del servidor puede variar y subir durante inferencias. Por eso 512 MB no es un tamaño fiable para mantener activos los cinco modelos.
