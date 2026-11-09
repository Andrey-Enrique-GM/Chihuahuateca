from datetime import datetime
from pymysql.cursors import DictCursor
from enums.notification_type import NotificationType
from persistence.db import get_connection



"""
Clase Notificacion que representa las notificaciones en la base de datos y los métodos
para gestionar las notificaciones.
Cada metodo retorna un booleano para indicar el estado de la operacion o una lista de
notificaciones si aplica.
"""



class Notification:
    @staticmethod
    def _get_columns():
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SHOW COLUMNS FROM notificaciones")
            columns = [row[0] for row in cursor.fetchall()]
            cursor.close(); connection.close()
            return set(columns)
        except Exception:
            return set()


    @staticmethod
    def ensure_structure():
        try:
            columns = Notification._get_columns()
            if not columns:
                return False

            connection = get_connection()
            cursor = connection.cursor()
            if 'referencia_id' not in columns:
                cursor.execute("ALTER TABLE notificaciones ADD COLUMN referencia_id INT NULL")
            if 'titulo_referencia' not in columns:
                cursor.execute("ALTER TABLE notificaciones ADD COLUMN titulo_referencia VARCHAR(200) NULL")
            connection.commit()
            cursor.close(); connection.close()
            return True
        except Exception as exc:
            print(f"No fue necesario migrar la estructura de notificaciones: {exc}")
            return False


    @staticmethod
    def create(user_id, sender_id=None, notification_type=None, reference_id=None, reference_title=None, message=None):
        if not user_id or not notification_type:
            return False

        columns = Notification._get_columns()
        try:
            connection = get_connection()
            cursor = connection.cursor()
            final_message = message or NotificationType.build_message(notification_type, sender_username=None, title=reference_title)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if 'referencia_id' in columns and 'titulo_referencia' in columns:
                cursor.execute(
                    """
                    INSERT INTO notificaciones (usuario_id, emisor_id, tipo, referencia_id, titulo_referencia, mensaje, leido, fecha)
                    VALUES (%s, %s, %s, %s, %s, %s, FALSE, %s)
                    """,
                    (user_id, sender_id, int(notification_type), reference_id, reference_title, final_message, now)
                )
            elif 'referencia_id' in columns:
                cursor.execute(
                    """
                    INSERT INTO notificaciones (usuario_id, emisor_id, tipo, referencia_id, mensaje, leido, fecha)
                    VALUES (%s, %s, %s, %s, %s, FALSE, %s)
                    """,
                    (user_id, sender_id, int(notification_type), reference_id, final_message, now)
                )
            elif 'titulo_referencia' in columns:
                cursor.execute(
                    """
                    INSERT INTO notificaciones (usuario_id, emisor_id, tipo, titulo_referencia, mensaje, leido, fecha)
                    VALUES (%s, %s, %s, %s, %s, FALSE, %s)
                    """,
                    (user_id, sender_id, int(notification_type), reference_title, final_message, now)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO notificaciones (usuario_id, emisor_id, tipo, mensaje, leido, fecha)
                    VALUES (%s, %s, %s, %s, FALSE, %s)
                    """,
                    (user_id, sender_id, int(notification_type), final_message, now)
                )
            connection.commit()
            cursor.close(); connection.close()
            return True
        except Exception as exc:
            print(f"Error al guardar notificación: {exc}")
            return False


    @staticmethod
    def list_for_user(user_id, limit=20):
        if not user_id:
            return []

        columns = Notification._get_columns()
        select_fields = "n.id, n.usuario_id, n.emisor_id, n.tipo, n.mensaje, n.leido, n.fecha"
        if 'referencia_id' in columns:
            select_fields += ", n.referencia_id"
        if 'titulo_referencia' in columns:
            select_fields += ", n.titulo_referencia"

        try:
            connection = get_connection()
            cursor = connection.cursor(DictCursor)
            cursor.execute(
                f"""
                SELECT {select_fields},
                       u.username AS emisor_username, u.nombre AS emisor_nombre
                FROM notificaciones n
                LEFT JOIN usuarios u ON u.id = n.emisor_id
                WHERE n.usuario_id = %s
                ORDER BY n.fecha DESC, n.id DESC
                LIMIT %s
                """,
                (user_id, limit)
            )
            results = cursor.fetchall()
            cursor.close(); connection.close()
            return results
        except Exception as exc:
            print(f"Error al obtener notificaciones: {exc}")
            return []


    @staticmethod
    def unread_count(user_id):
        if not user_id:
            return 0

        try:
            connection = get_connection()
            cursor = connection.cursor(DictCursor)
            cursor.execute(
                "SELECT COUNT(*) AS total FROM notificaciones WHERE usuario_id = %s AND leido = FALSE",
                (user_id,)
            )
            row = cursor.fetchone()
            cursor.close(); connection.close()
            return int(row.get('total', 0) if row else 0)
        except Exception as exc:
            print(f"Error al contar notificaciones no leídas: {exc}")
            return 0


    @staticmethod
    def mark_as_read(user_id, notification_id=None):
        if not user_id:
            return False

        try:
            connection = get_connection()
            cursor = connection.cursor()
            if notification_id:
                cursor.execute(
                    "UPDATE notificaciones SET leido = TRUE WHERE usuario_id = %s AND id = %s",
                    (user_id, notification_id)
                )
            else:
                cursor.execute(
                    "UPDATE notificaciones SET leido = TRUE WHERE usuario_id = %s",
                    (user_id,)
                )
            connection.commit()
            cursor.close(); connection.close()
            return True
        except Exception as exc:
            print(f"Error al marcar notificaciones como leídas: {exc}")
            return False


    @staticmethod
    def create_from_event(user_id, sender_id, notification_type, reference_id=None, reference_title=None, sender_username=None):
        if not user_id or not sender_id or not notification_type:
            return False

        message = NotificationType.build_message(
            notification_type,
            sender_username=sender_username or 'Alguien',
            title=reference_title
        )
        return Notification.create(
            user_id=user_id,
            sender_id=sender_id,
            notification_type=notification_type,
            reference_id=reference_id,
            reference_title=reference_title,
            message=message,
        )
