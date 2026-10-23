"""Reglas de negocio del inventario (independientes de la capa web)."""

import re

from .models import Categoria, Movimiento, Producto, db

SKU_PATRON = re.compile(r"^[A-Z0-9]{3,10}-[0-9]{3,6}$")


class InventarioError(ValueError):
    """Error de validación en una operación de inventario."""


def validar_sku(sku):
    sku = (sku or "").strip().upper()
    if not SKU_PATRON.match(sku):
        raise InventarioError(
            "SKU inválido: usa el formato ABC-001 (letras o números, guion y dígitos)"
        )
    return sku


def obtener_o_crear_categoria(nombre):
    nombre = (nombre or "").strip().title()
    if not nombre:
        return None
    categoria = Categoria.query.filter_by(nombre=nombre).first()
    if categoria is None:
        categoria = Categoria(nombre=nombre)
        db.session.add(categoria)
    return categoria


def crear_producto(sku, nombre, precio, stock_minimo=5, categoria=None):
    sku = validar_sku(sku)
    nombre = _validar_nombre(nombre)
    precio = _no_negativo(_a_numero(precio, float, "precio"), "precio")
    stock_minimo = _no_negativo(_a_numero(stock_minimo, int, "stock mínimo"), "stock mínimo")
    if Producto.query.filter_by(sku=sku).first():
        raise InventarioError(f"Ya existe un producto con SKU {sku}")

    producto = Producto(
        sku=sku,
        nombre=nombre,
        precio=round(precio, 2),
        stock=0,
        stock_minimo=stock_minimo,
        categoria=obtener_o_crear_categoria(categoria),
    )
    db.session.add(producto)
    db.session.commit()
    return producto


def actualizar_producto(producto, nombre=None, precio=None, stock_minimo=None, categoria=None):
    if nombre is not None:
        producto.nombre = _validar_nombre(nombre)
    if precio is not None:
        producto.precio = round(_no_negativo(_a_numero(precio, float, "precio"), "precio"), 2)
    if stock_minimo is not None:
        producto.stock_minimo = _no_negativo(
            _a_numero(stock_minimo, int, "stock mínimo"), "stock mínimo"
        )
    if categoria is not None:
        producto.categoria = obtener_o_crear_categoria(categoria)
    db.session.commit()
    return producto


def registrar_movimiento(producto, tipo, cantidad, motivo=""):
    if tipo not in (Movimiento.ENTRADA, Movimiento.SALIDA):
        raise InventarioError("El tipo debe ser entrada o salida")
    cantidad = _a_numero(cantidad, int, "cantidad")
    if cantidad <= 0:
        raise InventarioError("La cantidad debe ser mayor que cero")
    if tipo == Movimiento.SALIDA and cantidad > producto.stock:
        raise InventarioError(
            f"Stock insuficiente: hay {producto.stock} y se intentan retirar {cantidad}"
        )

    producto.stock += cantidad if tipo == Movimiento.ENTRADA else -cantidad
    movimiento = Movimiento(
        producto=producto, tipo=tipo, cantidad=cantidad, motivo=(motivo or "").strip()
    )
    db.session.add(movimiento)
    db.session.commit()
    return movimiento


def eliminar_producto(producto):
    db.session.delete(producto)
    db.session.commit()


def productos_con_stock_bajo():
    return [p for p in Producto.query.order_by(Producto.stock).all() if p.stock_bajo]


def resumen_inventario():
    productos = Producto.query.all()
    return {
        "total_productos": len(productos),
        "unidades_totales": sum(p.stock for p in productos),
        "valor_inventario": round(sum(p.valor_total for p in productos), 2),
        "productos_stock_bajo": sum(1 for p in productos if p.stock_bajo),
        "total_categorias": Categoria.query.count(),
    }


def buscar_productos(texto=""):
    consulta = Producto.query
    texto = (texto or "").strip()
    if texto:
        patron = f"%{texto}%"
        consulta = consulta.filter(
            db.or_(Producto.nombre.ilike(patron), Producto.sku.ilike(patron))
        )
    return consulta.order_by(Producto.nombre).all()


def _validar_nombre(nombre):
    nombre = (nombre or "").strip()
    if len(nombre) < 2:
        raise InventarioError("El nombre debe tener al menos 2 caracteres")
    return nombre


def _no_negativo(valor, campo):
    if valor < 0:
        raise InventarioError(f"El campo {campo} no puede ser negativo")
    return valor


def _a_numero(valor, tipo, campo):
    try:
        return tipo(valor)
    except (TypeError, ValueError):
        raise InventarioError(f"El campo {campo} debe ser numérico") from None
