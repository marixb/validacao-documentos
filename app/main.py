"""API da Validação Inteligente de Documentos.

Fluxo: Upload -> OCR -> IA -> Validação -> Banco -> Consulta do resultado
"""
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config, ia, ocr
from app.banco import Documento, criar_tabelas, obter_sessao
from app.docs_ptbr import pagina_docs
from app.regras import aplicar_regras

TIPOS_ACEITOS = (".pdf", ".png", ".jpg", ".jpeg")
PASTA_STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def ao_iniciar(app: FastAPI):
    criar_tabelas()
    config.PASTA_ARQUIVOS.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Validação Inteligente de Documentos",
    description=(
        "API que recebe comprovantes de residência (PDF ou imagem), extrai o texto com OCR, "
        "identifica as informações com IA, valida as regras de negócio e guarda o resultado."
    ),
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    lifespan=ao_iniciar,
    openapi_tags=[
        {"name": "Status", "description": "Verifica se a API está funcionando."},
        {"name": "Documentos", "description": "Envio, processamento e consulta de documentos."},
    ],
)
app.mount("/static", StaticFiles(directory=PASTA_STATIC), name="static")


# ---------- Modelos de resposta ----------
class DadosExtraidos(BaseModel):
    nome: str | None = Field(None, description="Nome do titular", examples=["Maria Da Silva"])
    cpf: str | None = Field(None, description="CPF do titular", examples=["529.982.247-25"])
    endereco: str | None = Field(None, description="Endereço", examples=["Rua das Flores, 123 - Recife/PE"])
    cep: str | None = Field(None, description="CEP", examples=["50000-000"])
    data_emissao: str | None = Field(None, description="Data de emissão (AAAA-MM-DD)", examples=["2026-11-10"])


class ResultadoRegra(BaseModel):
    codigo: str = Field(..., examples=["EMISSAO"])
    descricao: str = Field(..., examples=["Emissão em até 90 dias"])
    ok: bool = Field(..., description="Se a regra foi atendida")
    mensagem: str = Field(..., examples=["Emitido há 15 dias."])
    obrigatoria: bool = Field(..., description="Se a regra pode reprovar o documento")


class RespostaDocumento(BaseModel):
    id: int = Field(..., examples=[1])
    nome_arquivo: str = Field(..., examples=["comprovante.pdf"])
    criado_em: datetime
    status: str = Field(..., description="APROVADO ou REPROVADO", examples=["APROVADO"])
    paginas: int = Field(..., examples=[1])
    confianca_ocr: float = Field(..., description="Qualidade da leitura do OCR (0 a 100)", examples=[91.5])
    metodo_extracao: str = Field(..., description="Como os dados foram extraídos", examples=["IA (gemini-flash-latest)"])
    dados: DadosExtraidos
    regras: list[ResultadoRegra]
    texto_extraido: str = Field(..., description="Texto reconhecido pelo OCR")


class ItemHistorico(BaseModel):
    id: int = Field(..., examples=[1])
    nome_arquivo: str = Field(..., examples=["comprovante.pdf"])
    criado_em: datetime
    status: str = Field(..., examples=["REPROVADO"])
    nome: str | None = Field(None, examples=["Maria Da Silva"])


class RespostaStatus(BaseModel):
    status: str = Field(..., examples=["online"])
    versao_tesseract: str = Field(..., examples=["5.3.4"])
    ia: str = Field(..., description="Situação da IA", examples=["configurada"])


class RespostaErro(BaseModel):
    erro: str = Field(..., examples=["Documento não encontrado."])


# ---------- Erros em português ----------
@app.exception_handler(RequestValidationError)
async def erro_validacao(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"erro": "Dados inválidos na requisição. Verifique se o arquivo foi enviado."})


@app.exception_handler(HTTPException)
async def erro_http(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"erro": exc.detail})


def _para_resposta(doc: Documento) -> dict:
    return {
        "id": doc.id, "nome_arquivo": doc.nome_arquivo, "criado_em": doc.criado_em, "status": doc.status,
        "paginas": doc.paginas, "confianca_ocr": doc.confianca_ocr, "metodo_extracao": doc.metodo_extracao,
        "dados": doc.dados, "regras": doc.regras, "texto_extraido": doc.texto_extraido,
    }


# ---------- Páginas ----------
@app.get("/", include_in_schema=False)
def pagina_inicial():
    return FileResponse(PASTA_STATIC / "index.html")


@app.get("/docs", include_in_schema=False)
def documentacao():
    return pagina_docs(app.openapi_url, "Documentação - Validação Inteligente de Documentos")


# ---------- Endpoints ----------
@app.get("/status", tags=["Status"], summary="Verificar status da API", response_model=RespostaStatus,
         response_description="API funcionando")
def verificar_status():
    return {
        "status": "online",
        "versao_tesseract": ocr.versao_tesseract(),
        "ia": "configurada" if ia.ia_configurada() else "não configurada (usando padrões)",
    }


@app.post(
    "/documentos", tags=["Documentos"], summary="Enviar e validar documento",
    description="Envie um comprovante de residência em **PDF, PNG ou JPG**. O sistema faz o OCR, extrai os dados, "
                "aplica as regras de negócio, guarda o resultado e devolve **APROVADO** ou **REPROVADO**.",
    response_model=RespostaDocumento, status_code=201, response_description="Documento processado",
    responses={
        400: {"model": RespostaErro, "description": "Arquivo inválido"},
        422: {"model": RespostaErro, "description": "Nenhum arquivo foi enviado"},
        500: {"model": RespostaErro, "description": "Erro ao processar o documento"},
    },
)
async def enviar_documento(
    arquivo: UploadFile = File(..., description="Comprovante de residência em PDF ou imagem"),
    sessao: Session = Depends(obter_sessao),
):
    nome = arquivo.filename or "arquivo"
    if not nome.lower().endswith(TIPOS_ACEITOS):
        raise HTTPException(400, "Tipo de arquivo não suportado. Envie PDF, PNG ou JPG.")
    conteudo = await arquivo.read()
    if not conteudo:
        raise HTTPException(400, "O arquivo está vazio.")
    if len(conteudo) > config.TAMANHO_MAXIMO_MB * 1024 * 1024:
        raise HTTPException(400, f"Arquivo muito grande. O limite é {config.TAMANHO_MAXIMO_MB} MB.")

    # 1. OCR
    try:
        resultado_ocr = ocr.extrair_texto(conteudo, nome)
    except Exception:
        raise HTTPException(400, "Não foi possível ler o arquivo. Verifique se ele não está corrompido.")

    # 2. IA (extração dos dados)
    dados, metodo = ia.extrair_dados(resultado_ocr.texto)

    # 3. Regras de negócio e decisão
    status, regras = aplicar_regras(dados, resultado_ocr.texto, resultado_ocr.confianca)

    # 4. Guardar o arquivo e o resultado no banco
    caminho = config.PASTA_ARQUIVOS / f"{uuid4().hex}{Path(nome).suffix.lower()}"
    caminho.write_bytes(conteudo)
    doc = Documento(
        nome_arquivo=nome, caminho_arquivo=str(caminho), paginas=resultado_ocr.paginas,
        confianca_ocr=resultado_ocr.confianca, texto_extraido=resultado_ocr.texto,
        metodo_extracao=metodo, dados=dados, regras=regras, status=status,
    )
    sessao.add(doc)
    sessao.commit()
    sessao.refresh(doc)
    return _para_resposta(doc)


@app.get("/documentos", tags=["Documentos"], summary="Listar histórico",
         description="Lista os documentos processados, do mais recente para o mais antigo.",
         response_model=list[ItemHistorico], response_description="Histórico de documentos")
def listar_documentos(sessao: Session = Depends(obter_sessao)):
    docs = sessao.scalars(select(Documento).order_by(Documento.id.desc()).limit(100)).all()
    return [{"id": d.id, "nome_arquivo": d.nome_arquivo, "criado_em": d.criado_em,
             "status": d.status, "nome": (d.dados or {}).get("nome")} for d in docs]


@app.get("/documentos/{documento_id}", tags=["Documentos"], summary="Consultar resultado",
         description="Mostra o resultado completo de um documento: dados extraídos, regras e decisão.",
         response_model=RespostaDocumento, response_description="Resultado do documento",
         responses={404: {"model": RespostaErro, "description": "Documento não encontrado"}})
def consultar_documento(documento_id: int, sessao: Session = Depends(obter_sessao)):
    doc = sessao.get(Documento, documento_id)
    if not doc:
        raise HTTPException(404, "Documento não encontrado.")
    return _para_resposta(doc)


@app.get("/documentos/{documento_id}/arquivo", tags=["Documentos"], summary="Baixar arquivo original",
         response_description="Arquivo original enviado",
         responses={404: {"model": RespostaErro, "description": "Documento não encontrado"}})
def baixar_arquivo(documento_id: int, sessao: Session = Depends(obter_sessao)):
    doc = sessao.get(Documento, documento_id)
    if not doc or not Path(doc.caminho_arquivo).exists():
        raise HTTPException(404, "Documento não encontrado.")
    return FileResponse(doc.caminho_arquivo, filename=doc.nome_arquivo)
