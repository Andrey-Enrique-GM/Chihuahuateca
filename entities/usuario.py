from pymysql.cursors import DictCursor
from werkzeug.security import check_password_hash, generate_password_hash
from persistence.db import get_connection



"""
Clase Usuario que representa cada registro de la tabla 'usuarios' y contiene metodos
estaticos para interactuar con la base de datos.
Cada metodo estatico se encarga de una operacion CRUD especifica
(Crear, Leer, Actualizar, Eliminar) y utiliza funciones definidas en persistence/consultas_db.py
para mantener una separacion clara entre la logica de negocio y la capa de acceso a datos.
"""



class User:
    def __init__(self, id: int, username: str, nombre: str, password: str, rol: str = 'usuario'):
        self.id = id
        self.username = username
        self.nombre = nombre
        self.password = password
        self.rol = rol


    # Metodo estatico para autenticar el usuario
    @staticmethod
    def authenticate(username: str, password: str):
        try:
            conexion = get_connection()
            cursor = conexion.cursor(DictCursor)
            sql = "SELECT id, username, nombre, password, rol FROM usuarios WHERE username = %s"
            cursor.execute(sql, (username,))
            usuario = cursor.fetchone()

            cursor.close()
            conexion.close()

            if usuario and check_password_hash(usuario['password'], password):
                return User(
                    id=usuario['id'],
                    username=usuario['username'],
                    nombre=usuario['nombre'],
                    password=usuario['password'],
                    rol=usuario['rol']
                )
        except Exception as ex:
            print(f"Error al autenticar usuario: {ex}")

        return None


    # Metodo estatico para crear un nuevo usuario
    @staticmethod
    def create(nombre: str, username: str, password: str, rol: str = 'usuario'):
        if not nombre or not username or not password:
            return False, 'Todos los campos son obligatorios'

        password_encriptada = generate_password_hash(password)

        try:
            conexion = get_connection()
            cursor = conexion.cursor()
            sql = """
                INSERT INTO usuarios (username, nombre, password, rol)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (username, nombre, password_encriptada, rol))
            conexion.commit()

            cursor.close()
            conexion.close()
            return True, None
        except Exception as ex:
            mensaje = str(ex)
            if 'Duplicate entry' in mensaje or '1062' in mensaje or 'IntegrityError' in mensaje:
                return False, f"El nombre de usuario '{username}' ya está ocupado."

            print(f"Error al crear usuario: {ex}")
            return False, f"Error en el servidor: {ex}"
