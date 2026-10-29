"""Dublês para testar sem chamar a API do Gemini."""

import hashlib
import re

import pytest

from app.tools import _norm


class EmbedderFalso:
    """Embedding por "saco de palavras" com hashing: parecido o bastante para testar a busca."""

    nome = "falso"
    dim = 256

    def _vetor(self, texto: str) -> list[float]:
        v = [0.0] * self.dim
        for palavra in re.findall(r"[a-z0-9]+", _norm(texto)):
            v[int(hashlib.md5(palavra.encode()).hexdigest(), 16) % self.dim] += 1
        return v

    def embed_documentos(self, textos):
        return [self._vetor(t) for t in textos]

    def embed_pergunta(self, texto):
        return self._vetor(texto)


class _Modelos:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def generate_content(self, model, contents, config):
        self.chamadas.append(list(contents))
        return self.respostas.pop(0)


class ClienteFalso:
    """Devolve, em ordem, as respostas roteirizadas do "modelo"."""

    def __init__(self, respostas):
        self.models = _Modelos(respostas)


@pytest.fixture
def embedder():
    return EmbedderFalso()
