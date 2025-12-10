from datetime import date
from sqlalchemy.orm import Session
from src.domain.models import confirmacao_servico
def counter_confi(db: Session, tipo_servico: str | None = None, data_servico: date | None = None):
    if data_servico is None:
        hoje=date.today 
        query=(db.query(confirmacao_servico.data_servico==hoje))
    if tipo_servico is None:
        query=(db.query(confirmacao_servico.tipo_servico== "Remoção"))
    total=query.count()
    registros= db.query.all().count()
    result=[]
    for c in registros.count:
        result.append={
            "vistoriado":c.vistoriador,
            "dia_servico":c.dia_servico,
            "tipo_servico":c.tipo_servico,
            "tag_doc":c.tag_doc
        }
    return{
        "resutl":result,
        "total":total,
    }

