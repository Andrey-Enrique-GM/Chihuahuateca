from datetime import datetime
from persistence.db import get_connection 
from pymysql.cursors import DictCursor



"""
Clase Elemento que representa cada registro de la tabla 'coleccion' y contiene metodos
estaticos para interactuar con la base de datos.
Cada metodo estatico se encarga de una operacion CRUD especifica
(Crear, Leer, Actualizar, Eliminar) y utiliza funciones definidas en persistence/consultas_db.py
para mantener una separacion clara entre la logica de negocio y la capa de acceso a datos.
"""



class Element:
    def __init__(
        self,
        id: int,
        title: str = '',
        element_type: str = '',
        author_director: str = '',
        genre: str = '',
        description: str = '',
        rating: int = 0,
        review: str = '',
        user_id: int = None,
        user_name: str = '',
        created_at: str = '',
        updated_at: str = '',
        image_url: str = '',
        total_likes: int = 0,
        user_likes: bool = False,
        user_username: str = None,
        user_follows_creator: bool = False,
    ):
        self.id = id
        self.title = title or ''
        self.element_type = element_type or ''
        self.author_director = author_director or ''
        self.genre = genre or ''
        self.description = description or ''
        self.rating = rating or 0
        self.review = review or ''
        self.user_id = user_id
        self.user_name = user_name or ''
        self.user_username = user_username
        self.created_at = created_at or ''
        self.updated_at = updated_at or ''
        self.image_url = image_url or ''
        self.total_likes = total_likes or 0
        self.user_likes = user_likes
        self.user_follows_creator = user_follows_creator


    # Metodo estatico para obtener todos los elementos de la coleccion y mapearlos a objetos
    @staticmethod
    def get_all(user_id: int = None) -> list:
        elements = []
        try:
            connection = get_connection()
            cursor = connection.cursor(DictCursor) 
            if user_id:
                sql = """
                    SELECT c.id, c.titulo, c.tipo, c.autor_director, c.genero, c.descripcion, c.calificacion, c.opinion, c.imagen_url,
                        DATE_FORMAT(c.fecha_creacion, '%%Y-%%m-%%d %%H:%%i') as fecha_creacion,
                        DATE_FORMAT(c.fecha_actualizacion, '%%Y-%%m-%%d %%H:%%i') as fecha_actualizacion,
                        c.usuario_id, u.nombre as usuario_nombre, u.username as usuario_username,
                        COALESCE(mg.total_likes, 0) AS total_likes,
                        CASE WHEN ul.usuario_id IS NOT NULL THEN 1 ELSE 0 END AS le_gusta_usuario,
                        CASE WHEN sf.seguidor_id IS NOT NULL THEN 1 ELSE 0 END AS usuario_sigue_creador
                    FROM coleccion c
                    LEFT JOIN usuarios u ON c.usuario_id = u.id
                    LEFT JOIN (
                        SELECT elemento_id, COUNT(*) AS total_likes
                        FROM me_gusta
                        GROUP BY elemento_id
                    ) mg ON mg.elemento_id = c.id
                    LEFT JOIN (
                        SELECT elemento_id, usuario_id
                        FROM me_gusta
                        WHERE usuario_id = %s
                    ) ul ON ul.elemento_id = c.id
                    LEFT JOIN seguidores sf ON sf.seguido_id = c.usuario_id AND sf.seguidor_id = %s
                    ORDER BY c.id DESC
                """
                cursor.execute(sql, (user_id, user_id))
            else:
                sql = """
                    SELECT c.id, c.titulo, c.tipo, c.autor_director, c.genero, c.descripcion, c.calificacion, c.opinion, c.imagen_url,
                        DATE_FORMAT(c.fecha_creacion, '%%Y-%%m-%%d %%H:%%i') as fecha_creacion,
                        DATE_FORMAT(c.fecha_actualizacion, '%%Y-%%m-%%d %%H:%%i') as fecha_actualizacion,
                        c.usuario_id, u.nombre as usuario_nombre, u.username as usuario_username,
                        COALESCE(mg.total_likes, 0) AS total_likes,
                        0 AS le_gusta_usuario,
                        0 AS usuario_sigue_creador
                    FROM coleccion c
                    LEFT JOIN usuarios u ON c.usuario_id = u.id
                    LEFT JOIN (
                        SELECT elemento_id, COUNT(*) AS total_likes
                        FROM me_gusta
                        GROUP BY elemento_id
                    ) mg ON mg.elemento_id = c.id
                    ORDER BY c.id DESC
                """
                cursor.execute(sql)

            results = cursor.fetchall()

            for r in results:
                new_element = Element(
                    id=r['id'],
                    title=r['titulo'],
                    element_type=r['tipo'],
                    author_director=r['autor_director'],
                    genre=r.get('genero', ''),
                    description=r['descripcion'],
                    rating=r['calificacion'],
                    review=r['opinion'],
                    user_id=r['usuario_id'],
                    user_name=r['usuario_nombre'],
                    created_at=r['fecha_creacion'],
                    updated_at=r['fecha_actualizacion'],
                    image_url=r.get('imagen_url', ''),
                    total_likes=r.get('total_likes', 0),
                    user_likes=bool(r.get('le_gusta_usuario', 0)),
                    user_username=r.get('usuario_username'),
                    user_follows_creator=bool(r.get('usuario_sigue_creador', 0))
                )
                elements.append(new_element)

            cursor.close()
            connection.close()
        except Exception as ex:
            print(f"Error al obtener la colección: {ex}")
        return elements


    # Metodo estatico para obtener un elemento por su ID
    @staticmethod
    def get_by_id(element_id: int):
        try:
            connection = get_connection()
            cursor = connection.cursor(DictCursor)
            sql = """
                SELECT c.id, c.titulo, c.tipo, c.autor_director, c.genero, c.descripcion, c.calificacion, c.opinion, c.imagen_url,
                   c.fecha_creacion, c.fecha_actualizacion, c.usuario_id, u.nombre as usuario_nombre, u.username as usuario_username
                FROM coleccion c
                LEFT JOIN usuarios u ON c.usuario_id = u.id
                WHERE c.id = %s
            """
            cursor.execute(sql, (element_id,))
            r = cursor.fetchone()
            
            cursor.close()
            connection.close()

            if r:
                return Element(
                    id=r['id'],
                    title=r['titulo'],
                    element_type=r['tipo'],
                    author_director=r['autor_director'],
                    genre=r.get('genero', ''),
                    description=r['descripcion'],
                    rating=r['calificacion'],
                    review=r['opinion'],
                    user_id=r['usuario_id'],
                    user_name=r['usuario_nombre'],
                    user_username=r.get('usuario_username'),
                    created_at=str(r['fecha_creacion']),
                    updated_at=str(r['fecha_actualizacion']),
                    image_url=r.get('imagen_url', '')
                )
        except Exception as ex:
            print(f"Error al obtener elemento por ID: {ex}")
        return None


    # Metodo estatico para guardar un nuevo elemento en la base de datos
    @staticmethod
    def save(
        title: str,
        element_type: str,
        author_director: str,
        genre: str,
        description: str,
        rating: int,
        review: str,
        image_url: str,
        user_id: int
    ) -> bool:
        try:
            connection = get_connection()
            cursor = connection.cursor(DictCursor)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            sql = """
                INSERT INTO coleccion (titulo, tipo, autor_director, genero, descripcion, calificacion, opinion, imagen_url, usuario_id, fecha_creacion, fecha_actualizacion) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (title, element_type, author_director, genre, description, rating, review, image_url, user_id, now, now))
            connection.commit()

            cursor.close()
            connection.close()
            return True
        except Exception as ex:
            print(f"Error al guardar en la Chihuahuateca: {ex}")
            return False


    # Metodo estatico para actualizar un elemento existente en la base de datos
    @staticmethod
    def update(
        element_id: int,
        title: str,
        element_type: str,
        author_director: str,
        genre: str,
        description: str,
        rating: int,
        review: str,
        image_url: str,
        user_id: int,
        user_role: str = 'USER'
    ) -> bool:
        try:
            connection = get_connection()
            cursor = connection.cursor(DictCursor)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            normalized_role = (user_role or '').strip().upper()
            
            sql = """
                UPDATE coleccion 
                SET titulo = %s, tipo = %s, autor_director = %s, genero = %s, descripcion = %s, 
                    calificacion = %s, opinion = %s, imagen_url = %s, fecha_actualizacion = %s
                WHERE id = %s AND (usuario_id = %s OR %s = 'ADMIN')
            """
            cursor.execute(sql, (title, element_type, author_director, genre, description, rating, review, image_url, now, element_id, user_id, normalized_role))
            connection.commit()

            updated_rows = cursor.rowcount
            cursor.close()
            connection.close()
            return updated_rows > 0
        except Exception as ex:
            print(f"Error al actualizar en la Chihuahuateca: {ex}")
            return False


    @staticmethod
    def toggle_like(user_id: int, element_id: int):
        try:
            connection = get_connection()
            cursor = connection.cursor(DictCursor)

            cursor.execute("SELECT id FROM coleccion WHERE id = %s", (element_id,))
            if not cursor.fetchone():
                cursor.close()
                connection.close()
                return None

            cursor.execute("SELECT id FROM me_gusta WHERE usuario_id = %s AND elemento_id = %s", (user_id, element_id))
            like_row = cursor.fetchone()
            if like_row:
                cursor.execute("DELETE FROM me_gusta WHERE id = %s", (like_row['id'],))
                liked = False
            else:
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("INSERT INTO me_gusta (usuario_id, elemento_id, fecha) VALUES (%s, %s, %s)", (user_id, element_id, now))
                liked = True

            connection.commit()
            cursor.execute("SELECT COUNT(*) AS total_likes FROM me_gusta WHERE elemento_id = %s", (element_id,))
            total_likes = cursor.fetchone().get('total_likes', 0)

            cursor.close()
            connection.close()
            return {'liked': liked, 'total_likes': total_likes}
        except Exception as ex:
            print(f"Error al alternar like: {ex}")
            return None


    # Metodo estatico para eliminar un elemento de la base de datos por su ID
    @staticmethod
    def delete(element_id: int, user_id: int, user_role: str = 'USER') -> bool:
        try:
            connection = get_connection()
            cursor = connection.cursor(DictCursor)
            normalized_role = (user_role or '').strip().upper()
            sql = "DELETE FROM coleccion WHERE id = %s AND (usuario_id = %s OR %s = 'ADMIN')"
            cursor.execute(sql, (element_id, user_id, normalized_role))
            connection.commit()

            deleted_rows = cursor.rowcount
            cursor.close()
            connection.close()
            return deleted_rows > 0
        except Exception as ex:
            print(f"Error al eliminar de la Chihuahuateca: {ex}")
            return False
