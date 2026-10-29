"""O agente: junta a busca no cardápio (RAG) com as ferramentas (tool calling).

Fluxo de cada pergunta:
1. Busca os itens do cardápio mais parecidos com a pergunta e coloca no contexto.
2. Chama o modelo com as ferramentas disponíveis.
3. Se o modelo pedir uma ferramenta, executa a função em Python e devolve o
   resultado ao modelo. Repete até ele responder em texto (no máximo N rodadas).

O loop do passo 3 é escrito à mão (a chamada automática do SDK fica desligada)
para que cada chamada de ferramenta fique registrada e apareça na interface.
"""

from dataclasses import dataclass, field

from google.genai import types

from . import config
from .data import item_para_texto, itens
from .retrieval import IndiceCardapio
from .tools import FERRAMENTAS, FERRAMENTAS_POR_NOME

INSTRUCOES = """Você é o assistente de atendimento da Cantina Vila Nova, um restaurante de delivery.

Regras:
- Responda só com base nos itens do cardápio enviados no contexto ou nos resultados das ferramentas. Nunca invente pratos, ingredientes, preços ou informações de pedidos.
- Se a informação não estiver no cardápio, diga que não encontrou e ofereça uma alternativa que exista.
- Para perguntas de listagem (ex.: "quais pratos são veganos?", "sobremesas até R$ 20"), use filtrar_cardapio, porque o contexto traz só alguns itens.
- Para status de pedido, use consultar_pedido. Se o cliente não informou o número, peça.
- Para montar uma refeição dentro de um valor, use sugerir_combo.
- Ao falar de alérgenos, liste exatamente os alérgenos do item. Em caso de alergia grave, recomende confirmar com o restaurante.
- Responda em português, de forma curta e simpática, citando nome e preço dos itens."""


@dataclass
class Resposta:
    texto: str
    itens_recuperados: list[dict] = field(default_factory=list)
    ferramentas: list[dict] = field(default_factory=list)


class Agente:
    def __init__(
        self,
        cliente,
        indice: IndiceCardapio,
        modelo: str = config.CHAT_MODEL,
        top_k: int = config.TOP_K,
        max_rodadas: int = config.MAX_TOOL_ROUNDS,
    ):
        self.cliente = cliente
        self.indice = indice
        self.modelo = modelo
        self.top_k = top_k
        self.max_rodadas = max_rodadas
        self.config = types.GenerateContentConfig(
            system_instruction=INSTRUCOES,
            tools=FERRAMENTAS,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            temperature=0.2,
        )

    def responder(self, mensagem: str, historico: list[dict] | None = None) -> Resposta:
        """`historico` = [{"papel": "usuario" | "assistente", "texto": "..."}, ...]"""
        encontrados = self.indice.buscar(mensagem, k=self.top_k)
        contexto = "\n".join(item_para_texto(item) for item, _ in encontrados)

        conteudos = [
            types.Content(
                role="user" if m["papel"] == "usuario" else "model",
                parts=[types.Part(text=m["texto"])],
            )
            for m in historico or []
        ]
        conteudos.append(
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"Itens do cardápio relacionados à pergunta:\n{contexto}\n\n"
                        f"Mensagem do cliente: {mensagem}"
                    )
                ],
            )
        )

        resposta = Resposta(
            texto="",
            itens_recuperados=[
                {"id": item["id"], "nome": item["nome"], "similaridade": round(score, 3)}
                for item, score in encontrados
            ],
        )

        for _ in range(self.max_rodadas + 1):
            saida = self.cliente.models.generate_content(
                model=self.modelo, contents=conteudos, config=self.config
            )
            chamadas = saida.function_calls or []
            if not chamadas:
                resposta.texto = (saida.text or "").strip() or "Desculpe, não consegui responder agora."
                return resposta

            conteudos.append(saida.candidates[0].content)  # o pedido de ferramenta do modelo
            partes = []
            for chamada in chamadas:
                args = dict(chamada.args or {})
                funcao = FERRAMENTAS_POR_NOME.get(chamada.name)
                try:
                    resultado = funcao(**args) if funcao else {"erro": f"Ferramenta {chamada.name} não existe."}
                except Exception as erro:  # o modelo pode mandar argumentos inválidos
                    resultado = {"erro": str(erro)}
                resposta.ferramentas.append({"nome": chamada.name, "argumentos": args, "resultado": resultado})
                partes.append(types.Part.from_function_response(name=chamada.name, response=resultado))
            conteudos.append(types.Content(role="user", parts=partes))

        resposta.texto = "Desculpe, não consegui concluir essa solicitação. Pode reformular?"
        return resposta


def criar_agente() -> Agente:
    """Monta o agente real, com Gemini e o índice salvo em data/embeddings.json."""
    from .llm import GeminiEmbedder, criar_cliente

    cliente = criar_cliente()
    indice = IndiceCardapio(itens(), GeminiEmbedder(cliente), cache=config.DATA_DIR / "embeddings.json")
    return Agente(cliente, indice)
