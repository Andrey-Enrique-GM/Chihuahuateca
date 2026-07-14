from datetime import datetime
from entities.usuario import User
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

    def __init__(self, id: int, date: datetime, user: User, description: str, type: LogType):
        self.id = id
        self.date = date
        self.user = user
        self.description = description
        self.type = type


    # Metodo para guardar un nuevo log en la base de datos
    def save_log(user: User, description: str, type: LogType):
        try:
            connection = get_connection()
            cursor = connection.cursor()

            sql = "INSERT INTO log (date, id_user, description, type) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (datetime.now(), user.id, description, type.value))
            connection.commit()

            cursor.close()
            connection.close()
        # Print del error por si falla la conexion a la base de datos o la consulta SQL
        except Exception as e:
            print(f"Error al guardar el log: {e}")
            return False
        

    