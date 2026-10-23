def _crear(client, sku="TEC-001", nombre="Mouse", precio=10, minimo=3, categoria="Tecnología"):
    return client.post(
        "/api/productos",
        json={
            "sku": sku,
            "nombre": nombre,
            "precio": precio,
            "stock_minimo": minimo,
            "categoria": categoria,
        },
    )


def test_salud(client):
    assert client.get("/salud").get_json() == {"estado": "ok"}


def test_crear_y_obtener_producto(client):
    r = _crear(client)
    assert r.status_code == 201
    producto = r.get_json()
    assert producto["sku"] == "TEC-001"
    assert producto["categoria"] == "Tecnología"

    r = client.get(f"/api/productos/{producto['id']}")
    assert r.status_code == 200
    assert r.get_json()["nombre"] == "Mouse"


def test_crear_producto_invalido_devuelve_400(client):
    r = _crear(client, sku="malo")
    assert r.status_code == 400
    assert "SKU" in r.get_json()["error"]


def test_producto_inexistente_devuelve_404(client):
    r = client.get("/api/productos/999")
    assert r.status_code == 404
    assert r.get_json() == {"error": "Recurso no encontrado"}


def test_movimientos_actualizan_stock(client):
    pid = _crear(client).get_json()["id"]

    r = client.post(f"/api/productos/{pid}/movimientos", json={"tipo": "entrada", "cantidad": 8})
    assert r.status_code == 201
    assert r.get_json()["producto"]["stock"] == 8

    r = client.post(f"/api/productos/{pid}/movimientos", json={"tipo": "salida", "cantidad": 6})
    assert r.get_json()["producto"]["stock"] == 2
    assert r.get_json()["producto"]["stock_bajo"] is True

    r = client.post(f"/api/productos/{pid}/movimientos", json={"tipo": "salida", "cantidad": 99})
    assert r.status_code == 400
    assert "insuficiente" in r.get_json()["error"]

    movimientos = client.get("/api/movimientos").get_json()
    assert [m["tipo"] for m in movimientos] == ["salida", "entrada"]


def test_listado_filtra_stock_bajo_y_busqueda(client):
    a = _crear(client, sku="TEC-001", nombre="Mouse").get_json()["id"]
    _crear(client, sku="TEC-002", nombre="Teclado")
    client.post(f"/api/productos/{a}/movimientos", json={"tipo": "entrada", "cantidad": 50})

    assert len(client.get("/api/productos").get_json()) == 2
    bajos = client.get("/api/productos?stock_bajo=1").get_json()
    assert [p["sku"] for p in bajos] == ["TEC-002"]
    assert [p["sku"] for p in client.get("/api/productos?q=tecl").get_json()] == ["TEC-002"]


def test_actualizar_y_eliminar(client):
    pid = _crear(client).get_json()["id"]
    r = client.put(f"/api/productos/{pid}", json={"precio": 15.5, "categoria": "Oficina"})
    assert r.get_json()["precio"] == 15.5
    assert r.get_json()["categoria"] == "Oficina"

    assert client.delete(f"/api/productos/{pid}").status_code == 204
    assert client.get(f"/api/productos/{pid}").status_code == 404


def test_resumen_y_categorias(client):
    pid = _crear(client, precio=2.5).get_json()["id"]
    client.post(f"/api/productos/{pid}/movimientos", json={"tipo": "entrada", "cantidad": 4})

    resumen = client.get("/api/resumen").get_json()
    assert resumen["valor_inventario"] == 10.0
    assert resumen["unidades_totales"] == 4

    categorias = client.get("/api/categorias").get_json()
    assert categorias == [{"id": 1, "nombre": "Tecnología", "total_productos": 1}]


def test_paginas_web_responden(client):
    pid = _crear(client).get_json()["id"]
    for ruta in [
        "/",
        "/productos",
        "/productos/nuevo",
        f"/productos/{pid}/editar",
        "/movimientos",
        "/categorias",
        "/productos?q=mouse",
    ]:
        assert client.get(ruta).status_code == 200, ruta


def test_formularios_web(client):
    r = client.post(
        "/productos/nuevo",
        data={"sku": "LIM-001", "nombre": "Jabón", "precio": "1.5", "stock_minimo": "2"},
    )
    assert r.status_code == 302

    r = client.post("/productos/nuevo", data={"sku": "x", "nombre": "Jabón", "precio": "1"})
    assert r.status_code == 400
    assert "SKU inválido" in r.get_data(as_text=True)

    r = client.post("/movimientos", data={"producto_id": 1, "tipo": "entrada", "cantidad": 5})
    assert r.status_code == 302
    assert client.get("/api/productos/1").get_json()["stock"] == 5

    r = client.post(
        "/productos/1/editar",
        data={
            "nombre": "Jabón líquido",
            "precio": "2",
            "stock_minimo": "1",
            "categoria": "Limpieza",
        },
    )
    assert r.status_code == 302
    assert client.post("/productos/1/eliminar").status_code == 302
