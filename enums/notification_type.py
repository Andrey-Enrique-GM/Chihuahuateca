from enum import IntEnum


class NotificationType(IntEnum):
    LIKE = 1
    FOLLOW = 2
    COMMENT = 3

    @property
    def label(self):
        return {
            NotificationType.LIKE: 'le gustó tu publicación',
            NotificationType.FOLLOW: 'comenzó a seguirte',
            NotificationType.COMMENT: 'comentó en tu reseña',
        }.get(self, 'te notificó')

    @staticmethod
    def build_message(notification_type, sender_username=None, title=None):
        notification_type = NotificationType(int(notification_type)) if isinstance(notification_type, int) else notification_type
        sender_username = sender_username or 'Alguien'

        if notification_type == NotificationType.LIKE:
            title_text = f" '{title}'" if title else ''
            return f"@{sender_username} le gustó tu publicación{title_text}."

        if notification_type == NotificationType.FOLLOW:
            return f"@{sender_username} comenzó a seguirte."

        if notification_type == NotificationType.COMMENT:
            title_text = f" de '{title}'" if title else ''
            return f"@{sender_username} comentó en tu reseña{title_text}."

        return f"@{sender_username} te envió una nueva notificación."
