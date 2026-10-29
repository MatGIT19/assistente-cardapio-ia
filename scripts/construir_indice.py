"""Gera data/embeddings.json com os embeddings do cardápio.

Rode uma vez (e de novo sempre que mudar o cardápio):  python scripts/construir_indice.py
Fazer o commit desse arquivo evita gerar os embeddings a cada deploy.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402
from app.data import itens  # noqa: E402
from app.llm import GeminiEmbedder, criar_cliente  # noqa: E402
from app.retrieval import IndiceCardapio  # noqa: E402

if __name__ == "__main__":
    cache = config.DATA_DIR / "embeddings.json"
    indice = IndiceCardapio(itens(), GeminiEmbedder(criar_cliente()), cache=cache)
    print(f"{len(indice.itens)} itens indexados com {config.EMBEDDING_MODEL} em {cache}")
    for item, score in indice.buscar("tem opção sem carne?", k=3):
        print(f"  {score:.3f}  {item['nome']}")
