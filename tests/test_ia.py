from datetime import date

from app import ia

TEXTO_OCR = """COMPANHIA ENERGETICA FICTICIA S.A.
CONTA DE ENERGIA ELETRICA
Nome: MARIA DA SILVA
CPF: 529.982.247-25
Endereço: Rua das Flores, 123 - Boa Vista - Recife/PE
CEP: 50050-000
Data de emissão: 10/11/2026
Vencimento: 30/11/2026
"""


def test_extrai_todos_os_campos():
    dados = ia.extrair_por_padroes(TEXTO_OCR, hoje=date(2026, 11, 25))
    assert dados == {
        "nome": "Maria Da Silva",
        "cpf": "529.982.247-25",
        "endereco": "Rua das Flores, 123 - Boa Vista - Recife/PE",
        "cep": "50050-000",
        "data_emissao": "2026-11-10",
    }


def test_usa_data_de_emissao_e_nao_vencimento():
    dados = ia.extrair_por_padroes(TEXTO_OCR, hoje=date(2026, 12, 5))
    assert dados["data_emissao"] == "2026-11-10"


def test_sem_rotulo_de_emissao_usa_data_mais_recente_passada():
    texto = "Leitura: 01/10/2026\nReferente a 15/10/2026\nVencimento: 20/12/2026"
    dados = ia.extrair_por_padroes(texto, hoje=date(2026, 11, 25))
    assert dados["data_emissao"] == "2026-10-15"


def test_texto_vazio_nao_encontra_nada():
    dados = ia.extrair_por_padroes("", hoje=date(2026, 11, 25))
    assert all(valor is None for valor in dados.values())


def test_sem_ia_configurada_usa_padroes():
    dados, metodo = ia.extrair_dados(TEXTO_OCR)
    assert metodo.startswith("padrões")
    assert dados["nome"] == "Maria Da Silva"


def test_ia_tem_prioridade_e_padroes_completam(monkeypatch):
    monkeypatch.setattr(ia.config, "IA_API_KEY", "chave-falsa")
    monkeypatch.setattr(ia.config, "IA_MODELO", "modelo-teste")
    monkeypatch.setattr(ia, "extrair_com_ia", lambda texto: {
        "nome": "Maria da Silva Santos", "cpf": None, "endereco": None, "cep": "50050-000", "data_emissao": "2026-11-10"})
    dados, metodo = ia.extrair_dados(TEXTO_OCR)
    assert metodo == "IA (modelo-teste)"
    assert dados["nome"] == "Maria da Silva Santos"      # veio da IA
    assert dados["cpf"] == "529.982.247-25"              # completado pelos padrões


def test_se_a_ia_falhar_usa_padroes(monkeypatch):
    monkeypatch.setattr(ia.config, "IA_API_KEY", "chave-falsa")
    monkeypatch.setattr(ia.config, "IA_MODELO", "modelo-teste")

    def falhar(texto):
        raise ConnectionError("sem internet")

    monkeypatch.setattr(ia, "extrair_com_ia", falhar)
    dados, metodo = ia.extrair_dados(TEXTO_OCR)
    assert metodo == "padrões (IA indisponível)"
    assert dados["cep"] == "50050-000"


def test_resposta_da_ia_e_conferida():
    limpo = ia._limpar_resposta_ia({"nome": "Ana", "cpf": "abc", "cep": "123", "data_emissao": "ontem", "endereco": "Rua A, 10"})
    assert limpo["nome"] is None          # só um nome: não aceita
    assert limpo["cpf"] is None
    assert limpo["cep"] is None
    assert limpo["data_emissao"] is None
    assert limpo["endereco"] == "Rua A, 10"


def test_gemini_usa_api_nativa(monkeypatch):
    """Chaves novas do Gemini (AQ.) precisam da API nativa do Google."""
    import httpx

    monkeypatch.setattr(ia.config, "IA_API_KEY", "AQ.chave-de-teste")
    monkeypatch.setattr(ia.config, "IA_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    monkeypatch.setattr(ia.config, "IA_MODELO", "gemini-flash-latest")
    chamada = {}

    class RespostaFalsa:
        def raise_for_status(self):
            pass

        def json(self):
            texto = '```json\n{"nome": "Maria da Silva", "cpf": null, "endereco": "Rua das Flores, 123", "cep": "50050000", "data_emissao": "2026-11-10"}\n```'
            return {"candidates": [{"content": {"parts": [{"text": texto}]}}]}

    def post_falso(url, headers, json, timeout):
        chamada.update(url=url, headers=headers)
        return RespostaFalsa()

    monkeypatch.setattr(httpx, "post", post_falso)
    dados, metodo = ia.extrair_dados(TEXTO_OCR)
    assert chamada["url"].endswith("/models/gemini-flash-latest:generateContent")
    assert chamada["headers"]["x-goog-api-key"] == "AQ.chave-de-teste"
    assert metodo == "IA (gemini-flash-latest)"
    assert dados["cep"] == "50050-000"
    assert dados["cpf"] == "529.982.247-25"   # a IA não achou; completado pelos padrões