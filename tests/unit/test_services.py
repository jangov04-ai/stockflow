import pytest

from app import services
from app.models import Categoria, Movimiento
from app.services import InventarioError


def _producto(sku="PAP-001", nombre="Resma A4", precio=4.5, minimo=5, categoria="papelería"):
    return services.crear_producto(sku, nombre, precio, minimo, categoria)


class TestCrearProducto:
    def test_crea_producto_con_stock_cero(self, app):
        p = _producto()
        assert p.id is not None
        assert p.stock == 0
        assert p.sku == "PAP-001"

    def test_normaliza_sku_y_categoria(self, app):
        p = _producto(sku="  tec-010 ", categoria="  tecnología ")
        assert p.sku == "TEC-010"
        assert p.categoria.nombre == "Tecnología"

    def test_reutiliza_categoria_existente(self, app):
        _producto(sku="PAP-001", categoria="Papelería")
        _producto(sku="PAP-002", categoria="papelería")
        assert Categoria.query.count() == 1

    def test_redondea_precio(self, app):
        assert _producto(precio="3.456").precio == 3.46

    @pytest.mark.parametrize("sku", ["", "A-1", "SINGUION", "ABC-12", "abc_001"])
    def test_rechaza_sku_invalido(self, app, sku):
        with pytest.raises(InventarioError, match="SKU"):
            _producto(sku=sku)

    def test_rechaza_sku_duplicado(self, app):
        _producto()
        with pytest.raises(InventarioError, match="Ya existe"):
            _producto()

    def test_rechaza_nombre_corto(self, app):
        with pytest.raises(InventarioError, match="nombre"):
            _producto(nombre="A")

    @pytest.mark.parametrize("precio", [-1, "abc", None])
    def test_rechaza_precio_invalido(self, app, precio):
        with pytest.raises(InventarioError):
            _producto(precio=precio)

    def test_rechaza_stock_minimo_negativo(self, app):
        with pytest.raises(InventarioError, match="negativo"):
            _producto(minimo=-3)


class TestMovimientos:
    def test_entrada_suma_stock(self, app):
        p = _producto()
        services.registrar_movimiento(p, Movimiento.ENTRADA, 10, "compra")
        assert p.stock == 10

    def test_salida_resta_stock(self, app):
        p = _producto()
        services.registrar_movimiento(p, Movimiento.ENTRADA, 10)
        services.registrar_movimiento(p, Movimiento.SALIDA, 4, "venta")
        assert p.stock == 6
        assert len(p.movimientos) == 2

    def test_no_permite_stock_negativo(self, app):
        p = _producto()
        services.registrar_movimiento(p, Movimiento.ENTRADA, 2)
        with pytest.raises(InventarioError, match="Stock insuficiente"):
            services.registrar_movimiento(p, Movimiento.SALIDA, 3)
        assert p.stock == 2

    @pytest.mark.parametrize("cantidad", [0, -5, "x"])
    def test_rechaza_cantidad_invalida(self, app, cantidad):
        p = _producto()
        with pytest.raises(InventarioError):
            services.registrar_movimiento(p, Movimiento.ENTRADA, cantidad)

    def test_rechaza_tipo_desconocido(self, app):
        with pytest.raises(InventarioError, match="tipo"):
            services.registrar_movimiento(_producto(), "devolucion", 1)


class TestConsultas:
    def test_stock_bajo_y_resumen(self, app):
        a = _producto(sku="PAP-001", precio=2, minimo=5)
        b = _producto(sku="PAP-002", precio=10, minimo=5)
        services.registrar_movimiento(a, Movimiento.ENTRADA, 3)
        services.registrar_movimiento(b, Movimiento.ENTRADA, 20)

        assert [p.sku for p in services.productos_con_stock_bajo()] == ["PAP-001"]
        resumen = services.resumen_inventario()
        assert resumen["total_productos"] == 2
        assert resumen["unidades_totales"] == 23
        assert resumen["valor_inventario"] == 206.0
        assert resumen["productos_stock_bajo"] == 1
        assert resumen["total_categorias"] == 1

    def test_buscar_por_nombre_o_sku(self, app):
        _producto(sku="PAP-001", nombre="Resma A4")
        _producto(sku="TEC-001", nombre="Mouse", categoria="Tecnología")
        assert [p.sku for p in services.buscar_productos("mouse")] == ["TEC-001"]
        assert [p.sku for p in services.buscar_productos("pap")] == ["PAP-001"]
        assert len(services.buscar_productos("")) == 2

    def test_actualizar_y_eliminar(self, app):
        p = _producto()
        services.actualizar_producto(p, nombre="Resma Carta", precio=5, stock_minimo=2)
        assert (p.nombre, p.precio, p.stock_minimo) == ("Resma Carta", 5.0, 2)
        services.eliminar_producto(p)
        assert services.buscar_productos() == []
