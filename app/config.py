"""Configurações lidas do arquivo .env (ou das variáveis de ambiente do servidor)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PASTA_PROJETO = Path(__file__).resolve().parent.parent

# Banco de dados (SQLite por padrão: um arquivo dentro do projeto)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{PASTA_PROJETO / 'documentos.db'}")
if DATABASE_URL.startswith("postgres://"):  # formato usado por alguns serviços (ex.: Render)
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Pasta onde os arquivos enviados são guardados
PASTA_ARQUIVOS = Path(os.getenv("PASTA_ARQUIVOS", PASTA_PROJETO / "armazenamento"))

# IA (opcional). Qualquer serviço compatível com a API da OpenAI:
# OpenAI, Azure OpenAI, Google Gemini, Groq, Ollama (local)...
IA_API_KEY = os.getenv("IA_API_KEY", "")
IA_BASE_URL = os.getenv("IA_BASE_URL", "") or None
IA_MODELO = os.getenv("IA_MODELO", "")

# Regras de negócio
PRAZO_MAXIMO_DIAS = int(os.getenv("PRAZO_MAXIMO_DIAS", "90"))
CONFIANCA_MINIMA_OCR = float(os.getenv("CONFIANCA_MINIMA_OCR", "60"))
TAMANHO_MAXIMO_MB = int(os.getenv("TAMANHO_MAXIMO_MB", "10"))
