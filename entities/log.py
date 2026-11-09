from datetime import datetime, timezone
from pymysql.cursors import DictCursor
from entities.user import User
from enums.log_type import LogType
from persistence.db import get_connection



"""
Clase Log que representa cada registro de la tabla 'log' y contiene metodos
estaticos para interactuar con la base de datos.
Cada metodo estatico se encarga de una operacion CRUD especifica
(Crear, Leer, Actualizar, Eliminar) y utiliza funciones definidas en persistence/consultas_db.py
para mantener una separacion clara entre la logica de negocio y la capa de acceso a datos.
"""



class Log:
    def __init__(self, id: int, timestamp: datetime, user: User, description: str, log_type: LogType, details: str = ''):
        self.id = id

        # Asegurar que la fecha tenga informacion de zona horaria UTC si viene sin ella
        if timestamp and timestamp.tzinfo is None:
            self.timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            self.timestamp = timestamp
        
        self.user = user
        self.description = description or ''
        self.log_type = log_type
        self.details = details or ''


    # ISO Format para que JavaScript lea la fecha con offset Z (UTC)
    @property
    def iso_date(self):
        return self.timestamp.isoformat() if self.timestamp else ''


    # Metodo para guardar un nuevo log en la base de datos
    @property
    def date_time(self):
        return self.timestamp.strftime('%d/%m/%Y %H:%M:%S') if self.timestamp else ''


    @property
    def action(self):
        return self.description or ''


    @staticmethod
    def save_log(user: User, description: str, log_type: LogType):
        try:
            connection = get_connection()
            cursor = connection.cursor()

            sql = "INSERT INTO `log` (fecha, id_user, descripcion, type) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (datetime.now(timezone.utc), user.id, description, log_type.value))
            connection.commit()

            cursor.close()
            connection.close()
            return True
        except Exception as e:
            print(f"Error al guardar el log: {e}")
            return False


    @staticmethod
    def get_by_user(user_id: int):
        if not user_id:
            return []

        try:
            connection = get_connection()
            cursor = connection.cursor(DictCursor)
            sql = """
                SELECT id, fecha, id_user, descripcion, type
                FROM `log`
                WHERE id_user = %s
                ORDER BY fecha DESC
                LIMIT 10
            """
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()

            cursor.close()
            connection.close()

            return [
                Log(
                    id=row['id'],
                    timestamp=row['fecha'],
                    user=User(id=row['id_user'], username='', name='', password='', role='USER'),
                    description=row['descripcion'],
                    log_type=(LogType(row['type']) if isinstance(row.get('type'), int) and row.get('type') in set(item.value for item in LogType) else LogType.EDIT),
                )
                for row in rows
            ]
        except Exception as e:
            print(f"Error al obtener logs del usuario: {e}")
            return []
