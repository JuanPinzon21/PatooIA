# PatooIA

Prototipo Flask responsivo para explorar fotos de mascotas con detectores independientes de piel, orejas, ojos y dientes, y un clasificador general experimental.

## Modelos incluidos

| Opción | Ruta en el repositorio | Clases |
|---|---|---:|
| Piel v3_auto | `model/piel/best.pt` | 6 |
| Orejas v4 | `model/orejas/best.pt` | 3 |
| Ojos v1 | `model/ojos/best.pt` | 4 |
| Dental v2 | `model/dental/best.pt` | 2 |
| Foto general experimental | `model/colab/huellitas_best.keras` | 28 |

Los detectores por zona marcan regiones en la imagen. La opción general evalúa la imagen completa y no localiza lesiones. Los puntajes son orientativos: no son probabilidades ni diagnósticos veterinarios.

## Instalar y ejecutar en Windows

Abre PowerShell en la carpeta raíz de este repositorio:

```powershell
cd "C:\Users\JuanH\OneDrive\Desktop\Patoo\PatooIA"
```

El entorno `venv` ya existe en la carpeta. Actualiza e instala dependencias con el Python de ese entorno:

```powershell
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe app.py
```

Abre `http://127.0.0.1:5000`. Si clonas el repositorio en otro equipo y no existe `venv`, créalo primero con `py -3.12 -m venv venv` y luego ejecuta los mismos comandos. La instalación de PyTorch, Ultralytics y TensorFlow puede tardar y ocupar varios GB.

## Mostrar la app en un teléfono

1. Conecta el portátil y el teléfono a la misma red Wi-Fi.
2. Deja Flask ejecutándose en el portátil.
3. Ejecuta `ipconfig` y busca la dirección IPv4 del adaptador Wi-Fi.
4. En el teléfono abre `http://IP_DEL_COMPUTADOR:5000`, por ejemplo `http://192.168.1.25:5000`.
5. Si Windows pregunta, permite Python en redes privadas. El servidor de desarrollo es para una demostración local, no para publicar en Internet.

## Estado de las evaluaciones

Hay reportes *test* guardados para ojos (291 imágenes: P 0.863, R 0.801, mAP50 0.915, mAP50–95 0.615) y dientes v2 (140 imágenes: P 0.448, R 0.443, mAP50 0.402, mAP50–95 0.206). Dental v1 y v2 comparten exactamente el mismo test; el resultado no es independiente.

Se ejecutó evaluación *test* con los pesos integrados y quedan los resultados en `reports/evaluaciones/`: piel v3_auto sobre 357 imágenes (P 0.567, R 0.491, mAP50 0.524, mAP50–95 0.316) y orejas v4 sobre 44 imágenes (P 0.723, R 0.620, mAP50 0.612, mAP50–95 0.267). Las métricas completas y gráficos están guardados en esas carpetas. Orejas v4 reutiliza el test de la línea anterior; no es una evaluación independiente nueva. Dental v1/v2 también comparten el mismo test. Estas métricas no demuestran desempeño clínico.

Las particiones de entrenamiento no son necesarias para ejecutar la página. Las salidas del modelo no diagnostican y requieren validación de datos y revisión veterinaria.

## Muestras de demostración

`demo_samples/` contiene ejemplos locales de piel y orejas. Las muestras se excluyen de Git mediante `.gitignore` porque se debe verificar la licencia de las imágenes antes de redistribuirlas. La app funciona también si esa carpeta no está presente.

## Publicar en Render o Railway

El repositorio ya incluye `Procfile` para el servidor de producción Gunicorn. En ambos servicios conecta el repositorio GitHub `PatooIA`, usa la raíz del repo, instala con `pip install -r requirements.txt` y configura como start command:

```text
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 180
```

`workers=1` evita cargar varias copias de los modelos en memoria. La app se mantiene en CPU; no usa GPU alojada.

**Recomendación para este prototipo: Railway Hobby con 1–2 GB de RAM asignada.** Al cargar los cinco modelos, medí aproximadamente 525 MB de memoria en el entorno local, sin contar diferencias de Linux, el servidor y picos al analizar. Railway Trial baja de hasta 1 GB a 0.5 GB al terminar; Hobby tiene mínimo de $5/mes que incluye $5 de uso y cobra el consumo que lo exceda. Revisa Usage y fija un límite de gasto antes de dejarlo publicado.

Render también lo puede ejecutar: su plan gratis tiene 512 MB y se duerme tras 15 minutos sin tráfico, por lo que no lo recomiendo para esta app con los cinco modelos. El plan Render de 2 GB figura actualmente a $25/mes; ofrece un costo más fijo. Consulta precios antes de elegir porque pueden cambiar.

Pasos Render: `New` → `Web Service` → conecta `PatooIA` → build `pip install -r requirements.txt` → start command de arriba → plan con 2 GB RAM.

Pasos Railway: `New Project` → `Deploy from GitHub repo` → elige `PatooIA` → verifica el start command de arriba → asigna al menos 1 GB (2 GB recomendado) → genera un dominio público.

