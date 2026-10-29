"""API REST do assistente. Rode com: uvicorn api:app --reload

Documentação interativa em http://localhost:8000/docs
"""

from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent import Agente, criar_agente
from app.data import itens

app = FastAPI(title="Assistente de Cardápio", version="1.0.0")


class Mensagem(BaseModel):
    papel: str = Field(pattern="^(usuario|assistente)$")
    texto: str


class PerguntaChat(BaseModel):
    mensagem: str = Field(min_length=1, max_length=1000)
    historico: list[Mensagem] = []


class RespostaChat(BaseModel):
    resposta: str
    itens_recuperados: list[dict]
    ferramentas: list[dict]


@lru_cache
def agente() -> Agente:
    return criar_agente()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/cardapio")
def cardapio():
    return {"itens": itens()}


@app.post("/chat", response_model=RespostaChat)
def chat(pergunta: PerguntaChat):
    try:
        r = agente().responder(pergunta.mensagem, [m.model_dump() for m in pergunta.historico])
    except RuntimeError as erro:  # chave da API ausente
        raise HTTPException(status_code=500, detail=str(erro))
    return RespostaChat(resposta=r.texto, itens_recuperados=r.itens_recuperados, ferramentas=r.ferramentas)
