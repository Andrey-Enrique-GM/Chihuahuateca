from enum import IntEnum

class TipoNotificacion(IntEnum):
    LIKE = 1
    FOLLOW = 2
    COMMENT = 3


    @property
    def etiqueta(self):
        return {
            TipoNotificacion.LIKE: 'le gustó tu publicación',
            TipoNotificacion.FOLLOW: 'comenzó a seguirte',
            TipoNotificacion.COMMENT: 'comentó en tu reseña',
        }.get(self, 'te notificó')

    @staticmethod
    def construir_mensaje(tipo, emisor_username=None, titulo=None):
        tipo = TipoNotificacion(int(tipo)) if isinstance(tipo, int) else tipo
        emisor_username = emisor_username or 'Alguien'

        if tipo == TipoNotificacion.LIKE:
            titulo_texto = f" '{titulo}'" if titulo else ''
            return f"@{emisor_username} le gustó tu publicación{titulo_texto}."

        if tipo == TipoNotificacion.FOLLOW:
            return f"@{emisor_username} comenzó a seguirte."

        if tipo == TipoNotificacion.COMMENT:
            titulo_texto = f" de '{titulo}'" if titulo else ''
            return f"@{emisor_username} comentó en tu reseña{titulo_texto}."

        return f"@{emisor_username} te envió una nueva notificación."
