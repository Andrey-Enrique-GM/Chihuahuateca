import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime
from urllib.parse import quote_plus, urlparse

from entities.element import Element
from entities.log import Log
from entities.user import User
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
        value = ''
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if not value:
        return ''

    parsed = urlparse(value)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        return None
    return value


def validate_element_payload(data, require_id=False):
    if not isinstance(data, dict):
        return False, 'Datos inválidos', None

    title = sanitize_text(data.get('title') or data.get('titulo'), required=True, max_length=200)
    item_type = sanitize_text(data.get('element_type') or data.get('tipo') or data.get('type'), required=True, max_length=20)
    author_director = sanitize_text(data.get('author_director') or data.get('autor_director'), required=True, max_length=150)
    genre = sanitize_text(data.get('genre') or data.get('genero'), required=False, max_length=50) or ''
    description = sanitize_text(data.get('description') or data.get('descripcion'), required=False, max_length=1000)
    review = sanitize_text(data.get('review') or data.get('opinion'), required=False, max_length=1000)
    raw_image_url = data.get('image_url') if 'image_url' in data else data.get('imagen_url', '')
    image_url = sanitize_url(raw_image_url)

    if title is None:
        return False, 'El título es obligatorio', None
    if item_type not in ('libro', 'pelicula', 'serie'):
        return False, 'El tipo debe ser libro, pelicula o serie', None
    if author_director is None:
        return False, 'Autor / Director / Creador es obligatorio', None
    if raw_image_url and image_url is None:
        return False, 'La URL de la imagen no es válida', None

    raw_rating = data.get('rating') if 'rating' in data else data.get('calificacion')
    try:
        rating = int(raw_rating)
    except (TypeError, ValueError):
        return False, 'La calificación debe ser un número entre 1 y 5', None

    if rating < 1 or rating > 5:
        return False, 'La calificación debe estar entre 1 y 5', None

    element_id = None
    if require_id:
        try:
            element_id = int(data.get('id'))
        except (TypeError, ValueError):
            return False, 'ID de elemento inválido', None

    return True, None, {
        'id': element_id,
        'title': title,
        'element_type': item_type,
        'author_director': author_director,
        'genre': genre,
        'description': description,
        'review': review,
        'rating': rating,
        'image_url': image_url,
    }


def normalize_title(title):
    text = (title or '').strip()
    text = re.sub(r"[^\w\sáéíóúÁÉÍÓÚñÑüÜ-]", ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def merge_data(base_data, fallback_data):
    if not base_data:
        return fallback_data
    if not fallback_data:
        return base_data

    resolved_title = base_data.get('title') or fallback_data.get('title')
    resolved_description = base_data.get('description') or fallback_data.get('description') or ''
    resolved_image_url = base_data.get('image_url') or fallback_data.get('image_url') or ''

    return {
        'title': resolved_title,
        'description': resolved_description,
        'image_url': resolved_image_url,
    }


def search_openlibrary_data(title):
    clean_text = normalize_title(title)
    if not clean_text:
        return None

    url = f"https://openlibrary.org/search.json?title={quote_plus(clean_text)}&limit=1"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        return None

    docs = data.get('docs', [])
    if not docs:
        return None

    doc = docs[0]
    description = ''
    if isinstance(doc.get('first_sentence'), list):
        description = ' '.join(doc.get('first_sentence', [])).strip()
    elif isinstance(doc.get('first_sentence'), str):
        description = doc.get('first_sentence').strip()
    elif isinstance(doc.get('subtitle'), str):
        description = doc.get('subtitle').strip()

    image_url = ''
    if doc.get('cover_i'):
        image_url = f"https://covers.openlibrary.org/b/id/{doc.get('cover_i')}-L.jpg"
    elif doc.get('cover_edition_key'):
        image_url = f"https://covers.openlibrary.org/b/olid/{doc.get('cover_edition_key')}-L.jpg"

    resolved_title = doc.get('title_suggest') or doc.get('title') or title
    return {
        'title': resolved_title,
        'description': description,
        'image_url': image_url,
    }


def search_google_books_data(title):
    clean_text = normalize_title(title)
    if not clean_text:
        return None

    url = f"https://www.googleapis.com/books/v1/volumes?q={quote_plus(clean_text)}&langRestrict=es&maxResults=5"
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

        description = info.get('description', '') or ''
        image_url = ''
        image_links = info.get('imageLinks', {})
        if image_links.get('thumbnail'):
            image_url = image_links.get('thumbnail').replace('http://', 'https://')
        elif image_links.get('smallThumbnail'):
            image_url = image_links.get('smallThumbnail').replace('http://', 'https://')

        resolved_title = info.get('title') or title
        return {
            'title': resolved_title,
            'description': description,
            'image_url': image_url,
        }

    return None


def search_omdb_data(title, item_type):
    api_key = os.getenv('OMDB_API_KEY', '').strip()
    if not api_key:
        return None

    search_type = 'series' if item_type == 'serie' else 'movie'
    url = f"http://www.omdbapi.com/?apikey={quote_plus(api_key)}&t={quote_plus(title)}&type={quote_plus(search_type)}&plot=short&r=json"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        return None

    if data.get('Response') != 'True':
        return None

    description = data.get('Plot', '')
    if description == 'N/A':
        description = ''

    image_url = data.get('Poster', '')
    if image_url == 'N/A':
        image_url = ''

    resolved_title = data.get('Title', title)
    return {
        'title': resolved_title,
        'description': description,
        'image_url': image_url,
    }


def search_tmdb_data(title, item_type):
    api_key = os.getenv('TMDB_API_KEY', '').strip()
    if not api_key:
        return None

    media_type = 'tv' if item_type == 'serie' else 'movie'
    search_url = f"https://api.themoviedb.org/3/search/{media_type}?api_key={quote_plus(api_key)}&query={quote_plus(title)}&language=es-ES&page=1"
    try:
        with urllib.request.urlopen(search_url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        return None

    results = data.get('results', [])
    if not results:
        return None

    item = results[0]
    description = item.get('overview', '') or ''
    image_url = ''
    poster_path = item.get('poster_path')
    if poster_path:
        image_url = f"https://image.tmdb.org/t/p/w500{poster_path}"

    resolved_title = item.get('name') or item.get('title') or title
    return {
        'title': resolved_title,
        'description': description,
        'image_url': image_url,
    }


def search_itunes_data(title, item_type):
    clean_text = normalize_title(title)
    if not clean_text:
        return None

    media = 'tvShow' if item_type == 'serie' else 'movie'
    url = f"https://itunes.apple.com/search?term={quote_plus(clean_text)}&media={quote_plus(media)}&limit=1"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError):
        return None

    items = data.get('results', [])
    if not items:
        return None

    item = items[0]
    description = item.get('longDescription') or item.get('shortDescription') or ''
    image_url = item.get('artworkUrl100', '')
    if image_url:
        image_url = image_url.replace('100x100bb', '600x600bb').replace('100x100', '600x600')

    itunes_title = item.get('trackName') or item.get('collectionName') or title
    return {
        'title': itunes_title,
        'description': description,
        'image_url': image_url,
    }


def search_external_data(item_type, title):
    if item_type == 'libro':
        data_ol = search_openlibrary_data(title)
        data_google = search_google_books_data(title)
        return merge_data(data_ol, data_google)

    data = None
    if os.getenv('OMDB_API_KEY', '').strip():
        data = search_omdb_data(title, item_type)
    if not data and os.getenv('TMDB_API_KEY', '').strip():
        data = search_tmdb_data(title, item_type)
    if not data:
        data = search_itunes_data(title, item_type)

    return data


def save_element(user_id, payload):
    success = Element.save(
        title=payload['title'],
        element_type=payload['element_type'],
        author_director=payload['author_director'],
        genre=payload['genre'],
        description=payload['description'],
        rating=payload['rating'],
        review=payload['review'],
        image_url=payload['image_url'],
        user_id=user_id,
    )

    if success:
        return True, None
    return False, 'Error interno al guardar el elemento'


def edit_element(session, payload):
    title = payload['title']
    user_id = session.get('user_id') or session.get('usuario_id')
    user_role = session.get('role') or session.get('rol', 'USER') or 'USER'

    success = Element.update(
        element_id=payload['id'],
        title=title,
        element_type=payload['element_type'],
        author_director=payload['author_director'],
        genre=payload['genre'],
        description=payload['description'],
        rating=payload['rating'],
        review=payload['review'],
        image_url=payload['image_url'],
        user_id=user_id,
        user_role=user_role
    )

    if success:
        user = User(
            id=user_id,
            username=session.get('username', ''),
            name=session.get('name') or session.get('nombre', ''),
            password='',
            role=user_role
        )
        Log.save_log(user, f"Editó el elemento '{title}'", LogType.EDIT)
        return True, None

    return False, 'No autorizado o no se encontró el elemento'


def delete_element(session, element_id):
    user_id = session.get('user_id') or session.get('usuario_id')
    user_role = session.get('role') or session.get('rol', 'USER') or 'USER'

    success = Element.delete(
        element_id=element_id,
        user_id=user_id,
        user_role=user_role
    )

    if success:
        user = User(
            id=user_id,
            username=session.get('username', ''),
            name=session.get('name') or session.get('nombre', ''),
            password='',
            role=user_role
        )
        Log.save_log(user, f'Eliminó el elemento con ID {element_id}', LogType.DELETE)
        return True, None

    return False, 'No autorizado o no se encontró el elemento'


def toggle_like(session, element_id):
    user_id = session.get('user_id') or session.get('usuario_id')
    if not user_id:
        return False, 'No hay sesión activa', 401

    result = Element.toggle_like(user_id, element_id)
    if result is None:
        return False, 'Elemento no encontrado o error interno', 404

    return True, {
        'liked': result['liked'],
        'total_likes': result['total_likes'],
    }, 200


def toggle_follow(session, user_id):
    follower_id = session.get('user_id') or session.get('usuario_id')
    if not follower_id:
        return False, 'No hay sesión activa', 401

    if follower_id == user_id:
        return False, 'No puedes seguirte a ti mismo.', 400

    try:
        connection = get_connection()
        cursor = connection.cursor(DictCursor)

        cursor.execute('SELECT id FROM usuarios WHERE id = %s', (user_id,))
        if not cursor.fetchone():
            cursor.close(); connection.close()
            return False, 'Usuario no encontrado.', 404

        cursor.execute(
            'SELECT id FROM seguidores WHERE seguidor_id = %s AND seguido_id = %s',
            (follower_id, user_id)
        )
        already_follows = cursor.fetchone()

        if already_follows:
            cursor.execute(
                'DELETE FROM seguidores WHERE seguidor_id = %s AND seguido_id = %s',
                (follower_id, user_id)
            )
            following = False
            description = f'Dejó de seguir al usuario ID {user_id}'
            log_type = LogType.UNFOLLOW
        else:
            cursor.execute(
                'INSERT INTO seguidores (seguidor_id, seguido_id, fecha) VALUES (%s, %s, NOW())',
                (follower_id, user_id)
            )
            following = True
            description = f'Comenzó a seguir al usuario ID {user_id}'
            log_type = LogType.FOLLOW

        connection.commit()
        cursor.execute('SELECT COUNT(*) AS total FROM seguidores WHERE seguido_id = %s', (user_id,))
        total_followers = int(cursor.fetchone()['total'] or 0)

        user = User(
            id=follower_id,
            username=session.get('username', ''),
            name=session.get('name') or session.get('nombre', ''),
            password='',
            role=(session.get('role') or session.get('rol', 'USER') or 'USER')
        )
        Log.save_log(user, description, log_type)

        cursor.close(); connection.close()
        return True, {
            'siguiendo': following,
            'following': following,
            'total_seguidores': total_followers,
            'total_followers': total_followers
        }, 200
    except Exception as ex:
        print(f'Error al alternar seguimiento: {ex}')
        return False, 'No se pudo actualizar el seguimiento.', 500
