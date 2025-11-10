from sqlalchemy.orm import Session
from domain.models.confirmacao_servico import ConfirmacaoServico
from domain.models.imagem_confirmacao import ImagemConfirmacao

class ConfirmacaoRepository:
    @staticmethod
    def get_confirmacao(db: Session, confirmacao_id: int):
        return db.query(ConfirmacaoServico).filter(ConfirmacaoServico.id == confirmacao_id).first()
    @staticmethod
    def get_imagens_confirmacao(db: Session, confirmacao_id: int):
        return db.query(ImagemConfirmacao).filter(ImagemConfirmacao.confirmacao_id == confirmacao_id).all()
