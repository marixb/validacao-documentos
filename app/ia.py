"""Etapa de IA: transforma o texto bruto do OCR em dados estruturados.

Funciona em dois modos:
  1. Com IA configurada (IA_API_KEY e IA_MODELO no .env): um modelo de linguagem
     lê o texto e devolve um JSON com os campos. Os valores são conferidos
     (CPF, CEP e data) antes de serem aceitos.
  2. Sem IA (ou se a IA falhar): extração por padrões (expressões regulares).
"""
import json
import logging
import re
import unicodedata
from datetime import date

from app import config
from app.validadores import (
    cep_valido, converter_data, cpf_valido, formatar_cep, formatar_cpf,
)

log = logging.getLogger(__name__)

CAMPOS = ("nome", "cpf", "endereco", "cep", "data_emissao")

TIPOS_LOGRADOURO = r"(RUA|R\.|AVENIDA|AV\.?|TRAVESSA|TV\.|ESTRADA|RODOVIA|PRACA|ALAMEDA|LARGO|CONDOMINIO|VIA)\s"
PADRAO_DATA = r"(\d{1,2}\s*[/\-.]\s*\d{1,2}\s*[/\-.]\s*\d{2,4}|\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4})"


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").upper()


def _valor_depois_do_rotulo(linhas: list[str], rotulos: str) -> str | None:
    """Procura 'Rótulo: valor' e devolve o valor (na mesma linha ou na seguinte)."""
    padrao = re.compile(rf"\b({rotulos})\b\s*[:\-]?\s*(.*)", re.IGNORECASE)
    for i, linha in enumerate(linhas):
        m = padrao.search(_sem_acento(linha))
        if m:
            inicio = len(linha) - len(m.group(2))
            valor = linha[inicio:].strip(" :-\t")
            if not valor and i + 1 < len(linhas):
                valor = linhas[i + 1].strip()
            if valor:
                return valor
    return None


# ---------------- Extração por padrões ----------------
def _extrair_nome(linhas):
    valor = _valor_depois_do_rotulo(linhas, r"NOME|CLIENTE|TITULAR|DESTINATARIO|CONSUMIDOR")
    if not valor:
        return None
    valor = re.split(r"\s{2,}|\bCPF\b|\bCNPJ\b", valor, flags=re.IGNORECASE)[0]
    valor = re.sub(r"[^A-Za-zÀ-ÿ' ]", "", valor).strip()
    return valor.title() if len(valor.split()) >= 2 else None


def _extrair_endereco(linhas):
    valor = _valor_depois_do_rotulo(linhas, r"ENDERECO|END\.|LOGRADOURO")
    if not valor:
        for linha in linhas:
            if re.match(TIPOS_LOGRADOURO, _sem_acento(linha.strip())):
                valor = linha.strip()
                break
    if not valor:
        return None
    valor = re.split(r"\bCEP\b", valor, flags=re.IGNORECASE)[0].strip(" ,-")
    return valor if len(valor) >= 5 else None


def _extrair_cep(texto):
    m = re.search(r"CEP\s*[:\-]?\s*(\d{2}\.?\d{3}\s?-?\s?\d{3})", _sem_acento(texto))
    if not m:
        m = re.search(r"(?<![\d.])(\d{5}-\d{3})(?![\d-])", texto)
    return formatar_cep(m.group(1)) if m and cep_valido(m.group(1)) else None


def _extrair_cpf(texto):
    candidatos = re.findall(r"(?<!\d)(\d{3}\.?\d{3}\.?\d{3}-?\d{2})(?!\d)", texto)
    for c in candidatos:
        if cpf_valido(c):
            return formatar_cpf(c)
    # CPF encontrado mas com dígitos inválidos: devolvemos para a regra reprovar
    m = re.search(r"CPF\s*[:\-]?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})", _sem_acento(texto))
    return formatar_cpf(m.group(1)) if m else None


def _extrair_data_emissao(linhas, texto, hoje: date):
    rotulo = _valor_depois_do_rotulo(linhas, r"DATA DE EMISSAO|DATA DA EMISSAO|EMISSAO|EMITIDO EM|EMITIDA EM|DATA DO DOCUMENTO")
    if rotulo:
        m = re.search(PADRAO_DATA, rotulo, re.IGNORECASE)
        if m and converter_data(m.group(1)):
            return converter_data(m.group(1))
    # Sem rótulo: usa a data mais recente que não esteja no futuro
    datas = [converter_data(d) for d in re.findall(PADRAO_DATA, texto, re.IGNORECASE)]
    datas = [d for d in datas if d and d <= hoje]
    return max(datas) if datas else None


def extrair_por_padroes(texto: str, hoje: date | None = None) -> dict:
    hoje = hoje or date.today()
    linhas = [l for l in texto.splitlines() if l.strip()]
    data = _extrair_data_emissao(linhas, texto, hoje)
    return {
        "nome": _extrair_nome(linhas),
        "cpf": _extrair_cpf(texto),
        "endereco": _extrair_endereco(linhas),
        "cep": _extrair_cep(texto),
        "data_emissao": data.isoformat() if data else None,
    }


# ---------------- Extração com modelo de IA ----------------
PROMPT = """Você recebe o texto extraído por OCR de um COMPROVANTE DE RESIDÊNCIA brasileiro
(conta de luz, água, telefone, internet etc.). Extraia os campos abaixo e responda
APENAS com um JSON válido, sem comentários:

{"nome": "nome completo do titular", "cpf": "000.000.000-00", "endereco": "logradouro, número, complemento, bairro e cidade",
 "cep": "00000-000", "data_emissao": "AAAA-MM-DD"}

Regras: use null para qualquer campo que não esteja no texto. Não invente dados.
"data_emissao" é a data de emissão do documento (não use vencimento nem leitura).

Texto do OCR:
\"\"\"
{texto}
\"\"\""""


def ia_configurada() -> bool:
    return bool(config.IA_API_KEY and config.IA_MODELO)


def _limpar_resposta_ia(bruto: dict) -> dict:
    """Confere o que a IA devolveu: só aceita valores com formato correto."""
    limpo = {campo: None for campo in CAMPOS}
    nome = (bruto.get("nome") or "").strip()
    if len(nome.split()) >= 2:
        limpo["nome"] = nome.title()
    endereco = (bruto.get("endereco") or "").strip()
    if len(endereco) >= 5:
        limpo["endereco"] = endereco
    if bruto.get("cpf") and len(re.sub(r"\D", "", bruto["cpf"])) == 11:
        limpo["cpf"] = formatar_cpf(bruto["cpf"])
    if bruto.get("cep") and cep_valido(bruto["cep"]):
        limpo["cep"] = formatar_cep(bruto["cep"])
    data = converter_data(str(bruto.get("data_emissao") or ""))
    if data:
        limpo["data_emissao"] = data.isoformat()
    return limpo


def extrair_com_ia(texto: str) -> dict:
    from openai import OpenAI

    cliente = OpenAI(api_key=config.IA_API_KEY, base_url=config.IA_BASE_URL, timeout=60)
    resposta = cliente.chat.completions.create(
        model=config.IA_MODELO,
        messages=[{"role": "user", "content": PROMPT.replace("{texto}", texto[:8000])}],
    )
    conteudo = resposta.choices[0].message.content or ""
    json_texto = re.search(r"\{.*\}", conteudo, re.DOTALL)
    if not json_texto:
        raise ValueError("A IA não devolveu um JSON.")
    return _limpar_resposta_ia(json.loads(json_texto.group(0)))


# ---------------- Função principal ----------------
def extrair_dados(texto: str) -> tuple[dict, str]:
    """Devolve (dados, metodo). 'metodo' indica como os dados foram extraídos."""
    por_padroes = extrair_por_padroes(texto)
    if not ia_configurada():
        return por_padroes, "padrões (IA não configurada)"
    try:
        da_ia = extrair_com_ia(texto)
    except Exception as erro:  # sem internet, chave errada, limite atingido...
        log.warning("Falha na IA, usando extração por padrões: %s", erro)
        return por_padroes, "padrões (IA indisponível)"
    # A IA tem prioridade; o que ela não achou, completamos com os padrões
    combinado = {campo: da_ia.get(campo) or por_padroes.get(campo) for campo in CAMPOS}
    return combinado, f"IA ({config.IA_MODELO})"
