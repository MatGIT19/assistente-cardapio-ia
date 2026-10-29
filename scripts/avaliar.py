"""Avalia o agente em 15 perguntas com resposta conhecida.

Rode com: python scripts/avaliar.py   (precisa de GEMINI_API_KEY)
Gera resultados_avaliacao.md com a tabela de acertos.

A checagem é simples e de propósito: cada caso lista palavras que a resposta
precisa conter (grupos em que basta uma das alternativas) e, quando faz
sentido, a ferramenta que o agente deveria ter chamado. Não substitui uma
revisão humana, mas pega regressões e alucinações óbvias.
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.agent import criar_agente  # noqa: E402
from app.tools import _norm  # noqa: E402

CASOS = [
    {"pergunta": "Quanto custa a pizza margherita?", "checar": [["49,90", "49.90", "49,9"]]},
    {"pergunta": "A pizza de calabresa tem lactose?", "checar": [["sim", "contem lactose", "tem lactose"]]},
    {"pergunta": "Quais pratos são veganos?", "checar": [["hamburguer vegano"], ["nhoque"]], "ferramenta": "filtrar_cardapio"},
    {"pergunta": "Tem alguma sobremesa sem lactose?", "checar": [["mousse", "salada de frutas"]]},
    {"pergunta": "O risoto de camarão tem glúten?", "checar": [["nao", "sem gluten"]]},
    {"pergunta": "Cadê meu pedido 1006?", "checar": [["saiu para entrega", "a caminho"]], "ferramenta": "consultar_pedido"},
    {"pergunta": "Meu pedido 1005 vai chegar?", "checar": [["cancel"]], "ferramenta": "consultar_pedido"},
    {"pergunta": "Qual o status do pedido 9999?", "checar": [["nao encontr", "nenhum pedido", "nao localiz"]], "ferramenta": "consultar_pedido"},
    {"pergunta": "Quero saber do meu pedido", "checar": [["numero"]]},
    {"pergunta": "Tenho R$ 100 para duas pessoas, o que você sugere?", "checar": [["r$"]], "ferramenta": "sugerir_combo"},
    {"pergunta": "Vocês têm sushi?", "checar": [["nao"]]},
    {"pergunta": "Quais massas não têm glúten?", "checar": [["nhoque"], ["lasanha"], ["risoto"]], "ferramenta": "filtrar_cardapio"},
    {"pergunta": "Tenho alergia a castanha, posso comer o penne ao pesto?", "checar": [["castanha"], ["nao"]]},
    {"pergunta": "Qual a entrada mais barata?", "checar": [["batata frita"]]},
    {"pergunta": "Quanto tempo demora o petit gâteau?", "checar": [["12"]]},
]


def avaliar_caso(agente, caso: dict) -> dict:
    inicio = time.perf_counter()
    r = agente.responder(caso["pergunta"])
    segundos = time.perf_counter() - inicio
    texto = _norm(r.texto)
    conteudo_ok = all(any(_norm(alt) in texto for alt in grupo) for grupo in caso["checar"])
    chamadas = [f["nome"] for f in r.ferramentas]
    ferramenta_ok = caso.get("ferramenta") is None or caso["ferramenta"] in chamadas
    return {
        "pergunta": caso["pergunta"],
        "ok": conteudo_ok and ferramenta_ok,
        "ferramentas": ", ".join(chamadas) or "-",
        "segundos": segundos,
        "resposta": r.texto.replace("\n", " "),
    }


def main():
    agente = criar_agente()
    resultados = []
    for i, caso in enumerate(CASOS, 1):
        res = avaliar_caso(agente, caso)
        resultados.append(res)
        print(f"{i:2}. {'OK  ' if res['ok'] else 'FALHOU'} {res['pergunta']}  [{res['ferramentas']}]")
        time.sleep(4)  # respeita o limite de requisições por minuto da camada gratuita

    acertos = sum(r["ok"] for r in resultados)
    media = sum(r["segundos"] for r in resultados) / len(resultados)
    linhas = [
        "# Resultados da avaliação",
        "",
        f"**{acertos} de {len(resultados)} perguntas corretas** · tempo médio {media:.1f} s por resposta",
        "",
        "| # | Pergunta | Resultado | Ferramentas | Resposta |",
        "|---|---|---|---|---|",
    ]
    for i, r in enumerate(resultados, 1):
        resposta = r["resposta"][:160] + ("…" if len(r["resposta"]) > 160 else "")
        linhas.append(
            f"| {i} | {r['pergunta']} | {'✅' if r['ok'] else '❌'} | {r['ferramentas']} | {resposta.replace('|', '/')} |"
        )
    (ROOT / "resultados_avaliacao.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"\n{acertos}/{len(resultados)} corretas. Tabela salva em resultados_avaliacao.md")


if __name__ == "__main__":
    main()
