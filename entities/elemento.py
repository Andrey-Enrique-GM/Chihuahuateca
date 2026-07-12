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
    def __init__(self, id: int, titulo: str, tipo: str, autor_director: str, descripcion: str, calificacion: int, opinion: str, usuario_id: int, usuario_nombre: str, fecha_creacion: str, fecha_actualizacion: str):
        self.id = id
        self.titulo = titulo
        self.tipo = tipo
        self.autor_director = autor_director
        self.descripcion = descripcion
        self.calificacion = calificacion
        self.opinion = opinion
        self.usuario_id = usuario_id
        self.usuario_nombre = usuario_nombre
        self.fecha_creacion = fecha_creacion
        self.fecha_actualizacion = fecha_actualizacion


    # Metodo estatico para obtener todos los elementos de la coleccion y mapearlos a objetos
    @staticmethod
    def obtener_todos() -> list:
        elementos = []
        try:
            conexion = get_connection()
            cursor = conexion.cursor(DictCursor) 
            sql = """
                SELECT c.id, c.titulo, c.tipo, c.autor_director, c.descripcion, c.calificacion, c.opinion, 
                    DATE_FORMAT(c.fecha_creacion, '%Y-%m-%d %H:%i') as fecha_creacion,
                    DATE_FORMAT(c.fecha_actualizacion, '%Y-%m-%d %H:%i') as fecha_actualizacion,
                    c.usuario_id, u.nombre as usuario_nombre
                FROM coleccion c
                LEFT JOIN usuarios u ON c.usuario_id = u.id
                ORDER BY c.id DESC
            """
            cursor.execute(sql)
            resultados = cursor.fetchall()

            for r in resultados:
                nuevo_elemento = Elemento(
                    id=r['id'], titulo=r['titulo'], tipo=r['tipo'],
                    autor_director=r['autor_director'], descripcion=r['descripcion'],
                    calificacion=r['calificacion'], opinion=r['opinion'],
                    usuario_id=r['usuario_id'], usuario_nombre=r['usuario_nombre'],
                    fecha_creacion=r['fecha_creacion'], fecha_actualizacion=r['fecha_actualizacion']
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
                SELECT c.id, c.titulo, c.tipo, c.autor_director, c.descripcion, c.calificacion, c.opinion, 
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
                    descripcion=r['descripcion'],
                    calificacion=r['calificacion'],
                    opinion=r['opinion'],
                    usuario_id=r['usuario_id'],
                    usuario_nombre=r['usuario_nombre'],
                    fecha_creacion=str(r['fecha_creacion']),
                    fecha_actualizacion=str(r['fecha_actualizacion'])
                )
        except Exception as ex:
            print(f"Error al obtener elemento por ID: {ex}")
        return None


    # Metodo estatico para guardar un nuevo elemento en la base de datos
    @staticmethod
    def save(titulo: str, tipo: str, autor_director: str, descripcion: str, calificacion: int, opinion: str, usuario_id: int) -> bool:
        try:
            conexion = get_connection()
            cursor = conexion.cursor(DictCursor)
            ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            sql = """
                INSERT INTO coleccion (titulo, tipo, autor_director, descripcion, calificacion, opinion, usuario_id, fecha_creacion, fecha_actualizacion) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (titulo, tipo, autor_director, descripcion, calificacion, opinion, usuario_id, ahora, ahora))
            conexion.commit()

            cursor.close()
            conexion.close()
            return True
        except Exception as ex:
            print(f"Error al guardar en la Chihuahuateca: {ex}")
            return False


    # Metodo estatico para actualizar un elemento existente en la base de datos
    @staticmethod
    def update(id_elemento: int, titulo: str, tipo: str, autor_director: str, descripcion: str, calificacion: int, opinion: str) -> bool:
        try:
            conexion = get_connection()
            cursor = conexion.cursor(DictCursor)
            ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            sql = """
                UPDATE coleccion 
                SET titulo = %s, tipo = %s, autor_director = %s, descripcion = %s, 
                    calificacion = %s, opinion = %s, fecha_actualizacion = %s
                WHERE id = %s
            """
            cursor.execute(sql, (titulo, tipo, autor_director, descripcion, calificacion, opinion, ahora, id_elemento))
            conexion.commit()

            cursor.close()
            conexion.close()
            return True
        except Exception as ex:
            print(f"Error al actualizar en la Chihuahuateca: {ex}")
            return False


    # Metodo estatico para eliminar un elemento de la base de datos por su ID
    @staticmethod
    def delete(id_elemento: int) -> bool:
        try:
            conexion = get_connection()
            cursor = conexion.cursor(DictCursor)
            sql = "DELETE FROM coleccion WHERE id = %s"
            cursor.execute(sql, (id_elemento,))
            conexion.commit()

            cursor.close()
            conexion.close()
            return True
        except Exception as ex:
            print(f"Error al eliminar de la Chihuahuateca: {ex}")
            return False
        