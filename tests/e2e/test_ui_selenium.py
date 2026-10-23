"""Pruebas de interfaz end-to-end con Selenium (Chrome/Chromium en modo headless).

En Jenkins se usan CHROME_BIN y CHROMEDRIVER (Chromium del contenedor).
En local, si no están definidas, Selenium Manager localiza Chrome solo.
"""

import os
import threading

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait
from werkzeug.serving import make_server

from app import create_app

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def servidor(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("e2e") / "e2e.db"
    app = create_app("testing", SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_file}")
    server = make_server("127.0.0.1", 0, app, threaded=True)
    hilo = threading.Thread(target=server.serve_forever, daemon=True)
    hilo.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture(scope="module")
def navegador():
    opciones = webdriver.ChromeOptions()
    for arg in (
        "--headless=new",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--window-size=1280,900",
    ):
        opciones.add_argument(arg)
    if os.environ.get("CHROME_BIN"):
        opciones.binary_location = os.environ["CHROME_BIN"]
    servicio = Service(os.environ["CHROMEDRIVER"]) if os.environ.get("CHROMEDRIVER") else None
    driver = webdriver.Chrome(options=opciones, service=servicio)
    driver.implicitly_wait(3)
    yield driver
    driver.quit()


def _esperar_texto(driver, selector, texto):
    condicion = ec.text_to_be_present_in_element((By.CSS_SELECTOR, selector), texto)
    WebDriverWait(driver, 5).until(condicion)


def test_panel_carga(servidor, navegador):
    navegador.get(servidor)
    assert "StockFlow" in navegador.title
    assert navegador.find_element(By.ID, "kpi-productos").text == "0"


def test_crear_producto_desde_formulario(servidor, navegador):
    navegador.get(f"{servidor}/productos/nuevo")
    navegador.find_element(By.ID, "sku").send_keys("TEC-100")
    navegador.find_element(By.ID, "nombre").send_keys("Monitor 24 pulgadas")
    navegador.find_element(By.ID, "categoria").send_keys("Tecnología")
    navegador.find_element(By.ID, "precio").send_keys("150")
    minimo = navegador.find_element(By.ID, "stock_minimo")
    minimo.clear()
    minimo.send_keys("2")
    navegador.find_element(By.ID, "guardar").click()

    _esperar_texto(navegador, ".aviso-ok", "TEC-100 creado")
    fila = navegador.find_element(By.CSS_SELECTOR, "tr[data-sku='TEC-100']")
    assert "Monitor 24 pulgadas" in fila.text


def test_sku_invalido_muestra_error(servidor, navegador):
    navegador.get(f"{servidor}/productos/nuevo")
    navegador.find_element(By.ID, "sku").send_keys("MAL")
    navegador.find_element(By.ID, "nombre").send_keys("Producto")
    navegador.find_element(By.ID, "precio").send_keys("1")
    navegador.find_element(By.ID, "guardar").click()
    _esperar_texto(navegador, ".aviso-error", "SKU inválido")


def test_registrar_entrada_y_ver_en_panel(servidor, navegador):
    navegador.get(f"{servidor}/movimientos")
    Select(navegador.find_element(By.ID, "tipo")).select_by_value("entrada")
    cantidad = navegador.find_element(By.ID, "cantidad")
    cantidad.clear()
    cantidad.send_keys("10")
    navegador.find_element(By.ID, "motivo").send_keys("Compra proveedor")
    navegador.find_element(By.ID, "registrar").click()
    _esperar_texto(navegador, ".aviso-ok", "Stock de TEC-100: 10")

    navegador.get(servidor)
    assert navegador.find_element(By.ID, "kpi-unidades").text == "10"
    assert navegador.find_element(By.ID, "kpi-valor").text == "$1500.00"


def test_aviso_js_si_salida_supera_stock(servidor, navegador):
    navegador.get(f"{servidor}/movimientos")
    Select(navegador.find_element(By.ID, "tipo")).select_by_value("salida")
    cantidad = navegador.find_element(By.ID, "cantidad")
    cantidad.clear()
    cantidad.send_keys("50")
    aviso = navegador.find_element(By.ID, "aviso-stock")
    WebDriverWait(navegador, 5).until(lambda d: aviso.is_displayed())
    assert "Solo hay 10 unidades" in aviso.text
