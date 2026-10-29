"""Ferramentas que o modelo pode chamar (tool calling).

São funções Python puras sobre os dados: o modelo decide QUANDO chamar e com
QUAIS argumentos; o código garante que a resposta é exata. O SDK do Gemini lê
os type hints e as docstrings para descrever cada ferramenta ao modelo, por isso
elas estão escritas com cuidado.
"""

import itertools
import unicodedata

from .data import carregar_pedidos, item_por_id, itens

STATUS_LEGIVEL = {
    "recebido": "Pedido recebido pelo restaurante, aguardando início do preparo",
    "em_preparo": "Em preparo na cozinha",
    "saiu_para_entrega": "Saiu para entrega",
    "entregue": "Entregue",
    "cancelado": "Cancelado",
}

PRATOS_PRINCIPAIS = {"pizzas", "massas", "lanches", "saladas"}


def _norm(texto: str) -> str:
    """Minúsculas, sem acento e sem espaços extras ('Sem Glúten' -> 'sem gluten')."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().replace("_", " ").split())


def _resumo(item: dict) -> dict:
    return {
        "id": item["id"],
        "nome": item["nome"],
        "preco": item["preco"],
        "alergenos": item["alergenos"],
        "tags": item["tags"],
    }


def _atende(item: dict, restricao: str, sem_alergeno: str) -> bool:
    if restricao and _norm(restricao) not in {_norm(t) for t in item["tags"]}:
        return False
    if sem_alergeno:
        alvo = _norm(sem_alergeno).rstrip("s")  # "castanha" casa com "castanhas"
        if any(alvo in _norm(a) for a in item["alergenos"]):
            return False
    return True


def filtrar_cardapio(
    categoria: str = "",
    restricao: str = "",
    sem_alergeno: str = "",
    preco_maximo: float = 0.0,
) -> dict:
    """Lista TODOS os itens do cardápio que atendem aos filtros. Use para perguntas
    de listagem, como "quais pratos são veganos?" ou "sobremesas sem lactose até R$ 25".

    Args:
      categoria: Pizzas, Massas, Lanches, Saladas, Entradas, Sobremesas ou Bebidas. Vazio = todas.
      restricao: vegano, vegetariano, sem_gluten ou picante. Vazio = sem filtro.
      sem_alergeno: alérgeno a excluir, por exemplo lactose, glúten, ovo, castanhas, crustáceos. Vazio = sem filtro.
      preco_maximo: preço máximo em reais. 0 = sem limite.
    """
    resultado = [
        _resumo(i)
        for i in itens()
        if (not categoria or _norm(i["categoria"]) == _norm(categoria))
        and _atende(i, restricao, sem_alergeno)
        and (not preco_maximo or i["preco"] <= preco_maximo)
    ]
    return {"quantidade": len(resultado), "itens": resultado}


def consultar_pedido(pedido_id: str) -> dict:
    """Consulta o status de um pedido pelo número, por exemplo "1002".

    Args:
      pedido_id: número do pedido informado pelo cliente.
    """
    pid = pedido_id.strip().lstrip("#").strip()
    pedido = next((p for p in carregar_pedidos()["pedidos"] if p["id"] == pid), None)
    if pedido is None:
        return {"encontrado": False, "mensagem": f"Nenhum pedido com o número {pid}."}

    linhas, total = [], 0.0
    for linha in pedido["itens"]:
        item = item_por_id(linha["id"])
        linhas.append(f"{linha['qtd']}x {item['nome']}")
        total += item["preco"] * linha["qtd"]

    resposta = {
        "encontrado": True,
        "pedido_id": pid,
        "cliente": pedido["cliente"],
        "status": STATUS_LEGIVEL[pedido["status"]],
        "itens": linhas,
        "total": round(total, 2),
    }
    for campo in ("previsao_entrega", "entregue_em", "atraso_min", "motivo_cancelamento"):
        if campo in pedido:
            resposta[campo] = pedido[campo]
    return resposta


def sugerir_combo(
    orcamento: float,
    pessoas: int = 1,
    restricao: str = "",
    sem_alergeno: str = "",
) -> dict:
    """Monta a refeição mais completa possível dentro do orçamento: um prato principal
    e uma bebida por pessoa, mais uma sobremesa se couber.

    Args:
      orcamento: valor total disponível em reais.
      pessoas: quantas pessoas vão comer.
      restricao: vegano, vegetariano ou sem_gluten. Vazio = sem filtro.
      sem_alergeno: alérgeno a excluir, por exemplo lactose. Vazio = sem filtro.
    """
    pessoas = max(1, int(pessoas))
    por_pessoa = orcamento / pessoas
    ok = [i for i in itens() if _atende(i, restricao, sem_alergeno)]
    principais = [i for i in ok if _norm(i["categoria"]) in PRATOS_PRINCIPAIS]
    bebidas = [i for i in ok if i["categoria"] == "Bebidas"]
    sobremesas = [None] + [i for i in ok if i["categoria"] == "Sobremesas"]

    melhor, melhor_chave = None, None
    for prato, bebida, doce in itertools.product(principais, bebidas, sobremesas):
        combo = [x for x in (prato, bebida, doce) if x]
        valor = sum(x["preco"] for x in combo)
        if valor > por_pessoa:
            continue
        chave = (len(combo), valor)  # prefere combos completos e depois o maior valor
        if melhor_chave is None or chave > melhor_chave:
            melhor, melhor_chave = combo, chave

    if melhor is None:
        minimo = min((p["preco"] + b["preco"] for p in principais for b in bebidas), default=None)
        return {
            "encontrado": False,
            "mensagem": "Nenhuma combinação de prato e bebida cabe no orçamento.",
            "valor_minimo_por_pessoa": minimo,
        }

    total = round(sum(x["preco"] for x in melhor) * pessoas, 2)
    return {
        "encontrado": True,
        "por_pessoa": [_resumo(x) for x in melhor],
        "pessoas": pessoas,
        "total": total,
        "sobra": round(orcamento - total, 2),
    }


FERRAMENTAS = [filtrar_cardapio, consultar_pedido, sugerir_combo]
FERRAMENTAS_POR_NOME = {f.__name__: f for f in FERRAMENTAS}
