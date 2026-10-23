from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _ahora():
    return datetime.now(timezone.utc)


class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    productos = db.relationship("Producto", back_populates="categoria")

    def to_dict(self):
        return {"id": self.id, "nombre": self.nombre, "total_productos": len(self.productos)}


class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(30), unique=True, nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    precio = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=5)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"))
    categoria = db.relationship("Categoria", back_populates="productos")
    movimientos = db.relationship(
        "Movimiento", back_populates="producto", cascade="all, delete-orphan"
    )

    @property
    def stock_bajo(self):
        return self.stock <= self.stock_minimo

    @property
    def valor_total(self):
        return round(self.stock * self.precio, 2)

    def to_dict(self):
        return {
            "id": self.id,
            "sku": self.sku,
            "nombre": self.nombre,
            "precio": self.precio,
            "stock": self.stock,
            "stock_minimo": self.stock_minimo,
            "stock_bajo": self.stock_bajo,
            "valor_total": self.valor_total,
            "categoria": self.categoria.nombre if self.categoria else None,
        }


class Movimiento(db.Model):
    ENTRADA = "entrada"
    SALIDA = "salida"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"), nullable=False)
    producto = db.relationship("Producto", back_populates="movimientos")
    tipo = db.Column(db.String(10), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(200))
    fecha = db.Column(db.DateTime(timezone=True), default=_ahora, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "producto": self.producto.nombre,
            "sku": self.producto.sku,
            "tipo": self.tipo,
            "cantidad": self.cantidad,
            "motivo": self.motivo,
            "fecha": self.fecha.isoformat(),
        }
