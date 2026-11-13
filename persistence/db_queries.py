from datetime import datetime
from .db_utils import cursor as db_cursor



"""
Este archivo contiene funciones que interactúan directamente con la base de datos para realizar operaciones
CRUD (Crear, Leer, Actualizar, Eliminar) sobre los elementos de la colección. Estas funciones son utilizadas
por los métodos estáticos de la clase Elemento en entities/elemento.py para mantener una separación clara entre
la lógica de negocio y la capa de acceso a datos.
"""


# ---------------------------------------------------------------------
# READ OPERATIONS
# ---------------------------------------------------------------------

# Metodo para obtener toda la coleccion de elementos
def get_all_collection():
    """Return all rows of the `coleccion` table.
    Dates are formatted on the DB side for display convenience.
    Uses a ``DictCursor`` so the caller receives a list of ``dict`` objects.
    """
    sql = """
        SELECT id, titulo, tipo, autor_director, genero, descripcion, calificacion, opinion,
               DATE_FORMAT(fecha_creacion, '%%Y-%%m-%%d %%H:%%i') AS fecha_creacion,
               DATE_FORMAT(fecha_actualizacion, '%%Y-%%m-%%d %%H:%%i') AS fecha_actualizacion
        FROM coleccion
        ORDER BY id DESC
    """
    with db_cursor(dict_cursor=True) as cur:
        cur.execute(sql)
        results = cur.fetchall()
    return results


# Metodo para obtener un elemento por su ID
def get_element_by_id(element_id: int):
    """Fetch a single element by its primary key.
    Returns ``None`` if the id does not exist.
    """
    sql = """
        SELECT id, titulo, tipo, autor_director, genero, descripcion, calificacion, opinion,
               fecha_creacion, fecha_actualizacion, usuario_id
        FROM coleccion
        WHERE id = %s
    """
    with db_cursor(dict_cursor=True) as cur:
        cur.execute(sql, (element_id,))
        return cur.fetchone()


# ---------------------------------------------------------------------
# WRITE OPERATIONS (INSERT / UPDATE / DELETE)
# ---------------------------------------------------------------------

# Metodo para insertar un nuevo elemento en la base de datos
def insert_element(title, item_type, author_director, genre, description, rating, review):
    """Insert a new row into ``coleccion``.
    ``now`` is stored both as ``fecha_creacion`` and ``fecha_actualizacion``.
    Returns a ``dict`` with ``success`` and a human‑readable ``message``.
    """
    sql = """
        INSERT INTO coleccion (
            titulo, tipo, autor_director, genero, descripcion,
            calificacion, opinion, fecha_creacion, fecha_actualizacion
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    params = (title, item_type, author_director, genre, description,
              rating, review, now, now)
    try:
        with db_cursor(commit=True) as cur:
            cur.execute(sql, params)
        return {"success": True, "message": "¡Guardado con éxito en la Chihuahuateca!"}
    except Exception as exc:
        return {"success": False, "message": f"Error: {exc}"}


# Metodo para actualizar un elemento existente en la base de datos
def update_element(element_id, title, item_type, author_director, genre, description, rating, review):
    """Update an existing element.
    Only ``fecha_actualizacion`` is changed; ``fecha_creacion`` stays untouched.
    """
    sql = """
        UPDATE coleccion
        SET titulo = %s,
            tipo = %s,
            autor_director = %s,
            genero = %s,
            descripcion = %s,
            calificacion = %s,
            opinion = %s,
            fecha_actualizacion = %s
        WHERE id = %s
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    params = (title, item_type, author_director, genre, description,
              rating, review, now, element_id)
    try:
        with db_cursor(commit=True) as cur:
            cur.execute(sql, params)
            if cur.rowcount == 0:
                return {"success": False, "message": "Elemento no encontrado"}
        return {"success": True, "message": "¡Elemento actualizado correctamente!"}
    except Exception as exc:
        return {"success": False, "message": f"Error: {exc}"}


# Metodo para eliminar un elemento de la base de datos por su ID
def delete_element(element_id):
    """Delete a row from ``coleccion`` by its id.
    Returns a ``dict`` indicating success or failure.
    """
    sql = "DELETE FROM coleccion WHERE id = %s"
    try:
        with db_cursor(commit=True) as cur:
            cur.execute(sql, (element_id,))
            if cur.rowcount == 0:
                return {"success": False, "message": "No existía el elemento"}
        return {"success": True, "message": "Eliminado de la Chihuahuateca de forma permanente."}
    except Exception as exc:
        return {"success": False, "message": f"Error: {exc}"}
