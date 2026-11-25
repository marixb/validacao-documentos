from datetime import date

from app.regras import APROVADO, REPROVADO, aplicar_regras

HOJE = date(2026, 11, 25)
TEXTO = "texto suficiente para ser considerado um documento legível pelo sistema"
DADOS_OK = {
    "nome": "Maria Da Silva", "cpf": "529.982.247-25", "endereco": "Rua das Flores, 123",
    "cep": "50050-000", "data_emissao": "2026-11-10",
}


def falhas(regras):
    return {r["codigo"] for r in regras if not r["ok"]}


def test_documento_completo_e_aprovado():
    status, regras = aplicar_regras(DADOS_OK, TEXTO, 92, hoje=HOJE)
    assert status == APROVADO
    assert falhas(regras) == set()


def test_emissao_com_mais_de_90_dias_reprova():
    status, regras = aplicar_regras({**DADOS_OK, "data_emissao": "2026-08-01"}, TEXTO, 92, hoje=HOJE)
    assert status == REPROVADO
    assert falhas(regras) == {"EMISSAO"}


def test_emissao_com_exatamente_90_dias_aprova():
    status, _ = aplicar_regras({**DADOS_OK, "data_emissao": "2026-08-27"}, TEXTO, 92, hoje=HOJE)
    assert status == APROVADO


def test_emissao_no_futuro_reprova():
    status, regras = aplicar_regras({**DADOS_OK, "data_emissao": "2026-12-25"}, TEXTO, 92, hoje=HOJE)
    assert status == REPROVADO and falhas(regras) == {"EMISSAO"}


def test_documento_ilegivel_reprova():
    status, regras = aplicar_regras(DADOS_OK, TEXTO, 35, hoje=HOJE)
    assert status == REPROVADO and "LEGIVEL" in falhas(regras)


def test_dados_ausentes_reprovam():
    vazio = {chave: None for chave in DADOS_OK}
    status, regras = aplicar_regras(vazio, TEXTO, 92, hoje=HOJE)
    assert status == REPROVADO
    assert falhas(regras) == {"NOME", "ENDERECO", "CEP", "EMISSAO"}


def test_sem_cpf_nao_reprova():
    status, _ = aplicar_regras({**DADOS_OK, "cpf": None}, TEXTO, 92, hoje=HOJE)
    assert status == APROVADO


def test_cpf_invalido_reprova():
    status, regras = aplicar_regras({**DADOS_OK, "cpf": "123.456.789-00"}, TEXTO, 92, hoje=HOJE)
    assert status == REPROVADO and falhas(regras) == {"CPF"}
