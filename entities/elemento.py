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



class Elemento:
    def __init__(self, id: int, titulo: str, tipo: str, autor_director: str, genero: str, descripcion: str, calificacion: int, opinion: str, usuario_id: int, usuario_nombre: str, fecha_creacion: str, fecha_actualizacion: str, imagen_url: str = '', total_likes: int = 0, le_gusta_usuario: bool = False):
        self.id = id
        self.titulo = titulo
        self.tipo = tipo
        self.autor_director = autor_director
        self.genero = genero
        self.descripcion = descripcion
        self.calificacion = calificacion
        self.opinion = opinion
        self.usuario_id = usuario_id
        self.usuario_nombre = usuario_nombre
        self.fecha_creacion = fecha_creacion
        self.fecha_actualizacion = fecha_actualizacion
        self.imagen_url = imagen_url
        self.total_likes = total_likes
        self.le_gusta_usuario = le_gusta_usuario


    # Metodo estatico para obtener todos los elementos de la coleccion y mapearlos a objetos
    @staticmethod
    def obtener_todos(usuario_id: int = None) -> list:
        elementos = []
        try:
            conexion = get_connection()
            cursor = conexion.cursor(DictCursor) 
            if usuario_id:
                sql = """
                    SELECT c.id, c.titulo, c.tipo, c.autor_director, c.genero, c.descripcion, c.calificacion, c.opinion, c.imagen_url,
                        DATE_FORMAT(c.fecha_creacion, '%%Y-%%m-%%d %%H:%%i') as fecha_creacion,
                        DATE_FORMAT(c.fecha_actualizacion, '%%Y-%%m-%%d %%H:%%i') as fecha_actualizacion,
                        c.usuario_id, u.nombre as usuario_nombre,
                        COALESCE(mg.total_likes, 0) AS total_likes,
                        CASE WHEN ul.usuario_id IS NOT NULL THEN 1 ELSE 0 END AS le_gusta_usuario
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
                    ORDER BY c.id DESC
                """
                cursor.execute(sql, (usuario_id,))
            else:
                sql = """
                    SELECT c.id, c.titulo, c.tipo, c.autor_director, c.genero, c.descripcion, c.calificacion, c.opinion, c.imagen_url,
                        DATE_FORMAT(c.fecha_creacion, '%%Y-%%m-%%d %%H:%%i') as fecha_creacion,
                        DATE_FORMAT(c.fecha_actualizacion, '%%Y-%%m-%%d %%H:%%i') as fecha_actualizacion,
                        c.usuario_id, u.nombre as usuario_nombre,
                        COALESCE(mg.total_likes, 0) AS total_likes,
                        0 AS le_gusta_usuario
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

            resultados = cursor.fetchall()

            for r in resultados:
                nuevo_elemento = Elemento(
                    id=r['id'], titulo=r['titulo'], tipo=r['tipo'],
                    autor_director=r['autor_director'], genero=r.get('genero', ''), descripcion=r['descripcion'],
                    calificacion=r['calificacion'], opinion=r['opinion'],
                    usuario_id=r['usuario_id'], usuario_nombre=r['usuario_nombre'],
                    fecha_creacion=r['fecha_creacion'], fecha_actualizacion=r['fecha_actualizacion'],
                    imagen_url=r.get('imagen_url', ''),
                    total_likes=r.get('total_likes', 0), le_gusta_usuario=bool(r.get('le_gusta_usuario', 0))
                )
                elementos.append(nuevo_elemento)

            cursor.close()
            conexion.close()
        except Exception as ex:
            print(f"Error al obtener la colección: {ex}")
        return elementos


    # Metodo estatico para obtener un elemento por su ID
    @staticmethod
    def obtener_por_id(elemento_id: int):
        try:
            conexion = get_connection()
            cursor = conexion.cursor(DictCursor)
            sql = """
                SELECT c.id, c.titulo, c.tipo, c.autor_director, c.genero, c.descripcion, c.calificacion, c.opinion, c.imagen_url,
                   c.fecha_creacion, c.fecha_actualizacion, c.usuario_id, u.nombre as usuario_nombre
                FROM coleccion c
                LEFT JOIN usuarios u ON c.usuario_id = u.id
                WHERE c.id = %s
            """
            cursor.execute(sql, (elemento_id,))
            r = cursor.fetchone()
            
            cursor.close()
            conexion.close()

            if r:
                return Elemento(
                    id=r['id'],
                    titulo=r['titulo'],
                    tipo=r['tipo'],
                    autor_director=r['autor_director'],
                    genero=r.get('genero', ''),
                    descripcion=r['descripcion'],
                    calificacion=r['calificacion'],
                    opinion=r['opinion'],
                    usuario_id=r['usuario_id'],
                    usuario_nombre=r['usuario_nombre'],
                    fecha_creacion=str(r['fecha_creacion']),
                    fecha_actualizacion=str(r['fecha_actualizacion']),
                    imagen_url=r.get('imagen_url', '')
                )
        except Exception as ex:
            print(f"Error al obtener elemento por ID: {ex}")
        return None


    # Metodo estatico para guardar un nuevo elemento en la base de datos
    @staticmethod
    def save(titulo: str, tipo: str, autor_director: str, genero: str, descripcion: str, calificacion: int, opinion: str, imagen_url: str, usuario_id: int) -> bool:
        try:
            conexion = get_connection()
            cursor = conexion.cursor(DictCursor)
            ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            sql = """
                INSERT INTO coleccion (titulo, tipo, autor_director, genero, descripcion, calificacion, opinion, imagen_url, usuario_id, fecha_creacion, fecha_actualizacion) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (titulo, tipo, autor_director, genero, descripcion, calificacion, opinion, imagen_url, usuario_id, ahora, ahora))
            conexion.commit()

            cursor.close()
            conexion.close()
            return True
        except Exception as ex:
            print(f"Error al guardar en la Chihuahuateca: {ex}")
            return False


    # Metodo estatico para actualizar un elemento existente en la base de datos
    @staticmethod
    def update(id_elemento: int, titulo: str, tipo: str, autor_director: str, genero: str, descripcion: str, calificacion: int, opinion: str, imagen_url: str, usuario_id: int, user_role: str = 'usuario') -> bool:
        try:
            conexion = get_connection()
            cursor = conexion.cursor(DictCursor)
            ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            sql = """
                UPDATE coleccion 
                SET titulo = %s, tipo = %s, autor_director = %s, genero = %s, descripcion = %s, 
                    calificacion = %s, opinion = %s, imagen_url = %s, fecha_actualizacion = %s
                WHERE id = %s AND (usuario_id = %s OR %s = 'admin')
            """
            cursor.execute(sql, (titulo, tipo, autor_director, genero, descripcion, calificacion, opinion, imagen_url, ahora, id_elemento, usuario_id, user_role))
            conexion.commit()

            updated_rows = cursor.rowcount
            cursor.close()
            conexion.close()
            return updated_rows > 0
        except Exception as ex:
            print(f"Error al actualizar en la Chihuahuateca: {ex}")
            return False


    @staticmethod
    def toggle_like(usuario_id: int, elemento_id: int):
        try:
            conexion = get_connection()
            cursor = conexion.cursor(DictCursor)

            cursor.execute("SELECT id FROM coleccion WHERE id = %s", (elemento_id,))
            if not cursor.fetchone():
                cursor.close()
                conexion.close()
                return None

            cursor.execute("SELECT id FROM me_gusta WHERE usuario_id = %s AND elemento_id = %s", (usuario_id, elemento_id))
            fila_like = cursor.fetchone()
            if fila_like:
                cursor.execute("DELETE FROM me_gusta WHERE id = %s", (fila_like['id'],))
                liked = False
            else:
                ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("INSERT INTO me_gusta (usuario_id, elemento_id, fecha) VALUES (%s, %s, %s)", (usuario_id, elemento_id, ahora))
                liked = True

            conexion.commit()
            cursor.execute("SELECT COUNT(*) AS total_likes FROM me_gusta WHERE elemento_id = %s", (elemento_id,))
            total_likes = cursor.fetchone().get('total_likes', 0)

            cursor.close()
            conexion.close()
            return {'liked': liked, 'total_likes': total_likes}
        except Exception as ex:
            print(f"Error al alternar like: {ex}")
            return None


    # Metodo estatico para eliminar un elemento de la base de datos por su ID
    @staticmethod
    def delete(id_elemento: int, usuario_id: int, user_role: str = 'usuario') -> bool:
        try:
            conexion = get_connection()
            cursor = conexion.cursor(DictCursor)
            sql = "DELETE FROM coleccion WHERE id = %s AND (usuario_id = %s OR %s = 'admin')"
            cursor.execute(sql, (id_elemento, usuario_id, user_role))
            conexion.commit()

            deleted_rows = cursor.rowcount
            cursor.close()
            conexion.close()
            return deleted_rows > 0
        except Exception as ex:
            print(f"Error al eliminar de la Chihuahuateca: {ex}")
            return False
        