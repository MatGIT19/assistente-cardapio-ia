"""Carrega o cardápio e os pedidos fictícios."""

import json
from functools import lru_cache

from .config import DATA_DIR


@lru_cache
def carregar_cardapio() -> dict:
    with open(DATA_DIR / "cardapio.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def carregar_pedidos() -> dict:
    with open(DATA_DIR / "pedidos.json", encoding="utf-8") as f:
        return json.load(f)


def itens() -> list[dict]:
    return carregar_cardapio()["itens"]


def item_por_id(item_id: str) -> dict | None:
    return next((i for i in itens() if i["id"] == item_id), None)


def item_para_texto(item: dict) -> str:
    """Texto usado para gerar o embedding e para mostrar o item ao modelo."""
    tags = ", ".join(item["tags"]) or "nenhuma"
    alergenos = ", ".join(item["alergenos"]) or "nenhum"
    return (
        f"[{item['id']}] {item['nome']} ({item['categoria']}) - R$ {item['preco']:.2f}. "
        f"{item['descricao']} Ingredientes: {', '.join(item['ingredientes'])}. "
        f"Alérgenos: {alergenos}. Tags: {tags}. "
        f"Preparo: {item['tempo_preparo_min']} min."
    )
