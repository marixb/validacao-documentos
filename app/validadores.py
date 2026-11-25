"""Funções pequenas de validação, usadas pela extração e pelas regras."""
import re
from datetime import date

MESES = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}


def somente_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto or "")


def cpf_valido(cpf: str) -> bool:
    """Confere os dois dígitos verificadores do CPF."""
    numeros = somente_digitos(cpf)
    if len(numeros) != 11 or numeros == numeros[0] * 11:
        return False
    for posicao in (9, 10):
        soma = sum(int(numeros[i]) * (posicao + 1 - i) for i in range(posicao))
        digito = (soma * 10) % 11 % 10
        if digito != int(numeros[posicao]):
            return False
    return True


def formatar_cpf(cpf: str) -> str:
    n = somente_digitos(cpf)
    return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"


def cep_valido(cep: str) -> bool:
    return len(somente_digitos(cep)) == 8


def formatar_cep(cep: str) -> str:
    n = somente_digitos(cep)
    return f"{n[:5]}-{n[5:]}"


def converter_data(texto: str) -> date | None:
    """Aceita 10/11/2026, 10-11-26, 10.11.2026, 2026-11-10 e '10 de novembro de 2026'."""
    if not texto:
        return None
    texto = texto.strip().lower()

    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", texto)
    if m:
        ano, mes, dia = map(int, m.groups())
    else:
        m = re.search(r"(\d{1,2})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{2,4})", texto)
        if m:
            dia, mes, ano = map(int, m.groups())
        else:
            m = re.search(r"(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})", texto)
            if not m or m.group(2) not in MESES:
                return None
            dia, mes, ano = int(m.group(1)), MESES[m.group(2)], int(m.group(3))
    if ano < 100:
        ano += 2000
    try:
        return date(ano, mes, dia)
    except ValueError:
        return None
