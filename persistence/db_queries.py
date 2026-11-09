from datetime import datetime
from persistence.db import get_connection 



""""
Este archivo contiene funciones que interactúan directamente con la base de datos para realizar operaciones
CRUD (Crear, Leer, Actualizar, Eliminar) sobre los elementos de la colección. Estas funciones son utilizadas
por los métodos estáticos de la clase Elemento en entities/elemento.py para mantener una separación clara entre
la lógica de negocio y la capa de acceso a datos.
"""



# Metodo para obtener toda la coleccion de elementos, con las fechas formateadas para que se vean limpias en el HTML
def get_all_collection():
    connection = get_connection() 
    cursor = connection.cursor(dictionary=True)
    
    # Traemos las fechas formateadas para que en el HTML se vean limpias (Ej: 2026-05-23 22:40)
    cursor.execute("""
        SELECT id, titulo, tipo, autor_director, genero, descripcion, calificacion, opinion, 
               DATE_FORMAT(fecha_creacion, '%%Y-%%m-%%d %%H:%%i') as fecha_creacion,
               DATE_FORMAT(fecha_actualizacion, '%%Y-%%m-%%d %%H:%%i') as fecha_actualizacion 
        FROM coleccion 
        ORDER BY id DESC
    """)
    results = cursor.fetchall()
    
    cursor.close()
    connection.close()  
    return results


# Metodo para obtener un elemento por su ID
def get_element_by_id(element_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("SELECT id, titulo, tipo, autor_director, genero, descripcion, calificacion, opinion, fecha_creacion, fecha_actualizacion, usuario_id FROM coleccion WHERE id = %s", (element_id,))
    result = cursor.fetchone()
    
    cursor.close()
    connection.close()
    return result


# Metodo para insertar un nuevo elemento en la base de datos
def insert_element(title, item_type, author_director, genre, description, rating, review):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Al crear por primera vez, ambas fechas llevan el mismo valor
        query = """
            INSERT INTO coleccion (titulo, tipo, autor_director, genero, descripcion, calificacion, opinion, fecha_creacion, fecha_actualizacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (title, item_type, author_director, genre, description, rating, review, now, now))
        connection.commit()
        
        cursor.close()
        connection.close()
        return {"success": True, "message": "¡Guardado con éxito en la Chihuahuateca!"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


# Metodo para actualizar un elemento existente en la base de datos
def update_element(element_id, title, item_type, author_director, genre, description, rating, review):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Aquí SOLO actualizamos la fecha_actualizacion, la de creación se queda intacta
        query = """
            UPDATE coleccion 
            SET titulo = %s, tipo = %s, autor_director = %s, genero = %s, descripcion = %s, 
                calificacion = %s, opinion = %s, fecha_actualizacion = %s
            WHERE id = %s
        """
        cursor.execute(query, (title, item_type, author_director, genre, description, rating, review, now, element_id))
        connection.commit()
        
        cursor.close()
        connection.close()
        return {"success": True, "message": "¡Elemento actualizado correctamente!"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


# Metodo para eliminar un elemento de la base de datos por su ID
def delete_element(element_id):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        
        cursor.execute("DELETE FROM coleccion WHERE id = %s", (element_id,))
        connection.commit()
        
        cursor.close()
        connection.close()
        return {"success": True, "message": "Eliminado de la Chihuahuateca de forma permanente."}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}
