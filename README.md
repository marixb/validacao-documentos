# Validação Inteligente de Documentos

Solução que recebe **comprovantes de residência** (PDF ou imagem), lê o texto com **OCR**,
extrai as informações com **IA**, aplica **regras de negócio**, decide entre **APROVADO** ou
**REPROVADO**, guarda tudo em um **banco de dados** e permite **consultar** o resultado.

```
Upload → OCR → IA → Validação → Banco de dados → Consulta do resultado
```

---

## 1. Definições do projeto

| Item | Definição |
|---|---|
| **Problema** | A validação manual de comprovantes de residência gera atrasos, retrabalho e erros no cadastro de clientes. |
| **Usuário** | Analista de cadastro / backoffice. |
| **Documento** | Comprovante de residência (conta de luz, água, telefone, internet…). |
| **Dados extraídos** | Nome, CPF, endereço, CEP e data de emissão. |
| **Regras** | Documento legível · nome identificado · endereço identificado · CEP identificado · emissão em até 90 dias (e não no futuro) · CPF válido, quando presente. |
| **Aprovação** | Todos os dados obrigatórios extraídos e todas as regras atendidas. |
| **Rejeição** | Documento ilegível, dados ausentes, emissão com mais de 90 dias ou CPF inválido. |
| **Fluxo** | Upload → OCR → IA → Validação → Banco → Resultado. |
| **MVP** | Processar 1 tipo de documento (comprovante de residência) com validação e consulta do resultado. |

---

## 2. Tecnologias

| Tecnologia | Uso no projeto |
|---|---|
| **Python 3.12 + FastAPI** | Backend e API REST |
| **Tesseract OCR** (`pytesseract`, `pdf2image`, `Pillow`) | Transformar o documento em texto |
| **IA** (`openai`, compatível com Gemini, OpenAI, Ollama…) | Transformar o texto em dados estruturados |
| **Expressões regulares** | Extração sem IA (reserva) e conferência do que a IA devolve |
| **SQLite + SQLAlchemy** | Guardar documentos e resultados |
| **HTML, CSS e JavaScript** | Tela para o usuário |
| **pytest** | Testes automatizados |
| **Docker + Render** | Deploy (solução online) |
| **Git + GitHub** | Versionamento |

---

## 3. Estrutura

```
validacao-documentos/
├── app/
│   ├── main.py          # API: endpoints e fluxo completo
│   ├── ocr.py           # Etapa OCR (imagem/PDF → texto)
│   ├── ia.py            # Etapa IA (texto → dados)
│   ├── regras.py        # Regras de negócio e decisão
│   ├── validadores.py   # CPF, CEP e datas
│   ├── banco.py         # Banco de dados
│   ├── config.py        # Configurações (.env)
│   ├── docs_ptbr.py     # Página /docs em português
│   └── static/index.html  # Tela do usuário
├── tests/               # Testes automatizados
├── exemplos/            # Comprovantes FICTÍCIOS para testar
├── gerar_exemplos.py    # Gera os comprovantes de exemplo
├── Dockerfile           # Imagem para o deploy
├── render.yaml          # Configuração do Render
├── requirements.txt
└── .env.example         # Modelo do arquivo de configuração
```

---

## 4. Como rodar no computador (Linux)

```bash
sudo apt install -y tesseract-ocr tesseract-ocr-por poppler-utils
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # depois edite o .env se quiser usar IA
uvicorn app.main:app --reload
```

- Tela do usuário: http://127.0.0.1:8000
- Documentação da API: http://127.0.0.1:8000/docs

Para gerar comprovantes de teste: `python gerar_exemplos.py` (cria os arquivos na pasta `exemplos/`).

---

## 5. Endpoints da API

| Método | Endereço | O que faz |
|---|---|---|
| `GET` | `/status` | Situação da API, do OCR e da IA |
| `POST` | `/documentos` | Envia o arquivo, processa e devolve APROVADO/REPROVADO |
| `GET` | `/documentos` | Histórico de documentos |
| `GET` | `/documentos/{id}` | Resultado completo de um documento |
| `GET` | `/documentos/{id}/arquivo` | Arquivo original enviado |

---

## 6. IA

Sem configuração, o sistema extrai os dados por **padrões** (expressões regulares). Para usar
um modelo de IA, preencha no `.env`:

```
IA_API_KEY=sua_chave
IA_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
IA_MODELO=gemini-flash-latest
```

- A IA lê o texto do OCR e devolve um JSON com os campos.
- Todo valor devolvido pela IA é **conferido** (formato do CPF, CEP e data) antes de ser aceito.
- O que a IA não encontrar é completado pelos padrões.
- Se a IA falhar (sem internet, limite atingido), o sistema continua funcionando com os padrões.

---

## 7. Testes

```bash
pytest -v
```

Cobrem: validação de CPF/CEP/datas, extração dos dados, regras de negócio, decisão e a API de
ponta a ponta (upload de PNG e PDF, consulta, histórico e erros).

---

## 8. Deploy

O deploy usa **Docker** (necessário para instalar o Tesseract) no **Render**, que tem plano gratuito.

1. Envie o projeto para o GitHub (`git push`).
2. Crie uma conta em https://render.com entrando com o GitHub.
3. Clique em **New → Blueprint**, escolha o repositório `validacao-documentos` e confirme.
   O Render lê o arquivo `render.yaml` e cria o serviço sozinho.
4. Quando pedir `IA_API_KEY`, cole sua chave (ou deixe em branco para usar só os padrões).
5. Aguarde o build (alguns minutos). O endereço fica parecido com
   `https://validacao-documentos.onrender.com`.

**Limitações do plano gratuito:**
- O serviço "dorme" depois de 15 minutos sem acesso e leva cerca de 1 minuto para acordar.
  **Abra o link um pouco antes da apresentação.**
- Os arquivos e o banco SQLite são apagados quando o serviço reinicia. Para guardar os dados
  de forma permanente, use um banco PostgreSQL e informe o endereço em `DATABASE_URL`.
