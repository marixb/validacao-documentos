from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, Field
from PIL import Image
from pdf2image import convert_from_bytes
import pytesseract
import io

# docs_url=None e redoc_url=None: desligamos as páginas padrão (em inglês)
# para servir a nossa versão traduzida em /docs.
app = FastAPI(
    title="Validação Inteligente de Documentos",
    description=(
        "API que recebe documentos digitais (PDF ou imagem), extrai o texto com OCR, "
        "identifica as informações com IA e valida as regras de negócio."
    ),
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_tags=[
        {"name": "Status", "description": "Verifica se a API está funcionando."},
        {"name": "Documentos", "description": "Envio e processamento de documentos."},
    ],
)

TIPOS_ACEITOS = (".pdf", ".png", ".jpg", ".jpeg")
PASTA_STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=PASTA_STATIC), name="static")


# ---------- Página inicial (frontend) ----------
@app.get("/", include_in_schema=False)
def pagina_inicial():
    return FileResponse(PASTA_STATIC / "index.html")


# ---------- Modelos ----------
class RespostaStatus(BaseModel):
    status: str = Field(..., description="Situação da API", examples=["online"])
    versao_tesseract: str = Field(..., description="Versão do motor de OCR instalado", examples=["5.3.4"])


class RespostaUpload(BaseModel):
    arquivo: str = Field(..., description="Nome do arquivo enviado", examples=["comprovante_residencia.pdf"])
    paginas: int = Field(..., description="Quantidade de páginas processadas", examples=[1])
    texto_extraido: str = Field(..., description="Texto reconhecido pelo OCR", examples=["CONTA DE ENERGIA - Nome: Maria da Silva - CEP: 50000-000"])


class RespostaErro(BaseModel):
    erro: str = Field(..., description="Mensagem explicando o erro", examples=["Tipo de arquivo não suportado. Envie PDF, PNG ou JPG."])


# ---------- Erros em português ----------
@app.exception_handler(RequestValidationError)
async def erro_validacao(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"erro": "Dados inválidos na requisição. Verifique se o arquivo foi enviado."},
    )


@app.exception_handler(HTTPException)
async def erro_http(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"erro": exc.detail})


# ---------- Endpoints ----------
@app.get(
    "/status",
    tags=["Status"],
    summary="Verificar status da API",
    description="Retorna se a API está online e a versão do Tesseract (OCR).",
    response_model=RespostaStatus,
    response_description="API funcionando",
)
def verificar_status():
    return {"status": "online", "versao_tesseract": str(pytesseract.get_tesseract_version())}


@app.post(
    "/upload",
    tags=["Documentos"],
    summary="Enviar documento",
    description="Envie um arquivo **PDF, PNG ou JPG**. O sistema extrai o texto usando OCR em português.",
    response_model=RespostaUpload,
    response_description="Documento processado com sucesso",
    responses={
        400: {"model": RespostaErro, "description": "Tipo de arquivo não suportado"},
        422: {"model": RespostaErro, "description": "Nenhum arquivo foi enviado"},
        500: {"model": RespostaErro, "description": "Erro ao processar o documento"},
    },
)
async def enviar_documento(
    arquivo: UploadFile = File(..., description="Documento em PDF ou imagem"),
):
    if not arquivo.filename.lower().endswith(TIPOS_ACEITOS):
        raise HTTPException(status_code=400, detail="Tipo de arquivo não suportado. Envie PDF, PNG ou JPG.")

    try:
        conteudo = await arquivo.read()
        if arquivo.filename.lower().endswith(".pdf"):
            imagens = convert_from_bytes(conteudo)
        else:
            imagens = [Image.open(io.BytesIO(conteudo))]
        texto = "\n".join(pytesseract.image_to_string(img, lang="por") for img in imagens)
    except Exception as erro:
        raise HTTPException(status_code=500, detail=f"Erro ao processar o documento: {erro}")

    return {"arquivo": arquivo.filename, "paginas": len(imagens), "texto_extraido": texto}


# ---------- Página /docs traduzida para pt-BR ----------
TRADUCAO_SWAGGER = """
<script>
const TRADUCOES = {
  "Try it out": "Experimentar",
  "Cancel": "Cancelar",
  "Execute": "Executar",
  "Clear": "Limpar",
  "Parameters": "Parâmetros",
  "No parameters": "Sem parâmetros",
  "Request body": "Corpo da requisição",
  "required": "obrigatório",
  "Responses": "Respostas",
  "Response": "Resposta",
  "Code": "Código",
  "Details": "Detalhes",
  "Description": "Descrição",
  "Media type": "Tipo de mídia",
  "Controls Accept header.": "Define o cabeçalho Accept.",
  "Example Value": "Exemplo",
  "Example": "Exemplo",
  "Schema": "Estrutura",
  "Schemas": "Estruturas",
  "Curl": "Comando cURL",
  "Request URL": "URL da requisição",
  "Server response": "Resposta do servidor",
  "Response body": "Corpo da resposta",
  "Response headers": "Cabeçalhos da resposta",
  "Download": "Baixar",
  "Loading...": "Carregando...",
  "Undocumented": "Não documentado",
  "Successful Response": "Resposta com sucesso",
  "Validation Error": "Erro de validação",
  "Failed to fetch.": "Falha ao conectar com a API.",
  "Possible Reasons:": "Possíveis motivos:",
  "Expand all": "Expandir tudo",
  "Collapse all": "Recolher tudo",
  "Copy to clipboard": "Copiar",
  "Name": "Nome",
  "Request content type": "Tipo de conteúdo da requisição",
  "Media Type": "Tipo de mídia",
  "Reset": "Restaurar",
  "Links": "Ligações",
  "No links": "Sem ligações",
  "Controls": "Define o valor do cabeçalho",
  "header.": "da requisição.",
  "string": "texto",
  "integer": "número inteiro",
  "number": "número",
  "boolean": "verdadeiro/falso",
  "array": "lista",
  "object": "objeto",
  "Servers": "Servidores",
  "Required field is not provided": "Campo obrigatório não preenchido",
  "Value must be a string": "O valor deve ser um texto",
  "Value must be a number": "O valor deve ser um número",
  "Filter by tag": "Filtrar por grupo",
};

function traduzir(raiz) {
  const caminhante = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT);
  let no;
  while ((no = caminhante.nextNode())) {
    const texto = no.nodeValue.trim();
    if (TRADUCOES[texto] && TRADUCOES[texto] !== texto) no.nodeValue = no.nodeValue.replace(texto, TRADUCOES[texto]);
  }
  raiz.querySelectorAll?.("[title], [placeholder], [aria-label]").forEach(el => {
    ["title", "placeholder", "aria-label"].forEach(attr => {
      const v = el.getAttribute(attr);
      if (v && TRADUCOES[v.trim()]) el.setAttribute(attr, TRADUCOES[v.trim()]);
    });
  });
}

// O botão "Choose File" é desenhado pelo navegador. Colocamos um botão
// em português por cima dele (o campo original continua funcionando).
function traduzirCampoArquivo(raiz) {
  raiz.querySelectorAll?.('input[type="file"]:not([data-ptbr])').forEach(input => {
    input.dataset.ptbr = "1";
    const caixa = input.parentElement;
    caixa.style.position = "relative";
    caixa.style.display = "inline-block";
    const rotulo = document.createElement("span");
    rotulo.className = "ptbr-arquivo";
    rotulo.innerHTML = '<span class="btn">Escolher arquivo</span> <span class="nome">Nenhum arquivo escolhido</span>';
    caixa.appendChild(rotulo);
    Object.assign(input.style, { position: "absolute", inset: "0", opacity: "0", cursor: "pointer", width: "100%" });
    input.addEventListener("change", () => {
      rotulo.querySelector(".nome").textContent =
        input.files.length ? input.files[0].name : "Nenhum arquivo escolhido";
    });
  });
}

document.documentElement.lang = "pt-BR";
// esconde o selo "OAS 3.1" e o link "/openapi.json" (termos técnicos em inglês)
const estilo = document.createElement("style");
estilo.textContent = `
  .version-stamp, .info .link { display: none !important; }
  .swagger-ui .parameter__name.required:after,
  .swagger-ui .opblock-section-request-body .required:after { content: "obrigatório" !important; }
  .ptbr-arquivo { display: inline-block; padding: 6px 4px; font-family: sans-serif; font-size: 13px; }
  .ptbr-arquivo .btn { padding: 3px 10px; border: 1px solid #888; border-radius: 4px; background: #f0f0f0; }
`;
document.head.appendChild(estilo);
new MutationObserver(() => { traduzir(document.body); traduzirCampoArquivo(document.body); })
  .observe(document.body, { childList: true, subtree: true, characterData: true });
traduzir(document.body);
traduzirCampoArquivo(document.body);
</script>
"""


@app.get("/docs", include_in_schema=False)
def documentacao():
    pagina = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="Documentação - Validação Inteligente de Documentos",
        swagger_ui_parameters={"defaultModelsExpandDepth": -1},  # esconde a seção "Schemas"
    )
    html = pagina.body.decode("utf-8").replace("</body>", TRADUCAO_SWAGGER + "</body>")
    return HTMLResponse(html)