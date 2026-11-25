"""Página /docs (Swagger) traduzida para pt-BR."""
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

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


def pagina_docs(openapi_url: str, titulo: str) -> HTMLResponse:
    pagina = get_swagger_ui_html(
        openapi_url=openapi_url,
        title=titulo,
        swagger_ui_parameters={"defaultModelsExpandDepth": -1},  # esconde a seção "Schemas"
    )
    html = pagina.body.decode("utf-8").replace("</body>", TRADUCAO_SWAGGER + "</body>")
    return HTMLResponse(html)
