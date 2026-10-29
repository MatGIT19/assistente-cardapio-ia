from app.tools import consultar_pedido, filtrar_cardapio, sugerir_combo


def test_filtrar_veganos_traz_so_itens_veganos():
    r = filtrar_cardapio(restricao="vegano")
    assert r["quantidade"] > 5
    assert all("vegano" in i["tags"] for i in r["itens"])


def test_filtro_aceita_acento_e_maiusculas():
    assert filtrar_cardapio(restricao="Sem Glúten") == filtrar_cardapio(restricao="sem_gluten")


def test_filtrar_sem_lactose_exclui_queijos():
    nomes = {i["nome"] for i in filtrar_cardapio(categoria="Pizzas", sem_alergeno="lactose")["itens"]}
    assert nomes == {"Pizza Vegana de Legumes"}


def test_filtrar_por_preco_maximo():
    r = filtrar_cardapio(categoria="Sobremesas", preco_maximo=22)
    assert r["itens"] and all(i["preco"] <= 22 for i in r["itens"])


def test_consultar_pedido_existente_aceita_cerquilha():
    r = consultar_pedido(" #1002 ")
    assert r["encontrado"] and r["status"] == "Saiu para entrega"
    assert r["total"] == 100.7


def test_consultar_pedido_inexistente():
    assert consultar_pedido("9999")["encontrado"] is False


def test_combo_respeita_orcamento_e_restricao():
    r = sugerir_combo(90, pessoas=2, restricao="vegano")
    assert r["encontrado"] and r["total"] <= 90
    assert all("vegano" in i["tags"] for i in r["por_pessoa"])


def test_combo_sem_orcamento_suficiente():
    r = sugerir_combo(10)
    assert r["encontrado"] is False and r["valor_minimo_por_pessoa"] > 10
