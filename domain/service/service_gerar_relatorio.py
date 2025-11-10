from sqlalchemy.orm import Session
from domain.models.confirmacao_servico import ConfirmacaoServico
from domain.models.imagem_confirmacao import ImagemConfirmacao
from domain.models.relatorio_confirmacao import RelatorioConfirmacao

def gerar_relatorio(db: Session, confirmacao_id: int, imagens_escolhidas: list[int]):
    confirmacao = db.query(ConfirmacaoServico).filter_by(id=confirmacao_id).first()
    if not confirmacao:
        raise Exception("ConfirmacaoServico não encontrada")

    imagens = db.query(ImagemConfirmacao).filter(
        ImagemConfirmacao.id.in_(imagens_escolhidas),
        ImagemConfirmacao.confirmacao_id == confirmacao_id
    ).all()

    campos_antes = [img.imagem for img in imagens]
    campos_depois = []  

    relatorio = RelatorioConfirmacao(
        tag_doc=confirmacao.tag_doc,
        nome_vistoriador=confirmacao.nome_vistoriador,
        campos_antes=campos_antes,
        campos_depois=campos_depois,
    )

    db.add(relatorio)
    db.commit()
    db.refresh(relatorio)
    return relatorio
