import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime
from urllib.parse import quote_plus, urlparse

from entities.elemento import Elemento
from entities.log import Log
from entities.usuario import User
from enums.log_type import LogType
from persistence.db import get_connection
from pymysql.cursors import DictCursor


def sanitize_text(value, required=False, max_length=255):
    if value is None:
        value = ''
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if required and not value:
        return None
    if len(value) > max_length:
        return value[:max_length]
    return value


def sanitize_url(value):
    if value is None:
        return ''
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if not value:
        return ''

    parsed = urlparse(value)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        return None
    return value


def validate_elemento_payload(data, require_id=False):
    if not isinstance(data, dict):
        return False, 'Datos inválidos', None

    titulo = sanitize_text(data.get('titulo'), required=True, max_length=200)
    tipo = sanitize_text(data.get('tipo'), required=True, max_length=20)
    autor_director = sanitize_text(data.get('autor_director'), required=True, max_length=150)
    genero = sanitize_text(data.get('genero'), required=False, max_length=50) or ''
    descripcion = sanitize_text(data.get('descripcion'), required=False, max_length=1000)
    opinion = sanitize_text(data.get('opinion'), required=False, max_length=1000)
    imagen_url_raw = data.get('imagen_url', '')
    imagen_url = sanitize_url(imagen_url_raw)

    if titulo is None:
        return False, 'El título es obligatorio', None
    if tipo not in ('libro', 'pelicula', 'serie'):
        return False, 'El tipo debe ser libro, pelicula o serie', None
    if autor_director is None:
        return False, 'Autor / Director / Creador es obligatorio', None
    if imagen_url_raw and imagen_url is None:
        return False, 'La URL de la imagen no es válida', None

    try:
        calificacion = int(data.get('calificacion'))
    except (TypeError, ValueError):
        return False, 'La calificación debe ser un número entre 1 y 5', None

    if calificacion < 1 or calificacion > 5:
        return False, 'La calificación debe estar entre 1 y 5', None

    elemento_id = None
    if require_id:
        try:
            elemento_id = int(data.get('id'))
        except (TypeError, ValueError):
            return False, 'ID de elemento inválido', None

    return True, None, {
        'titulo': titulo,
        'tipo': tipo,
        'autor_director': autor_director,
        'genero': genero,
        'descripcion': descripcion,
        'opinion': opinion,
        'calificacion': calificacion,
        'imagen_url': imagen_url,
        'id': elemento_id,
    }


def normalizar_titulo(titulo):
    texto = (titulo or '').strip()
    texto = re.sub(r"[^\w\sáéíóúÁÉÍÓÚñÑüÜ-]", ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def merge_datos(datos_base, datos_fallback):
    if not datos_base:
        return datos_fallback
    if not datos_fallback:
        return datos_base

    return {
        'titulo': datos_base.get('titulo') or datos_fallback.get('titulo'),
        'descripcion': datos_base.get('descripcion') or datos_fallback.get('descripcion') or '',
        'imagen_url': datos_base.get('imagen_url') or datos_fallback.get('imagen_url') or '',
    }


def buscar_datos_openlibrary(titulo):
    texto_limpio = normalizar_titulo(titulo)
    if not texto_limpio:
        return None

    url = f"https://openlibrary.org/search.json?title={quote_plus(texto_limpio)}&limit=1"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        return None

    docs = data.get('docs', [])
    if not docs:
        return None

    doc = docs[0]
    descripcion = ''
    if isinstance(doc.get('first_sentence'), list):
        descripcion = ' '.join(doc.get('first_sentence', [])).strip()
    elif isinstance(doc.get('first_sentence'), str):
        descripcion = doc.get('first_sentence').strip()
    elif isinstance(doc.get('subtitle'), str):
        descripcion = doc.get('subtitle').strip()

    imagen_url = ''
    if doc.get('cover_i'):
        imagen_url = f"https://covers.openlibrary.org/b/id/{doc.get('cover_i')}-L.jpg"
    elif doc.get('cover_edition_key'):
        imagen_url = f"https://covers.openlibrary.org/b/olid/{doc.get('cover_edition_key')}-L.jpg"

    return {
        'titulo': doc.get('title_suggest') or doc.get('title') or titulo,
        'descripcion': descripcion,
        'imagen_url': imagen_url,
    }


def buscar_datos_google_books(titulo):
    texto_limpio = normalizar_titulo(titulo)
    if not texto_limpio:
        return None

    url = f"https://www.googleapis.com/books/v1/volumes?q={quote_plus(texto_limpio)}&langRestrict=es&maxResults=5"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        return None

    items = data.get('items', [])
    if not items:
        return None

    for item in items:
        info = item.get('volumeInfo', {})
        if not info.get('title'):
            continue

        descripcion = info.get('description', '') or ''
        imagen_url = ''
        image_links = info.get('imageLinks', {})
        if image_links.get('thumbnail'):
            imagen_url = image_links.get('thumbnail').replace('http://', 'https://')
        elif image_links.get('smallThumbnail'):
            imagen_url = image_links.get('smallThumbnail').replace('http://', 'https://')

        return {
            'titulo': info.get('title') or titulo,
            'descripcion': descripcion,
            'imagen_url': imagen_url,
        }

    return None


def buscar_datos_omdb(titulo, tipo):
    api_key = os.getenv('OMDB_API_KEY', '').strip()
    if not api_key:
        return None

    tipo_busqueda = 'series' if tipo == 'serie' else 'movie'
    url = f"http://www.omdbapi.com/?apikey={quote_plus(api_key)}&t={quote_plus(titulo)}&type={quote_plus(tipo_busqueda)}&plot=short&r=json"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        return None

    if data.get('Response') != 'True':
        return None

    descripcion = data.get('Plot', '')
    if descripcion == 'N/A':
        descripcion = ''

    imagen_url = data.get('Poster', '')
    if imagen_url == 'N/A':
        imagen_url = ''

    return {
        'titulo': data.get('Title', titulo),
        'descripcion': descripcion,
        'imagen_url': imagen_url,
    }


def buscar_datos_tmdb(titulo, tipo):
    api_key = os.getenv('TMDB_API_KEY', '').strip()
    if not api_key:
        return None

    media_type = 'tv' if tipo == 'serie' else 'movie'
    search_url = f"https://api.themoviedb.org/3/search/{media_type}?api_key={quote_plus(api_key)}&query={quote_plus(titulo)}&language=es-ES&page=1"
    try:
        with urllib.request.urlopen(search_url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        return None

    resultados = data.get('results', [])
    if not resultados:
        return None

    item = resultados[0]
    descripcion = item.get('overview', '') or ''
    imagen_url = ''
    poster_path = item.get('poster_path')
    if poster_path:
        imagen_url = f"https://image.tmdb.org/t/p/w500{poster_path}"

    return {
        'titulo': item.get('name') or item.get('title') or titulo,
        'descripcion': descripcion,
        'imagen_url': imagen_url,
    }


def buscar_datos_itunes(titulo, tipo):
    texto_limpio = normalizar_titulo(titulo)
    if not texto_limpio:
        return None

    media = 'tvShow' if tipo == 'serie' else 'movie'
    url = f"https://itunes.apple.com/search?term={quote_plus(texto_limpio)}&media={quote_plus(media)}&limit=1"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        return None

    items = data.get('results', [])
    if not items:
        return None

    item = items[0]
    descripcion = item.get('longDescription') or item.get('shortDescription') or ''
    imagen_url = item.get('artworkUrl100', '')
    if imagen_url:
        imagen_url = imagen_url.replace('100x100bb', '600x600bb').replace('100x100', '600x600')

    titulo_itunes = item.get('trackName') or item.get('collectionName') or titulo
    return {
        'titulo': titulo_itunes,
        'descripcion': descripcion,
        'imagen_url': imagen_url,
    }


def buscar_datos_externos(tipo, titulo):
    if tipo == 'libro':
        datos_ol = buscar_datos_openlibrary(titulo)
        datos_google = buscar_datos_google_books(titulo)
        return merge_datos(datos_ol, datos_google)

    datos = None
    if os.getenv('OMDB_API_KEY', '').strip():
        datos = buscar_datos_omdb(titulo, tipo)
    if not datos and os.getenv('TMDB_API_KEY', '').strip():
        datos = buscar_datos_tmdb(titulo, tipo)
    if not datos:
        datos = buscar_datos_itunes(titulo, tipo)

    return datos


def guardar_elemento(usuario_id, payload):
    exito = Elemento.save(
        titulo=payload['titulo'],
        tipo=payload['tipo'],
        autor_director=payload['autor_director'],
        genero=payload['genero'],
        descripcion=payload['descripcion'],
        calificacion=payload['calificacion'],
        opinion=payload['opinion'],
        imagen_url=payload['imagen_url'],
        usuario_id=usuario_id,
    )

    if exito:
        return True, None
    return False, 'Error interno al guardar el elemento'


def editar_elemento(session, payload):
    exito = Elemento.update(
        id_elemento=payload['id'],
        titulo=payload['titulo'],
        tipo=payload['tipo'],
        autor_director=payload['autor_director'],
        genero=payload['genero'],
        descripcion=payload['descripcion'],
        calificacion=payload['calificacion'],
        opinion=payload['opinion'],
        imagen_url=payload['imagen_url'],
        usuario_id=session['usuario_id'],
        user_role=(session.get('rol', 'USER') or 'USER')
    )

    if exito:
        usuario = User(
            id=session['usuario_id'],
            username=session.get('username', ''),
            nombre=session.get('nombre', ''),
            password='',
            rol=(session.get('rol', 'USER') or 'USER')
        )
        Log.save_log(usuario, f"Editó el elemento '{payload['titulo']}'", LogType.EDIT)
        return True, None

    return False, 'No autorizado o no se encontró el elemento'


def borrar_elemento(session, elemento_id):
    exito = Elemento.delete(
        id_elemento=elemento_id,
        usuario_id=session['usuario_id'],
        user_role=(session.get('rol', 'USER') or 'USER')
    )

    if exito:
        usuario = User(
            id=session['usuario_id'],
            username=session.get('username', ''),
            nombre=session.get('nombre', ''),
            password='',
            rol=(session.get('rol', 'USER') or 'USER')
        )
        Log.save_log(usuario, f'Eliminó el elemento con ID {elemento_id}', LogType.DELETE)
        return True, None

    return False, 'No autorizado o no se encontró el elemento'


def alternar_like(session, elemento_id):
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return False, 'No hay sesión activa', 401

    resultado = Elemento.toggle_like(usuario_id, elemento_id)
    if resultado is None:
        return False, 'Elemento no encontrado o error interno', 404

    return True, {
        'liked': resultado['liked'],
        'total_likes': resultado['total_likes'],
    }, 200


def alternar_seguimiento(session, usuario_id):
    seguidor_id = session.get('usuario_id') or session.get('user_id')
    if not seguidor_id:
        return False, 'No hay sesión activa', 401

    if seguidor_id == usuario_id:
        return False, 'No puedes seguirte a ti mismo.', 400

    try:
        conexion = get_connection()
        cursor = conexion.cursor(DictCursor)

        cursor.execute('SELECT id FROM usuarios WHERE id = %s', (usuario_id,))
        if not cursor.fetchone():
            cursor.close(); conexion.close()
            return False, 'Usuario no encontrado.', 404

        cursor.execute(
            'SELECT id FROM seguidores WHERE seguidor_id = %s AND seguido_id = %s',
            (seguidor_id, usuario_id)
        )
        ya_sigue = cursor.fetchone()

        if ya_sigue:
            cursor.execute(
                'DELETE FROM seguidores WHERE seguidor_id = %s AND seguido_id = %s',
                (seguidor_id, usuario_id)
            )
            siguiendo = False
            descripcion = f'Dejó de seguir al usuario ID {usuario_id}'
            tipo_log = LogType.UNFOLLOW
        else:
            cursor.execute(
                'INSERT INTO seguidores (seguidor_id, seguido_id, fecha) VALUES (%s, %s, NOW())',
                (seguidor_id, usuario_id)
            )
            siguiendo = True
            descripcion = f'Comenzó a seguir al usuario ID {usuario_id}'
            tipo_log = LogType.FOLLOW

        conexion.commit()
        cursor.execute('SELECT COUNT(*) AS total FROM seguidores WHERE seguido_id = %s', (usuario_id,))
        total_seguidores = int(cursor.fetchone()['total'] or 0)

        usuario = User(
            id=seguidor_id,
            username=session.get('username', ''),
            nombre=session.get('nombre', ''),
            password='',
            rol=(session.get('rol', 'USER') or 'USER')
        )
        Log.save_log(usuario, descripcion, tipo_log)

        cursor.close(); conexion.close()
        return True, {'siguiendo': siguiendo, 'total_seguidores': total_seguidores}, 200
    except Exception as ex:
        print(f'Error al alternar seguimiento: {ex}')
        return False, 'No se pudo actualizar el seguimiento.', 500
