"""Busca semântica no cardápio (a parte "R" do RAG).

Com ~30 itens, um índice em memória com numpy é suficiente e não exige
nenhum serviço extra. Para milhares de itens, troque por ChromaDB ou pgvector:
a interface `buscar()` continua a mesma.
"""

import hashlib
import json
from pathlib import Path
from typing import Protocol

import numpy as np

from .data import item_para_texto


class Embedder(Protocol):
    nome: str

    def embed_documentos(self, textos: list[str]) -> list[list[float]]: ...

    def embed_pergunta(self, texto: str) -> list[float]: ...


def _normalizar(m: np.ndarray) -> np.ndarray:
    norma = np.linalg.norm(m, axis=-1, keepdims=True)
    return m / np.where(norma == 0, 1, norma)


class IndiceCardapio:
    def __init__(self, itens: list[dict], embedder: Embedder, cache: Path | None = None):
        self.itens = itens
        self.embedder = embedder
        self.textos = [item_para_texto(i) for i in itens]
        self.matriz = _normalizar(np.array(self._embeddings(cache), dtype=np.float32))

    def _embeddings(self, cache: Path | None) -> list[list[float]]:
        """Reaproveita embeddings salvos se o texto e o modelo não mudaram."""
        assinatura = hashlib.sha256(
            (self.embedder.nome + "\n".join(self.textos)).encode()
        ).hexdigest()
        if cache and cache.exists():
            salvo = json.loads(cache.read_text(encoding="utf-8"))
            if salvo.get("assinatura") == assinatura:
                return salvo["vetores"]
        vetores = self.embedder.embed_documentos(self.textos)
        if cache:
            cache.write_text(
                json.dumps({"assinatura": assinatura, "modelo": self.embedder.nome, "vetores": vetores}),
                encoding="utf-8",
            )
        return vetores

    def buscar(self, pergunta: str, k: int = 5) -> list[tuple[dict, float]]:
        """Devolve os k itens mais parecidos com a pergunta e a similaridade (cosseno)."""
        q = _normalizar(np.array(self.embedder.embed_pergunta(pergunta), dtype=np.float32))
        scores = self.matriz @ q
        melhores = np.argsort(-scores)[:k]
        return [(self.itens[i], float(scores[i])) for i in melhores]
