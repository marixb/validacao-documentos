from datetime import date

from app.validadores import cep_valido, converter_data, cpf_valido


def test_cpf_valido():
    assert cpf_valido("529.982.247-25")
    assert cpf_valido("52998224725")


def test_cpf_invalido():
    assert not cpf_valido("123.456.789-00")
    assert not cpf_valido("111.111.111-11")
    assert not cpf_valido("123")


def test_cep():
    assert cep_valido("50050-000")
    assert not cep_valido("5005-000")


def test_converter_datas_em_varios_formatos():
    assert converter_data("10/11/2026") == date(2026, 11, 10)
    assert converter_data("10-11-26") == date(2026, 11, 10)
    assert converter_data("2026-11-10") == date(2026, 11, 10)
    assert converter_data("10 de novembro de 2026") == date(2026, 11, 10)
    assert converter_data("32/13/2026") is None
