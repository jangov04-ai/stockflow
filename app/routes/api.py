from flask import Blueprint, jsonify, request

from .. import services
from ..models import Categoria, Movimiento, Producto, db

api_bp = Blueprint("api", __name__)


def _error(mensaje, codigo=400):
    return jsonify({"error": mensaje}), codigo


@api_bp.errorhandler(services.InventarioError)
def _error_inventario(error):
    db.session.rollback()
    return _error(str(error))


@api_bp.errorhandler(404)
def _no_encontrado(_excepcion):
    return _error("Recurso no encontrado", 404)


@api_bp.get("/productos")
def listar_productos():
    productos = services.buscar_productos(request.args.get("q", ""))
    if request.args.get("stock_bajo") == "1":
        productos = [p for p in productos if p.stock_bajo]
    return jsonify([p.to_dict() for p in productos])


@api_bp.post("/productos")
def crear_producto():
    datos = request.get_json(silent=True) or {}
    producto = services.crear_producto(
        sku=datos.get("sku"),
        nombre=datos.get("nombre"),
        precio=datos.get("precio", 0),
        stock_minimo=datos.get("stock_minimo", 5),
        categoria=datos.get("categoria"),
    )
    return jsonify(producto.to_dict()), 201


@api_bp.get("/productos/<int:producto_id>")
def obtener_producto(producto_id):
    return jsonify(db.get_or_404(Producto, producto_id).to_dict())


@api_bp.put("/productos/<int:producto_id>")
def actualizar_producto(producto_id):
    producto = db.get_or_404(Producto, producto_id)
    datos = request.get_json(silent=True) or {}
    services.actualizar_producto(
        producto,
        nombre=datos.get("nombre"),
        precio=datos.get("precio"),
        stock_minimo=datos.get("stock_minimo"),
        categoria=datos.get("categoria"),
    )
    return jsonify(producto.to_dict())


@api_bp.delete("/productos/<int:producto_id>")
def eliminar_producto(producto_id):
    services.eliminar_producto(db.get_or_404(Producto, producto_id))
    return "", 204


@api_bp.post("/productos/<int:producto_id>/movimientos")
def registrar_movimiento(producto_id):
    producto = db.get_or_404(Producto, producto_id)
    datos = request.get_json(silent=True) or {}
    movimiento = services.registrar_movimiento(
        producto, datos.get("tipo"), datos.get("cantidad"), datos.get("motivo", "")
    )
    return jsonify({"movimiento": movimiento.to_dict(), "producto": producto.to_dict()}), 201


@api_bp.get("/movimientos")
def listar_movimientos():
    limite = min(request.args.get("limite", 50, type=int), 200)
    movimientos = Movimiento.query.order_by(Movimiento.fecha.desc()).limit(limite).all()
    return jsonify([m.to_dict() for m in movimientos])


@api_bp.get("/categorias")
def listar_categorias():
    return jsonify([c.to_dict() for c in Categoria.query.order_by(Categoria.nombre).all()])


@api_bp.get("/resumen")
def resumen():
    return jsonify(services.resumen_inventario())
