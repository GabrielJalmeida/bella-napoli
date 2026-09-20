from datetime import datetime, time
from zoneinfo import ZoneInfo


STORE_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def is_store_open(
    current_datetime: datetime,
    is_closed: bool,
    open_time: time | None,
    close_time: time | None,
) -> bool:
    """
    Determina se a loja está aberta em um determinado instante.

    O horário é interpretado no fuso America/Sao_Paulo.

    Para horários normais:
        18:00 -> 23:00
        aberto a partir de 18:00
        fechado a partir de 23:00

    Para fechamento à meia-noite:
        18:00 -> 00:00
        00:00 representa o fim do período daquele dia.
    """

    if current_datetime.tzinfo is None:
        raise ValueError(
            "A data e hora precisam possuir timezone."
        )

    if is_closed:
        return False

    if open_time is None or close_time is None:
        raise ValueError(
            "Loja aberta precisa possuir horário de abertura e fechamento."
        )

    local_datetime = current_datetime.astimezone(STORE_TIMEZONE)
    current_time = local_datetime.time()

    if close_time == time(0, 0):
        return current_time >= open_time

    return (
        current_time >= open_time
        and current_time < close_time
    )