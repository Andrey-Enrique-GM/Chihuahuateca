from datetime import datetime
from pymysql.cursors import DictCursor
from enums.notificacion_type import TipoNotificacion
from persistence.db import get_connection



class Notificacion:
    @staticmethod
    def _obtener_columnas():
        try:
            conexion = get_connection()
            cursor = conexion.cursor()
            cursor.execute("SHOW COLUMNS FROM notificaciones")
            columnas = [fila[0] for fila in cursor.fetchall()]
            cursor.close(); conexion.close()
            return set(columnas)
        except Exception:
            return set()

    @staticmethod
    def asegurar_estructura():
        try:
            columnas = Notificacion._obtener_columnas()
            if not columnas:
                return False

            conexion = get_connection()
            cursor = conexion.cursor()
            if 'referencia_id' not in columnas:
                cursor.execute("ALTER TABLE notificaciones ADD COLUMN referencia_id INT NULL")
            if 'titulo_referencia' not in columnas:
                cursor.execute("ALTER TABLE notificaciones ADD COLUMN titulo_referencia VARCHAR(200) NULL")
            conexion.commit()
            cursor.close(); conexion.close()
            return True
        except Exception as exc:
            print(f"No fue necesario migrar la estructura de notificaciones: {exc}")
            return False

    @staticmethod
    def crear(usuario_id, emisor_id=None, tipo=None, referencia_id=None, titulo_referencia=None, mensaje=None):
        if not usuario_id or not tipo:
            return False

        columnas = Notificacion._obtener_columnas()
        try:
            conexion = get_connection()
            cursor = conexion.cursor()
            mensaje_final = mensaje or TipoNotificacion.construir_mensaje(tipo, emisor_username=None, titulo=titulo_referencia)
            ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if 'referencia_id' in columnas and 'titulo_referencia' in columnas:
                cursor.execute(
                    """
                    INSERT INTO notificaciones (usuario_id, emisor_id, tipo, referencia_id, titulo_referencia, mensaje, leido, fecha)
                    VALUES (%s, %s, %s, %s, %s, %s, FALSE, %s)
                    """,
                    (usuario_id, emisor_id, int(tipo), referencia_id, titulo_referencia, mensaje_final, ahora)
                )
            elif 'referencia_id' in columnas:
                cursor.execute(
                    """
                    INSERT INTO notificaciones (usuario_id, emisor_id, tipo, referencia_id, mensaje, leido, fecha)
                    VALUES (%s, %s, %s, %s, %s, FALSE, %s)
                    """,
                    (usuario_id, emisor_id, int(tipo), referencia_id, mensaje_final, ahora)
                )
            elif 'titulo_referencia' in columnas:
                cursor.execute(
                    """
                    INSERT INTO notificaciones (usuario_id, emisor_id, tipo, titulo_referencia, mensaje, leido, fecha)
                    VALUES (%s, %s, %s, %s, %s, FALSE, %s)
                    """,
                    (usuario_id, emisor_id, int(tipo), titulo_referencia, mensaje_final, ahora)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO notificaciones (usuario_id, emisor_id, tipo, mensaje, leido, fecha)
                    VALUES (%s, %s, %s, %s, FALSE, %s)
                    """,
                    (usuario_id, emisor_id, int(tipo), mensaje_final, ahora)
                )
            conexion.commit()
            cursor.close(); conexion.close()
            return True
        except Exception as exc:
            print(f"Error al guardar notificación: {exc}")
            return False


    @staticmethod
    def listar_para_usuario(usuario_id, limite=20):
        if not usuario_id:
            return []

        columnas = Notificacion._obtener_columnas()
        select_campos = "n.id, n.usuario_id, n.emisor_id, n.tipo, n.mensaje, n.leido, n.fecha"
        if 'referencia_id' in columnas:
            select_campos += ", n.referencia_id"
        if 'titulo_referencia' in columnas:
            select_campos += ", n.titulo_referencia"

        try:
            conexion = get_connection()
            cursor = conexion.cursor(DictCursor)
            cursor.execute(
                f"""
                SELECT {select_campos},
                       u.username AS emisor_username, u.nombre AS emisor_nombre
                FROM notificaciones n
                LEFT JOIN usuarios u ON u.id = n.emisor_id
                WHERE n.usuario_id = %s
                ORDER BY n.fecha DESC, n.id DESC
                LIMIT %s
                """,
                (usuario_id, limite)
            )
            resultados = cursor.fetchall()
            cursor.close(); conexion.close()
            return resultados
        except Exception as exc:
            print(f"Error al obtener notificaciones: {exc}")
            return []


    @staticmethod
    def contador_no_leidas(usuario_id):
        if not usuario_id:
            return 0

        try:
            conexion = get_connection()
            cursor = conexion.cursor(DictCursor)
            cursor.execute(
                "SELECT COUNT(*) AS total FROM notificaciones WHERE usuario_id = %s AND leido = FALSE",
                (usuario_id,)
            )
            fila = cursor.fetchone()
            cursor.close(); conexion.close()
            return int(fila.get('total', 0) if fila else 0)
        except Exception as exc:
            print(f"Error al contar notificaciones no leídas: {exc}")
            return 0


    @staticmethod
    def marcar_leidas(usuario_id, notificacion_id=None):
        if not usuario_id:
            return False

        try:
            conexion = get_connection()
            cursor = conexion.cursor()
            if notificacion_id:
                cursor.execute(
                    "UPDATE notificaciones SET leido = TRUE WHERE usuario_id = %s AND id = %s",
                    (usuario_id, notificacion_id)
                )
            else:
                cursor.execute(
                    "UPDATE notificaciones SET leido = TRUE WHERE usuario_id = %s",
                    (usuario_id,)
                )
            conexion.commit()
            cursor.close(); conexion.close()
            return True
        except Exception as exc:
            print(f"Error al marcar notificaciones como leídas: {exc}")
            return False


    @staticmethod
    def crear_desde_evento(usuario_id, emisor_id, tipo, referencia_id=None, titulo_referencia=None, emisor_username=None):
        if not usuario_id or not emisor_id or not tipo:
            return False

        mensaje = TipoNotificacion.construir_mensaje(
            tipo,
            emisor_username=emisor_username or 'Alguien',
            titulo=titulo_referencia
        )
        return Notificacion.crear(
            usuario_id=usuario_id,
            emisor_id=emisor_id,
            tipo=tipo,
            referencia_id=referencia_id,
            titulo_referencia=titulo_referencia,
            mensaje=mensaje,
        )
