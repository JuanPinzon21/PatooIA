const zona = document.getElementById("zona");
const inputArchivo = document.getElementById("archivo");
const inputCamara = document.getElementById("camara");
const btnElegir = document.getElementById("btn-elegir");
const btnCamara = document.getElementById("btn-camara");
const btnAnalizar = document.getElementById("btn-analizar");
const btnOtra = document.getElementById("btn-otra");
const preview = document.getElementById("preview");
const zonaTexto = document.getElementById("zona-texto");
const cargando = document.getElementById("cargando");
const errorEl = document.getElementById("error");
const resultado = document.getElementById("resultado");

const TIPOS = ["image/jpeg", "image/png", "image/webp"];
const MAX_ORIGINAL = 25 * 1024 * 1024; // se comprime antes de enviar
const MAX_ENVIO = 8 * 1024 * 1024;
const LADO_MAX = 1600;

let archivoActual = null;
let urlPreview = null;

function mostrarError(msg) {
  errorEl.textContent = msg;
  errorEl.hidden = !msg;
}

function cargarArchivo(file) {
  if (!file) return;
  if (!file.type.startsWith("image/") || (file.type && !TIPOS.includes(file.type))) {
    mostrarError("Ese formato no sirve. Elige una imagen JPG, PNG o WebP.");
    return;
  }
  if (file.size > MAX_ORIGINAL) {
    mostrarError("La foto es demasiado grande. Prueba con una de menos de 25 MB.");
    return;
  }
  mostrarError("");
  archivoActual = file;
  if (urlPreview) URL.revokeObjectURL(urlPreview);
  urlPreview = URL.createObjectURL(file);
  preview.src = urlPreview;
  preview.hidden = false;
  zonaTexto.hidden = true;
  zona.classList.add("con-foto");
  btnAnalizar.disabled = false;
  btnElegir.textContent = "Cambiar foto";
  resultado.hidden = true;
}

// Reduce el tamaño de la foto para que suba rápido desde el celular
async function prepararImagen(file) {
  try {
    const bmp = await createImageBitmap(file, { imageOrientation: "from-image" });
    const escala = Math.min(1, LADO_MAX / Math.max(bmp.width, bmp.height));
    if (escala === 1 && file.size <= MAX_ENVIO) { bmp.close?.(); return file; }
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bmp.width * escala);
    canvas.height = Math.round(bmp.height * escala);
    canvas.getContext("2d").drawImage(bmp, 0, 0, canvas.width, canvas.height);
    bmp.close?.();
    const blob = await new Promise((ok) => canvas.toBlob(ok, "image/jpeg", 0.88));
    if (blob && blob.size < file.size) return new File([blob], "foto.jpg", { type: "image/jpeg" });
  } catch (_) { /* si falla, se envía el original */ }
  return file;
}

function reiniciar() {
  archivoActual = null;
  inputArchivo.value = "";
  inputCamara.value = "";
  if (urlPreview) { URL.revokeObjectURL(urlPreview); urlPreview = null; }
  preview.removeAttribute("src");
  preview.hidden = true;
  zonaTexto.hidden = false;
  zona.classList.remove("con-foto");
  btnAnalizar.disabled = true;
  btnElegir.textContent = "Elegir foto";
  resultado.hidden = true;
  mostrarError("");
  zona.scrollIntoView({ behavior: "smooth", block: "center" });
}

btnElegir.addEventListener("click", () => inputArchivo.click());
btnCamara.addEventListener("click", () => inputCamara.click());
zona.addEventListener("click", () => inputArchivo.click());
zona.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") { e.preventDefault(); inputArchivo.click(); }
});
inputArchivo.addEventListener("change", () => cargarArchivo(inputArchivo.files[0]));
inputCamara.addEventListener("change", () => cargarArchivo(inputCamara.files[0]));
btnOtra.addEventListener("click", reiniciar);

zona.addEventListener("dragover", (e) => { e.preventDefault(); zona.classList.add("arriba"); });
zona.addEventListener("dragleave", () => zona.classList.remove("arriba"));
zona.addEventListener("drop", (e) => {
  e.preventDefault();
  zona.classList.remove("arriba");
  cargarArchivo(e.dataTransfer.files[0]);
});

function enCarga(activo) {
  cargando.hidden = !activo;
  cargando.setAttribute("aria-hidden", String(!activo));
  btnAnalizar.disabled = activo;
  btnElegir.disabled = activo;
  btnCamara.disabled = activo;
  btnAnalizar.textContent = activo ? "Analizando…" : "Analizar foto";
}

btnAnalizar.addEventListener("click", async () => {
  if (!archivoActual) return;
  enCarga(true);
  mostrarError("");

  try {
    const envio = await prepararImagen(archivoActual);
    if (envio.size > MAX_ENVIO) throw new Error("La foto pesa demasiado. Prueba con otra más liviana.");

    const datos = new FormData();
    datos.append("imagen", envio);

    const resp = await fetch("/predict", { method: "POST", body: datos });
    let json = {};
    try { json = await resp.json(); } catch (_) {}
    if (!resp.ok) throw new Error(json.error || "No pudimos analizar la foto. Inténtalo de nuevo.");
    mostrarResultado(json);
  } catch (err) {
    mostrarError(err instanceof TypeError
      ? "No hay conexión. Revisa tu internet e inténtalo de nuevo."
      : err.message);
  } finally {
    enCarga(false);
    btnAnalizar.disabled = !archivoActual;
  }
});

function mostrarResultado(json) {
  document.getElementById("aviso-baja").hidden = !!json.confiable;
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
    pista.setAttribute("role", "progressbar");
    pista.setAttribute("aria-valuenow", pct);
    pista.setAttribute("aria-valuemin", 0);
    pista.setAttribute("aria-valuemax", 100);
    pista.setAttribute("aria-label", r.clase);
    const relleno = document.createElement("div");
    relleno.className = "relleno";
    pista.append(relleno);

    fila.append(top, pista);
    barras.append(fila);
    requestAnimationFrame(() => requestAnimationFrame(() => { relleno.style.width = pct + "%"; }));
  });

  resultado.hidden = false;
  resultado.scrollIntoView({ behavior: "smooth", block: "start" });
  resultado.focus({ preventScroll: true });
}