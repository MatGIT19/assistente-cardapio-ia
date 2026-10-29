"""Conexão com a API do Gemini (chat e embeddings)."""

from google import genai
from google.genai import types

from . import config


def criar_cliente() -> genai.Client:
    if not config.API_KEY:
        raise RuntimeError(
            "Defina GEMINI_API_KEY (no .env, nas variáveis de ambiente ou nos secrets do Streamlit)."
        )
    return genai.Client(api_key=config.API_KEY)


class GeminiEmbedder:
    """Gera embeddings com o Gemini, separando documentos (itens) de perguntas."""

    def __init__(self, cliente: genai.Client, modelo: str = config.EMBEDDING_MODEL):
        self.cliente = cliente
        self.nome = modelo

    def _embed(self, textos: list[str], tarefa: str) -> list[list[float]]:
        vetores = []
        for inicio in range(0, len(textos), 50):  # lotes para respeitar limites da API
            resposta = self.cliente.models.embed_content(
                model=self.nome,
                contents=textos[inicio : inicio + 50],
                config=types.EmbedContentConfig(task_type=tarefa),
            )
            vetores.extend(e.values for e in resposta.embeddings)
        return vetores

    def embed_documentos(self, textos: list[str]) -> list[list[float]]:
        return self._embed(textos, "RETRIEVAL_DOCUMENT")

    def embed_pergunta(self, texto: str) -> list[float]:
        return self._embed([texto], "RETRIEVAL_QUERY")[0]
