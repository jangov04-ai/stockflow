/* Interacciones de la interfaz de StockFlow (sin dependencias). */
"use strict";

/**
 * Pide confirmación antes de enviar formularios con data-confirmar.
 * @param {Document} doc
 */
function activarConfirmaciones(doc) {
  doc.querySelectorAll("form[data-confirmar]").forEach((form) => {
    form.addEventListener("submit", (evento) => {
      const mensaje = form.getAttribute("data-confirmar");
      if (!window.confirm(mensaje)) {
        evento.preventDefault();
      }
    });
  });
}

/**
 * Avisa si una salida supera el stock disponible del producto elegido.
 * @param {Document} doc
 */
function activarAvisoStock(doc) {
  const producto = doc.getElementById("producto_id");
  const tipo = doc.getElementById("tipo");
  const cantidad = doc.getElementById("cantidad");
  const aviso = doc.getElementById("aviso-stock");
  if (!producto || !tipo || !cantidad || !aviso) {
    return;
  }

  const revisar = () => {
    const opcion = producto.options[producto.selectedIndex];
    const disponible = Number(opcion ? opcion.dataset.stock : 0);
    const pedida = Number(cantidad.value);
    const excede = tipo.value === "salida" && pedida > disponible;
    aviso.hidden = !excede;
    aviso.textContent = excede
      ? `Solo hay ${disponible} unidades disponibles de este producto.`
      : "";
  };

  [producto, tipo, cantidad].forEach((campo) => campo.addEventListener("input", revisar));
  revisar();
}

/**
 * Oculta automáticamente los avisos de éxito tras unos segundos.
 * @param {Document} doc
 */
function ocultarAvisos(doc) {
  doc.querySelectorAll(".aviso-ok").forEach((aviso) => {
    window.setTimeout(() => {
      aviso.style.display = "none";
    }, 5000);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  activarConfirmaciones(document);
  activarAvisoStock(document);
  ocultarAvisos(document);
});
