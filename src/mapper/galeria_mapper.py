from datetime import date
from sqlalchemy.orm import Session
from src.domain.models import confirmacao_servico, imagem_confirmacao

##### endpoint pra possivel galeria de imagens 
def galeria_de_imagens(
    db: Session,
    tipo_servico: str | None = None,
    data_inicial: date | None = None,
    data_final: date | None = None,
):
    query = (
        db.query(
            imagem_confirmacao.id.label("imagem_id"),
            confirmacao_servico.data_servico,
            confirmacao_servico.tipo_servico,
        )
        .join(
            confirmacao_servico,
            confirmacao_servico.id == imagem_confirmacao.confirmacao_id
        )
    )
    if data_inicial:
        query = query.filter(confirmacao_servico.data_servico >= data_inicial)

    if data_final:
        query = query.filter(confirmacao_servico.data_servico <= data_final)

    if tipo_servico:
        query = query.filter(confirmacao_servico.tipo_servico == tipo_servico)

    lista_imagens = []

    for c in query.all():
        lista_imagens.append({
            "imagem_id": c.imagem_id,
            "data_servico": c.data_servico,
            "tipo_servico": c.tipo_servico,
            "responsavel":c.vistoriador,
        })

    return lista_imagens
