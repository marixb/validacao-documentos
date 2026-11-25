"""Configuração dos testes: usa um banco e uma pasta temporários (não mexe nos seus dados)."""
import os
import tempfile
from pathlib import Path

PASTA_TEMP = Path(tempfile.mkdtemp(prefix="testes_validacao_"))
os.environ["DATABASE_URL"] = f"sqlite:///{PASTA_TEMP / 'teste.db'}"
os.environ["PASTA_ARQUIVOS"] = str(PASTA_TEMP / "arquivos")
os.environ["IA_API_KEY"] = ""   # os testes nunca chamam a IA de verdade
os.environ["IA_MODELO"] = ""
