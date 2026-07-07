from datetime import datetime
from persistence.db import get_connection 



""""
Este archivo contiene funciones que interactúan directamente con la base de datos para realizar operaciones
CRUD (Crear, Leer, Actualizar, Eliminar) sobre los elementos de la colección. Estas funciones son utilizadas
por los métodos estáticos de la clase Elemento en entities/elemento.py para mantener una separación clara entre
la lógica de negocio y la capa de acceso a datos.
"""



# Metodo para obtener toda la coleccion de elementos, con las fechas formateadas para que se vean limpias en el HTML
def obtener_toda_la_coleccion():
    conexion = get_connection() 
    cursor = conexion.cursor(dictionary=True)
    
    # Traemos las fechas formateadas para que en el HTML se vean limpias (Ej: 2026-05-23 22:40)
    cursor.execute("""
        SELECT id, titulo, tipo, autor_director, descripcion, calificacion, opinion, 
               DATE_FORMAT(fecha_creacion, '%Y-%m-%d %H:%i') as fecha_creacion,
               DATE_FORMAT(fecha_actualizacion, '%Y-%m-%d %H:%i') as fecha_actualizacion 
        FROM coleccion 
        ORDER BY id DESC
    """)
    resultados = cursor.fetchall()
    
    cursor.close()
    conexion.close()  
    return resultados


# Metodo para obtener un elemento por su ID
def obtener_elemento_por_id(elemento_id):
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM coleccion WHERE id = %s", (elemento_id,))
    resultado = cursor.fetchone()
    
    cursor.close()
    conexion.close()
    return resultado


# Metodo para insertar un nuevo elemento en la base de datos
def insertar_elemento(titulo, tipo, autor_director, descripcion, calificacion, opinion):
    try:
        conexion = get_connection()
        cursor = conexion.cursor()
        ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Al crear por primera vez, ambas fechas llevan el mismo valor
        query = """
            INSERT INTO coleccion (titulo, tipo, autor_director, descripcion, calificacion, opinion, fecha_creacion, fecha_actualizacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (titulo, tipo, autor_director, descripcion, calificacion, opinion, ahora, ahora))
        conexion.commit()
        
        cursor.close()
        conexion.close()
        return {"success": True, "message": "¡Guardado con éxito en la Chihuahuateca!"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


# Metodo para actualizar un elemento existente en la base de datos
def actualizar_elemento(id_elemento, titulo, tipo, autor_director, descripcion, calificacion, opinion):
    try:
        conexion = get_connection()
        cursor = conexion.cursor()
        ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Aquí SOLO actualizamos la fecha_actualizacion, la de creación se queda intacta
        query = """
            UPDATE coleccion 
            SET titulo = %s, tipo = %s, autor_director = %s, descripcion = %s, 
                calificacion = %s, opinion = %s, fecha_actualizacion = %s
            WHERE id = %s
        """
        cursor.execute(query, (titulo, tipo, autor_director, descripcion, calificacion, opinion, ahora, id_elemento))
        conexion.commit()
        
        cursor.close()
        conexion.close()
        return {"success": True, "message": "¡Elemento actualizado correctamente!"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


# Metodo para eliminar un elemento de la base de datos por su ID
def eliminar_elemento(id_elemento):
    try:
        conexion = get_connection()
        cursor = conexion.cursor()
        
        cursor.execute("DELETE FROM coleccion WHERE id = %s", (id_elemento,))
        conexion.commit()
        
        cursor.close()
        conexion.close()
        return {"success": True, "message": "Eliminado de la Chihuahuateca de forma permanente."}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
    