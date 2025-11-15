# domain/service/service_gerar_relatorio.py

from fastapi import HTTPException
from sqlalchemy.orm import Session
from domain.models.relatorio_confirmacao import RelatorioConfirmacao

def gerar_relatorio(
    db: Session,
    confirmacao_tag: str,
    imagem_antes_id: int,
    imagem_depois_id: int,
    observacao: str = None
) -> RelatorioConfirmacao:

    # Verifica se já existe relatório para a confirmação
    relatorio_existente = db.query(RelatorioConfirmacao).filter(
        RelatorioConfirmacao.confirmacao_tag == confirmacao_tag
    ).first()
    if relatorio_existente:
        raise HTTPException(status_code=400, detail="Relatório já existe para esta confirmação.")

    if imagem_antes_id == imagem_depois_id:
        raise HTTPException(status_code=400, detail="Imagem 'antes' e 'depois' não podem ser iguais.")

    # Cria relatório
    relatorio = RelatorioConfirmacao(
        confirmacao_tag=confirmacao_tag,
        obs_antes=None,
        obs_depois=None,
        observacao=observacao
    )

    db.add(relatorio)
    db.commit()
    db.refresh(relatorio)

    return relatorio
