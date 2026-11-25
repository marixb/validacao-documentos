"""Banco de dados: guarda cada documento processado e o seu resultado."""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app import config

argumentos = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(config.DATABASE_URL, connect_args=argumentos)
SessaoLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


class Documento(Base):
    __tablename__ = "documentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome_arquivo: Mapped[str] = mapped_column(String(255))
    caminho_arquivo: Mapped[str] = mapped_column(String(500))
    tipo_documento: Mapped[str] = mapped_column(String(50), default="comprovante_residencia")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    paginas: Mapped[int] = mapped_column(Integer)
    confianca_ocr: Mapped[float] = mapped_column(Float)
    texto_extraido: Mapped[str] = mapped_column(Text)
    metodo_extracao: Mapped[str] = mapped_column(String(100))
    dados: Mapped[dict] = mapped_column(JSON)
    regras: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20))


def criar_tabelas():
    Base.metadata.create_all(engine)


def obter_sessao():
    """Usado pelo FastAPI: abre uma sessão por requisição e fecha no final."""
    sessao = SessaoLocal()
    try:
        yield sessao
    finally:
        sessao.close()
