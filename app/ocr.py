"""Etapa de OCR: transforma o arquivo (PDF ou imagem) em texto."""
import io
from dataclasses import dataclass

import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image, ImageOps


@dataclass
class ResultadoOCR:
    texto: str
    paginas: int
    confianca: float  # média de 0 a 100 da certeza do Tesseract


def _carregar_imagens(conteudo: bytes, nome_arquivo: str) -> list[Image.Image]:
    if nome_arquivo.lower().endswith(".pdf"):
        return convert_from_bytes(conteudo, dpi=300)
    return [Image.open(io.BytesIO(conteudo))]


def _preparar(imagem: Image.Image) -> Image.Image:
    """Pré-processamento simples que melhora a leitura do OCR."""
    imagem = ImageOps.exif_transpose(imagem)       # corrige fotos de celular giradas
    imagem = imagem.convert("L")                    # tons de cinza
    if imagem.width < 1500:                         # imagens pequenas: amplia
        fator = 1500 / imagem.width
        imagem = imagem.resize((int(imagem.width * fator), int(imagem.height * fator)), Image.LANCZOS)
    return ImageOps.autocontrast(imagem)


def extrair_texto(conteudo: bytes, nome_arquivo: str) -> ResultadoOCR:
    imagens = [_preparar(img) for img in _carregar_imagens(conteudo, nome_arquivo)]

    textos, confiancas = [], []
    for imagem in imagens:
        textos.append(pytesseract.image_to_string(imagem, lang="por"))
        dados = pytesseract.image_to_data(imagem, lang="por", output_type=pytesseract.Output.DICT)
        confiancas += [float(c) for c, p in zip(dados["conf"], dados["text"]) if float(c) >= 0 and p.strip()]

    confianca = round(sum(confiancas) / len(confiancas), 1) if confiancas else 0.0
    return ResultadoOCR(texto="\n".join(textos).strip(), paginas=len(imagens), confianca=confianca)


def versao_tesseract() -> str:
    return str(pytesseract.get_tesseract_version())
