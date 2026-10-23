from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from .. import services
from ..models import Categoria, Movimiento, Producto, db

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def dashboard():
    return render_template(
        "dashboard.html",
        resumen=services.resumen_inventario(),
        stock_bajo=services.productos_con_stock_bajo(),
        ultimos=Movimiento.query.order_by(Movimiento.fecha.desc()).limit(5).all(),
    )


@web_bp.route("/productos")
def lista_productos():
    texto = request.args.get("q", "")
    return render_template(
        "productos/lista.html", productos=services.buscar_productos(texto), q=texto
    )


@web_bp.route("/productos/nuevo", methods=["GET", "POST"])
def nuevo_producto():
    if request.method == "POST":
        try:
            producto = services.crear_producto(
                sku=request.form.get("sku"),
                nombre=request.form.get("nombre"),
                precio=request.form.get("precio"),
                stock_minimo=request.form.get("stock_minimo", 5),
                categoria=request.form.get("categoria"),
            )
        except services.InventarioError as error:
            db.session.rollback()
            flash(str(error), "error")
            return render_template("productos/form.html", producto=None, datos=request.form), 400
        flash(f"Producto {producto.sku} creado", "ok")
        return redirect(url_for("web.lista_productos"))
    return render_template("productos/form.html", producto=None, datos={})


@web_bp.route("/productos/<int:producto_id>/editar", methods=["GET", "POST"])
def editar_producto(producto_id):
    producto = db.get_or_404(Producto, producto_id)
    if request.method == "POST":
        try:
            services.actualizar_producto(
                producto,
                nombre=request.form.get("nombre"),
                precio=request.form.get("precio"),
                stock_minimo=request.form.get("stock_minimo"),
                categoria=request.form.get("categoria", ""),
            )
        except services.InventarioError as error:
            db.session.rollback()
            flash(str(error), "error")
            return (
                render_template("productos/form.html", producto=producto, datos=request.form),
                400,
            )
        flash(f"Producto {producto.sku} actualizado", "ok")
        return redirect(url_for("web.lista_productos"))
    datos = {
        "nombre": producto.nombre,
        "precio": producto.precio,
        "stock_minimo": producto.stock_minimo,
        "categoria": producto.categoria.nombre if producto.categoria else "",
    }
    return render_template("productos/form.html", producto=producto, datos=datos)


@web_bp.route("/productos/<int:producto_id>/eliminar", methods=["POST"])
def eliminar_producto(producto_id):
    producto = db.get_or_404(Producto, producto_id)
    services.eliminar_producto(producto)
    flash(f"Producto {producto.sku} eliminado", "ok")
    return redirect(url_for("web.lista_productos"))


@web_bp.route("/movimientos", methods=["GET", "POST"])
def movimientos():
    if request.method == "POST":
        producto = db.session.get(Producto, request.form.get("producto_id", type=int))
        if producto is None:
            flash("Selecciona un producto válido", "error")
        else:
            try:
                services.registrar_movimiento(
                    producto,
                    request.form.get("tipo"),
                    request.form.get("cantidad"),
                    request.form.get("motivo", ""),
                )
                flash(f"Movimiento registrado. Stock de {producto.sku}: {producto.stock}", "ok")
                return redirect(url_for("web.movimientos"))
            except services.InventarioError as error:
                db.session.rollback()
                flash(str(error), "error")
    return render_template(
        "movimientos/lista.html",
        productos=Producto.query.order_by(Producto.nombre).all(),
        movimientos=Movimiento.query.order_by(Movimiento.fecha.desc()).limit(50).all(),
    )


@web_bp.route("/categorias")
def categorias():
    return render_template(
        "categorias.html", categorias=Categoria.query.order_by(Categoria.nombre).all()
    )


@web_bp.route("/productos/exportar.csv")
def exportar_productos():
    contenido = services.exportar_csv(services.buscar_productos(request.args.get("q", "")))
    return Response(
        contenido,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventario.csv"},
    )


@web_bp.route("/salud")
def salud():
    return {"estado": "ok"}
