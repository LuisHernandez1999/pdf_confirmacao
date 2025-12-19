from datetime import date, datetime

def normalizar_data(valor):
    if valor is None:
        return None
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        return datetime.fromisoformat(valor).date()
    return None