from sqlalchemy.orm import Session
from domain.models.relatorio_confirmacao import RelatorioConfirmacao

class RelatorioRepository:

    @staticmethod
    def create(db: Session, relatorio: RelatorioConfirmacao):
        db.add(relatorio)
        db.commit()
        db.refresh(relatorio)
        return relatorio
