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
    @staticmethod
    def normalize_role(role: str) -> str:
        value = (role or '').strip().upper()
        return value if value in {'USER', 'ADMIN'} else 'USER'

    def __init__(
        self,
        id: int,
        username: str,
        name: str = '',
        password: str = '',
        role: str = 'USER',
        timezone: str = 'AUTO',
        registration_date: str = '',
        is_following: bool = False
    ):
        self.id = id
        self.username = username
        self.name = name or ''
        self.password = password
        self.role = self.normalize_role(role)
        self.timezone = (timezone or 'AUTO').strip() or 'AUTO'
        self.registration_date = registration_date or ''
        self.is_following = is_following

    # Metodo estatico para autenticar el usuario
    @staticmethod
    def authenticate(username: str, password: str):
        try:
            connection = get_connection()
            cursor = connection.cursor(DictCursor)
            sql = "SELECT id, username, nombre, password, rol, zona_horaria FROM usuarios WHERE username = %s"
            cursor.execute(sql, (username,))
            user_data = cursor.fetchone()

            cursor.close()
            connection.close()

            if user_data and check_password_hash(user_data['password'], password):
                return User(
                    id=user_data['id'],
                    username=user_data['username'],
                    name=user_data['nombre'],
                    password=user_data['password'],
                    role=user_data['rol'],
                    timezone=user_data.get('zona_horaria', 'AUTO')
                )
        except Exception as ex:
            print(f"Error al autenticar usuario: {ex}")

        return None


    @staticmethod
    def get_by_id(user_id: int):
        if not user_id:
            return None

        try:
            connection = get_connection()
            cursor = connection.cursor(DictCursor)
            sql = "SELECT id, username, nombre, password, rol, zona_horaria FROM usuarios WHERE id = %s"
            cursor.execute(sql, (user_id,))
            user_data = cursor.fetchone()

            cursor.close()
            connection.close()

            if user_data:
                return User(
                    id=user_data['id'],
                    username=user_data['username'],
                    name=user_data['nombre'],
                    password=user_data['password'],
                    role=user_data['rol'],
                    timezone=user_data.get('zona_horaria', 'AUTO')
                )
        except Exception as ex:
            print(f"Error al obtener usuario por ID: {ex}")

        return None


    @staticmethod
    def get_all(current_user_id=None):
        try:
            connection = get_connection()
            cursor = connection.cursor(DictCursor)
            cursor.execute(
                """
                SELECT u.id, u.username, u.nombre, u.rol, u.fecha_registro, u.zona_horaria,
                       CASE WHEN s.id IS NULL THEN 0 ELSE 1 END AS usuario_sigue
                FROM usuarios u
                LEFT JOIN seguidores s
                    ON s.seguido_id = u.id AND s.seguidor_id = %s
                ORDER BY u.id ASC
                """,
                (current_user_id,)
            )
            rows = cursor.fetchall()
            cursor.close()
            connection.close()
            return [
                User(
                    id=row['id'],
                    username=row['username'],
                    name=row['nombre'],
                    password='',
                    role=row['rol'],
                    timezone=row.get('zona_horaria', 'AUTO'),
                    registration_date=str(row.get('fecha_registro', '')),
                    is_following=bool(row.get('usuario_sigue', 0))
                )
                for row in rows
            ]
        except Exception as ex:
            print(f"Error al obtener usuarios: {ex}")
            return []


    @staticmethod
    def get_by_username(username: str):
        if not username:
            return None
        try:
            connection = get_connection()
            cursor = connection.cursor(DictCursor)
            sql = "SELECT id, username, nombre, password, rol, zona_horaria FROM usuarios WHERE username = %s"
            cursor.execute(sql, (username,))
            user_data = cursor.fetchone()

            cursor.close()
            connection.close()

            if user_data:
                return User(
                    id=user_data['id'],
                    username=user_data['username'],
                    name=user_data['nombre'],
                    password=user_data['password'],
                    role=user_data.get('rol', 'USER'),
                    timezone=user_data.get('zona_horaria', 'AUTO')
                )
        except Exception as ex:
            print(f"Error al obtener usuario por username: {ex}")

        return None


    # Metodo estatico para crear un nuevo usuario
    @staticmethod
    def create(name: str, username: str, password: str, role: str = 'USER'):
        if not name or not username or not password:
            return False, 'Todos los campos son obligatorios'

        normalized_role = User.normalize_role(role)
        encrypted_password = generate_password_hash(password)

        try:
            connection = get_connection()
            cursor = connection.cursor()
            sql = """
                INSERT INTO usuarios (username, nombre, password, rol)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (username, name, encrypted_password, normalized_role))
            connection.commit()

            cursor.close()
            connection.close()
            return True, None
        except Exception as ex:
            message = str(ex)
            if 'Duplicate entry' in message or '1062' in message or 'IntegrityError' in message:
                return False, f"El nombre de usuario '{username}' ya está ocupado."

            print(f"Error al crear usuario: {ex}")
            return False, f"Error en el servidor: {ex}"


    # Metodo estatico para actualizar la contraseña del usuario
    @staticmethod
    def update_password(user_id: int, new_password: str):
        if not user_id or not new_password:
            return False, 'Datos incompletos para actualizar la contraseña'

        encrypted_password = generate_password_hash(new_password)

        try:
            connection = get_connection()
            cursor = connection.cursor()
            sql = "UPDATE usuarios SET password = %s WHERE id = %s"
            cursor.execute(sql, (encrypted_password, user_id))
            connection.commit()

            cursor.close()
            connection.close()
            return True, None
        except Exception as ex:
            print(f"Error al actualizar la contraseña: {ex}")
            return False, f"Error en el servidor: {ex}"
