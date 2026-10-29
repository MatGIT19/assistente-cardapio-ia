"""Configuração lida de variáveis de ambiente (ou de um arquivo .env)."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

try:  # .env é opcional
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# Chave da API do Gemini (crie em https://aistudio.google.com/apikey)
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")

# Os nomes dos modelos mudam com frequência: confira a lista atual na
# documentação do Gemini e troque aqui ou no .env, sem mexer no código.
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-3.8-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")

# Quantos itens do cardápio entram no contexto de cada pergunta
TOP_K = int(os.getenv("TOP_K", "5"))

# Limite de rodadas de chamada de ferramenta por pergunta (evita loop infinito)
MAX_TOOL_ROUNDS = int(os.getenv("MAX_TOOL_ROUNDS", "4"))
