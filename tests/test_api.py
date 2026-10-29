from fastapi.testclient import TestClient

import api
from app.agent import Resposta


class AgenteFalso:
    def responder(self, mensagem, historico=None):
        return Resposta(texto=f"eco: {mensagem}", itens_recuperados=[{"id": "P01"}], ferramentas=[])


def test_chat_devolve_resposta(monkeypatch):
    monkeypatch.setattr(api, "agente", lambda: AgenteFalso())
    r = TestClient(api.app).post("/chat", json={"mensagem": "oi", "historico": []})
    assert r.status_code == 200
    assert r.json()["resposta"] == "eco: oi"


def test_chat_valida_entrada():
    r = TestClient(api.app).post("/chat", json={"mensagem": ""})
    assert r.status_code == 422


def test_cardapio_e_health():
    cliente = TestClient(api.app)
    assert cliente.get("/health").json() == {"status": "ok"}
    assert len(cliente.get("/cardapio").json()["itens"]) == 31
