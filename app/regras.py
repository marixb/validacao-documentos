"""Regras de negócio do comprovante de residência e decisão Aprovado / Reprovado."""
from datetime import date

from app import config
from app.validadores import cpf_valido

APROVADO = "APROVADO"
REPROVADO = "REPROVADO"


def _regra(codigo: str, descricao: str, ok: bool, mensagem: str, obrigatoria: bool = True) -> dict:
    return {"codigo": codigo, "descricao": descricao, "ok": ok, "mensagem": mensagem, "obrigatoria": obrigatoria}


def aplicar_regras(dados: dict, texto: str, confianca: float, hoje: date | None = None) -> tuple[str, list[dict]]:
    hoje = hoje or date.today()
    regras = []

    # 1. Documento legível
    legivel = confianca >= config.CONFIANCA_MINIMA_OCR and len(texto.strip()) >= 30
    regras.append(_regra(
        "LEGIVEL", "Documento legível", legivel,
        f"Qualidade da leitura: {confianca:.0f}%." if legivel
        else f"Leitura ruim ({confianca:.0f}%, mínimo {config.CONFIANCA_MINIMA_OCR:.0f}%). Envie uma imagem mais nítida.",
    ))

    # 2. Nome identificado
    regras.append(_regra(
        "NOME", "Nome identificado", bool(dados.get("nome")),
        f"Titular: {dados['nome']}." if dados.get("nome") else "Nome do titular não encontrado.",
    ))

    # 3. Endereço identificado
    regras.append(_regra(
        "ENDERECO", "Endereço identificado", bool(dados.get("endereco")),
        "Endereço encontrado." if dados.get("endereco") else "Endereço não encontrado.",
    ))

    # 4. CEP identificado
    regras.append(_regra(
        "CEP", "CEP identificado", bool(dados.get("cep")),
        f"CEP {dados['cep']}." if dados.get("cep") else "CEP não encontrado.",
    ))

    # 5. Emissão em até 90 dias
    if not dados.get("data_emissao"):
        regras.append(_regra("EMISSAO", f"Emissão em até {config.PRAZO_MAXIMO_DIAS} dias", False,
                             "Data de emissão não encontrada."))
    else:
        emissao = date.fromisoformat(dados["data_emissao"])
        dias = (hoje - emissao).days
        if dias < 0:
            ok, msg = False, "A data de emissão está no futuro."
        elif dias > config.PRAZO_MAXIMO_DIAS:
            ok, msg = False, f"Emitido há {dias} dias (máximo {config.PRAZO_MAXIMO_DIAS})."
        else:
            ok, msg = True, f"Emitido há {dias} dia{'s' if dias != 1 else ''}."
        regras.append(_regra("EMISSAO", f"Emissão em até {config.PRAZO_MAXIMO_DIAS} dias", ok, msg))

    # 6. CPF válido (muitos comprovantes não trazem CPF, então só reprova se estiver errado)
    if not dados.get("cpf"):
        regras.append(_regra("CPF", "CPF válido", True, "CPF não consta no documento (opcional).", obrigatoria=False))
    else:
        valido = cpf_valido(dados["cpf"])
        regras.append(_regra("CPF", "CPF válido", valido,
                             "CPF válido." if valido else "CPF com dígitos verificadores inválidos."))

    status = APROVADO if all(r["ok"] for r in regras) else REPROVADO
    return status, regras
