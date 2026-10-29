from google.genai import types

from app.agent import Agente
from app.data import itens
from app.retrieval import IndiceCardapio
from conftest import ClienteFalso


def _texto(t: str) -> types.GenerateContentResponse:
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=[types.Part(text=t)]))]
    )


def _ferramenta(nome: str, **args) -> types.GenerateContentResponse:
    chamada = types.Part(function_call=types.FunctionCall(name=nome, args=args))
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=[chamada]))]
    )


def test_resposta_direta_inclui_itens_do_cardapio_no_contexto(embedder):
    cliente = ClienteFalso([_texto("A Margherita custa R$ 49,90.")])
    agente = Agente(cliente, IndiceCardapio(itens(), embedder))

    r = agente.responder("Quanto custa a pizza margherita?")

    assert r.texto == "A Margherita custa R$ 49,90."
    assert r.ferramentas == []
    prompt = cliente.models.chamadas[0][-1].parts[0].text
    assert "Pizza Margherita" in prompt  # o RAG colocou o item no contexto


def test_executa_ferramenta_e_devolve_resultado_ao_modelo(embedder):
    cliente = ClienteFalso([_ferramenta("consultar_pedido", pedido_id="1002"), _texto("Seu pedido saiu.")])
    agente = Agente(cliente, IndiceCardapio(itens(), embedder))

    r = agente.responder("Cadê o pedido 1002?")

    assert r.texto == "Seu pedido saiu."
    assert r.ferramentas[0]["nome"] == "consultar_pedido"
    assert r.ferramentas[0]["resultado"]["status"] == "Saiu para entrega"
    devolvido = cliente.models.chamadas[1][-1].parts[0].function_response
    assert devolvido.name == "consultar_pedido"


def test_argumento_invalido_vira_erro_e_nao_quebra(embedder):
    cliente = ClienteFalso([_ferramenta("consultar_pedido", numero="1"), _texto("Qual o número?")])
    r = Agente(cliente, IndiceCardapio(itens(), embedder)).responder("meu pedido")
    assert "erro" in r.ferramentas[0]["resultado"]
    assert r.texto == "Qual o número?"


def test_para_depois_do_limite_de_rodadas(embedder):
    respostas = [_ferramenta("filtrar_cardapio") for _ in range(10)]
    agente = Agente(ClienteFalso(respostas), IndiceCardapio(itens(), embedder), max_rodadas=2)
    r = agente.responder("liste tudo")
    assert len(r.ferramentas) == 3
    assert "não consegui" in r.texto


def test_historico_vira_turnos_do_usuario_e_do_modelo(embedder):
    cliente = ClienteFalso([_texto("ok")])
    historico = [{"papel": "usuario", "texto": "oi"}, {"papel": "assistente", "texto": "olá!"}]
    Agente(cliente, IndiceCardapio(itens(), embedder)).responder("e a sobremesa?", historico)
    papeis = [c.role for c in cliente.models.chamadas[0]]
    assert papeis == ["user", "model", "user"]
