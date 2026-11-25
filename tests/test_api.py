"""Testes da API de ponta a ponta (upload -> OCR -> IA -> regras -> banco -> consulta)."""
import io
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from app.main import app


def _fonte(tamanho):
    for caminho in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]:
        if Path(caminho).exists():
            return ImageFont.truetype(caminho, tamanho)
    pytest.skip("Nenhuma fonte TrueType instalada para gerar a imagem de teste.")


def comprovante(emissao: date, formato="PNG") -> bytes:
    img = Image.new("RGB", (1240, 700), "white")
    d = ImageDraw.Draw(img)
    linhas = ["CONTA DE ENERGIA ELETRICA", "Nome: Maria da Silva", "CPF: 529.982.247-25",
              "Endereco: Rua das Flores, 123 - Recife/PE", "CEP: 50050-000",
              f"Data de emissao: {emissao.strftime('%d/%m/%Y')}"]
    for i, linha in enumerate(linhas):
        d.text((60, 60 + i * 80), linha, font=_fonte(34), fill="black")
    saida = io.BytesIO()
    img.save(saida, formato)
    return saida.getvalue()


@pytest.fixture(scope="module")
def cliente():
    with TestClient(app) as c:
        yield c


def test_status(cliente):
    r = cliente.get("/status")
    assert r.status_code == 200 and r.json()["status"] == "online"


def test_paginas_abrem(cliente):
    assert cliente.get("/").status_code == 200
    assert cliente.get("/docs").status_code == 200


def test_documento_recente_e_aprovado_e_fica_salvo(cliente):
    r = cliente.post("/documentos", files={"arquivo": ("conta.png", comprovante(date.today() - timedelta(days=10)), "image/png")})
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["status"] == "APROVADO", doc["regras"]
    assert doc["dados"]["cep"] == "50050-000"

    consulta = cliente.get(f"/documentos/{doc['id']}")
    assert consulta.status_code == 200 and consulta.json()["status"] == "APROVADO"
    assert any(item["id"] == doc["id"] for item in cliente.get("/documentos").json())
    assert cliente.get(f"/documentos/{doc['id']}/arquivo").status_code == 200


def test_pdf_antigo_e_reprovado(cliente):
    pdf = comprovante(date.today() - timedelta(days=120), formato="PDF")
    r = cliente.post("/documentos", files={"arquivo": ("conta.pdf", pdf, "application/pdf")})
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["status"] == "REPROVADO"
    assert [regra["codigo"] for regra in doc["regras"] if not regra["ok"]] == ["EMISSAO"]


def test_tipo_de_arquivo_invalido(cliente):
    r = cliente.post("/documentos", files={"arquivo": ("notas.txt", b"ola", "text/plain")})
    assert r.status_code == 400 and "não suportado" in r.json()["erro"]


def test_arquivo_corrompido(cliente):
    r = cliente.post("/documentos", files={"arquivo": ("foto.png", b"isso nao e uma imagem", "image/png")})
    assert r.status_code == 400


def test_sem_arquivo(cliente):
    assert cliente.post("/documentos").status_code == 422


def test_documento_inexistente(cliente):
    r = cliente.get("/documentos/999999")
    assert r.status_code == 404 and r.json()["erro"] == "Documento não encontrado."
