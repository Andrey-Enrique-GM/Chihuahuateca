from contextlib import contextmanager
from persistence.db import get_connection



"""
Este archivo contiene funciones de utilidad para interactuar con la base de datos.
La función `cursor` es un context manager que se encarga de crear una conexión a la base de datos
y devolver un cursor. Si `commit` es True, se hará commit de la transacción al salir del bloque.
Si ocurre un error, se hará rollback.
"""



@contextmanager
def cursor(commit: bool = False, dict_cursor: bool = False):
    conn = get_connection()
    cur = conn.cursor() if not dict_cursor else conn.cursor(dictionary=True)
    try:
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
