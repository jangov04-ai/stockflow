"""Carga datos de ejemplo: python seed.py"""

from app import create_app
from app import services
from app.models import Producto

DATOS = [
    ("PAP-001", "Resma papel A4", 4.50, 10, "Papelería", 40),
    ("PAP-002", "Bolígrafo azul (caja 12)", 3.20, 5, "Papelería", 3),
    ("TEC-001", "Mouse inalámbrico", 12.99, 4, "Tecnología", 15),
    ("TEC-002", "Teclado USB", 18.50, 4, "Tecnología", 2),
    ("LIM-001", "Desinfectante 1L", 2.75, 8, "Limpieza", 25),
]


def cargar():
    app = create_app("development")
    with app.app_context():
        for sku, nombre, precio, minimo, categoria, stock in DATOS:
            if Producto.query.filter_by(sku=sku).first():
                continue
            producto = services.crear_producto(sku, nombre, precio, minimo, categoria)
            services.registrar_movimiento(producto, "entrada", stock, "Inventario inicial")
        print(f"Productos en la base de datos: {Producto.query.count()}")


if __name__ == "__main__":
    cargar()
