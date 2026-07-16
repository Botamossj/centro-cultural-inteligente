/* ==========================================================================
   Centro Cultural Inteligente - Lógica del frontend
   Vanilla JavaScript + Fetch API.
   IMPORTANTE: solo se usan rutas RELATIVAS (/api/...). Nunca IPs fijas,
   porque el navegador y el backend comparten origen a través de Nginx.
   ========================================================================== */

"use strict";

// URL base relativa. Nginx enruta /api/ hacia el backend Flask.
const API_BASE = "/api/visitantes";

// Estado de búsqueda con debounce.
let searchTimer = null;

// --- Referencias al DOM ---
const form = document.getElementById("visitante-form");
const idField = document.getElementById("visitante-id");
const nombreField = document.getElementById("nombre");
const correoField = document.getElementById("correo");
const categoriaField = document.getElementById("categoria");
const submitBtn = document.getElementById("submit-btn");
const clearBtn = document.getElementById("clear-btn");
const refreshBtn = document.getElementById("refresh-btn");
const searchField = document.getElementById("search");
const messageEl = document.getElementById("message");
const loadingEl = document.getElementById("loading");
const emptyStateEl = document.getElementById("empty-state");
const tableBody = document.getElementById("visitantes-body");
const paginationInfo = document.getElementById("pagination-info");

// ---------------------------------------------------------------------------
// Utilidades de UI
// ---------------------------------------------------------------------------
function showMessage(text, type) {
  messageEl.textContent = text; // textContent evita XSS
  messageEl.className = "message " + type;
  messageEl.hidden = false;
  if (type === "success") {
    setTimeout(() => {
      messageEl.hidden = true;
    }, 4000);
  }
}

function hideMessage() {
  messageEl.hidden = true;
}

function setLoading(active) {
  loadingEl.hidden = !active;
}

function formatFecha(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString("es-ES", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ---------------------------------------------------------------------------
// Renderizado seguro de la tabla (sin innerHTML con datos del usuario)
// ---------------------------------------------------------------------------
function crearCelda(texto) {
  const td = document.createElement("td");
  td.textContent = texto == null ? "" : String(texto);
  return td;
}

function crearFila(v) {
  const tr = document.createElement("tr");

  tr.appendChild(crearCelda(v.id));
  tr.appendChild(crearCelda(v.nombre));
  tr.appendChild(crearCelda(v.correo));

  // Categoría con badge
  const catTd = document.createElement("td");
  const badge = document.createElement("span");
  badge.className = "badge";
  badge.textContent = v.categoria;
  catTd.appendChild(badge);
  tr.appendChild(catTd);

  tr.appendChild(crearCelda(formatFecha(v.fecha_registro)));

  // Acciones
  const accionesTd = document.createElement("td");
  accionesTd.className = "actions-cell";

  const editBtn = document.createElement("button");
  editBtn.type = "button";
  editBtn.className = "btn btn-small btn-edit";
  editBtn.textContent = "Editar";
  editBtn.addEventListener("click", () => cargarEnFormulario(v));

  const deleteBtn = document.createElement("button");
  deleteBtn.type = "button";
  deleteBtn.className = "btn btn-small btn-danger";
  deleteBtn.textContent = "Eliminar";
  deleteBtn.addEventListener("click", () => eliminarVisitante(v));

  accionesTd.appendChild(editBtn);
  accionesTd.appendChild(deleteBtn);
  tr.appendChild(accionesTd);

  return tr;
}

function renderTabla(visitantes, pagination) {
  tableBody.replaceChildren();

  if (!visitantes || visitantes.length === 0) {
    emptyStateEl.hidden = false;
    paginationInfo.textContent = "";
    return;
  }

  emptyStateEl.hidden = true;
  const fragment = document.createDocumentFragment();
  visitantes.forEach((v) => fragment.appendChild(crearFila(v)));
  tableBody.appendChild(fragment);

  if (pagination) {
    paginationInfo.textContent =
      "Mostrando " +
      visitantes.length +
      " de " +
      pagination.total +
      " visitante(s).";
  }
}

// ---------------------------------------------------------------------------
// Llamadas a la API
// ---------------------------------------------------------------------------
async function cargarVisitantes() {
  setLoading(true);
  hideMessage();
  try {
    const search = searchField.value.trim();
    const query = search ? "?search=" + encodeURIComponent(search) : "";
    const resp = await fetch(API_BASE + query);
    if (!resp.ok) {
      throw new Error("No se pudo cargar la lista (HTTP " + resp.status + ").");
    }
    const body = await resp.json();
    renderTabla(body.data, body.pagination);
  } catch (err) {
    renderTabla([], null);
    showMessage(err.message || "Error al cargar los visitantes.", "error");
  } finally {
    setLoading(false);
  }
}

async function guardarVisitante(evento) {
  evento.preventDefault();
  hideMessage();

  const payload = {
    nombre: nombreField.value.trim(),
    correo: correoField.value.trim(),
    categoria: categoriaField.value,
  };

  if (!payload.nombre || !payload.correo || !payload.categoria) {
    showMessage("Completa todos los campos obligatorios.", "error");
    return;
  }

  const id = idField.value;
  const editando = Boolean(id);
  const url = editando ? API_BASE + "/" + encodeURIComponent(id) : API_BASE;
  const method = editando ? "PUT" : "POST";

  submitBtn.disabled = true;
  try {
    const resp = await fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (resp.status === 201 || resp.status === 200) {
      showMessage(
        editando ? "Visitante actualizado correctamente." : "Visitante registrado correctamente.",
        "success"
      );
      resetFormulario();
      await cargarVisitantes();
      return;
    }

    // Manejo de errores controlados de la API
    let mensaje = "Error al guardar el visitante.";
    try {
      const data = await resp.json();
      if (data && data.error) mensaje = data.error;
    } catch (_) {
      /* respuesta sin cuerpo JSON */
    }
    showMessage(mensaje, "error");
  } catch (err) {
    showMessage("Error de red al guardar el visitante.", "error");
  } finally {
    submitBtn.disabled = false;
  }
}

async function eliminarVisitante(v) {
  const confirmar = window.confirm(
    "¿Eliminar al visitante \"" + v.nombre + "\"? Esta acción no se puede deshacer."
  );
  if (!confirmar) return;

  hideMessage();
  try {
    const resp = await fetch(API_BASE + "/" + encodeURIComponent(v.id), {
      method: "DELETE",
    });
    if (resp.status === 204) {
      showMessage("Visitante eliminado.", "success");
      await cargarVisitantes();
      return;
    }
    let mensaje = "No se pudo eliminar el visitante.";
    try {
      const data = await resp.json();
      if (data && data.error) mensaje = data.error;
    } catch (_) {
      /* sin cuerpo */
    }
    showMessage(mensaje, "error");
  } catch (err) {
    showMessage("Error de red al eliminar el visitante.", "error");
  }
}

// ---------------------------------------------------------------------------
// Manejo del formulario
// ---------------------------------------------------------------------------
function cargarEnFormulario(v) {
  idField.value = v.id;
  nombreField.value = v.nombre;
  correoField.value = v.correo;
  categoriaField.value = v.categoria;
  submitBtn.textContent = "Guardar cambios";
  nombreField.focus();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function resetFormulario() {
  form.reset();
  idField.value = "";
  submitBtn.textContent = "Registrar";
}

// ---------------------------------------------------------------------------
// Eventos
// ---------------------------------------------------------------------------
form.addEventListener("submit", guardarVisitante);
clearBtn.addEventListener("click", resetFormulario);
refreshBtn.addEventListener("click", cargarVisitantes);
searchField.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(cargarVisitantes, 350);
});

// Carga inicial
document.addEventListener("DOMContentLoaded", cargarVisitantes);
