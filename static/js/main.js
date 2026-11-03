const zona = document.getElementById("zona");
const inputArchivo = document.getElementById("archivo");
const btnElegir = document.getElementById("btn-elegir");
const btnAnalizar = document.getElementById("btn-analizar");
const preview = document.getElementById("preview");
const zonaTexto = document.getElementById("zona-texto");
const errorEl = document.getElementById("error");
const resultado = document.getElementById("resultado");

let archivoActual = null;

function mostrarError(msg) {
  errorEl.textContent = msg;
  errorEl.hidden = !msg;
}

function cargarArchivo(file) {
  if (!file || !file.type.startsWith("image/")) {
    mostrarError("Selecciona una imagen (JPG o PNG).");
    return;
  }
  mostrarError("");
  archivoActual = file;
  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
  zonaTexto.hidden = true;
  btnAnalizar.disabled = false;
  resultado.hidden = true;
}

btnElegir.addEventListener("click", () => inputArchivo.click());
inputArchivo.addEventListener("change", () => cargarArchivo(inputArchivo.files[0]));

zona.addEventListener("dragover", (e) => { e.preventDefault(); zona.classList.add("arriba"); });
zona.addEventListener("dragleave", () => zona.classList.remove("arriba"));
zona.addEventListener("drop", (e) => {
  e.preventDefault();
  zona.classList.remove("arriba");
  cargarArchivo(e.dataTransfer.files[0]);
});

btnAnalizar.addEventListener("click", async () => {
  if (!archivoActual) return;
  btnAnalizar.disabled = true;
  btnAnalizar.textContent = "Analizando...";
  mostrarError("");

  const datos = new FormData();
  datos.append("imagen", archivoActual);

  try {
    const resp = await fetch("/predict", { method: "POST", body: datos });
    const json = await resp.json();
    if (!resp.ok) throw new Error(json.error || "Error al analizar la imagen.");
    mostrarResultado(json);
  } catch (err) {
    mostrarError(err.message);
  } finally {
    btnAnalizar.disabled = false;
    btnAnalizar.textContent = "Analizar";
  }
});

function mostrarResultado(json) {
  document.getElementById("aviso-baja").hidden = json.confiable;
  document.getElementById("demo").hidden = !json.demo;
  document.getElementById("titulo-res").textContent = json.confiable
    ? json.resultados[0].clase
    : "Posibilidades";

  const barras = document.getElementById("barras");
  barras.replaceChildren();

  json.resultados.forEach((r, i) => {
    const pct = Math.round(r.confianza * 100);
    const fila = document.createElement("div");
    fila.className = "fila" + (i === 0 && json.confiable ? " principal" : "");

    const top = document.createElement("div");
    top.className = "fila-top";
    const nombre = document.createElement("span");
    nombre.textContent = r.clase;
    const valor = document.createElement("span");
    valor.textContent = pct + "%";
    top.append(nombre, valor);

    const pista = document.createElement("div");
    pista.className = "pista";
    const relleno = document.createElement("div");
    relleno.className = "relleno";
    relleno.style.width = pct + "%";
    pista.append(relleno);

    fila.append(top, pista);
    barras.append(fila);
  });

  resultado.hidden = false;
  resultado.scrollIntoView({ behavior: "smooth" });
}