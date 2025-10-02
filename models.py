from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class AnaliseContrato(Base):
    __tablename__ = 'analises_contratos'

    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String, index=True)
    score_risco = Column(Integer)
    resumo_riscos = Column(JSON)
    analise_completa_ia = Column(String)
    data_analise = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Análise(id={self.id}, arquivo='{self.nome_arquivo}')>"