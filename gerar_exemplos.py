"""Gera comprovantes de residência FICTÍCIOS para testar o sistema."""
from datetime import date, timedelta
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PASTA = Path(__file__).parent / "exemplos"
PASTA.mkdir(exist_ok=True)

def fonte(tamanho, negrito=False):
    nomes = ["DejaVuSans-Bold.ttf" if negrito else "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
    for pasta in ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation"]:
        for n in nomes:
            if Path(pasta, n).exists():
                return ImageFont.truetype(str(Path(pasta, n)), tamanho)
    return ImageFont.load_default()

def comprovante(nome_arquivo, emissao, nome="Maria da Silva", cpf="529.982.247-25", borrar=False):
    img = Image.new("RGB", (1240, 900), "white")
    d = ImageDraw.Draw(img)
    d.text((60, 50), "COMPANHIA ENERGETICA FICTICIA S.A.", font=fonte(38, True), fill="black")
    d.text((60, 105), "CONTA DE ENERGIA ELETRICA - DOCUMENTO DE TESTE", font=fonte(26), fill="black")
    d.line((60, 160, 1180, 160), fill="black", width=3)
    linhas = [
        f"Nome: {nome}",
        f"CPF: {cpf}",
        "Endereco: Rua das Flores, 123 - Boa Vista - Recife/PE",
        "CEP: 50050-000",
        f"Data de emissao: {emissao.strftime('%d/%m/%Y')}",
        f"Vencimento: {(emissao + timedelta(days=20)).strftime('%d/%m/%Y')}",
        "Consumo: 215 kWh      Valor total: R$ 187,40",
    ]
    for i, l in enumerate(linhas):
        d.text((60, 200 + i * 70), l, font=fonte(32), fill="black")
    if borrar:
        img = img.resize((300, 218)).filter(ImageFilter.GaussianBlur(3))
    img.save(PASTA / nome_arquivo)
    print("criado:", PASTA / nome_arquivo)

hoje = date.today()
comprovante("1_aprovado.png", hoje - timedelta(days=15))
comprovante("2_reprovado_emissao_antiga.png", hoje - timedelta(days=140))
comprovante("3_reprovado_cpf_invalido.png", hoje - timedelta(days=10), cpf="123.456.789-00")
comprovante("4_reprovado_ilegivel.png", hoje - timedelta(days=10), borrar=True)
