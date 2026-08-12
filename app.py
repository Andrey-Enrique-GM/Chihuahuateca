import os
import json
import urllib.error
import urllib.request
from flask import Flask, redirect, render_template, jsonify, request, session, url_for
from dotenv import load_dotenv
from entities.elemento import Elemento
from entities.log import Log
from entities.usuario import User
from enums.log_type import LogType
from datetime import datetime
from urllib.parse import quote_plus, urlparse



# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configuración de la aplicación Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")



# --- RUTAS DE NAVEGACION ---

@app.route('/')
def login_view():
    return render_template('login.html')


@app.route('/signup')
def signup_view():
    return render_template('signup.html')


@app.route('/coleccion')
def index():
    # Si no hay un usuario en la sesión, lo mandamos al login de vuelta
    if 'usuario_id' not in session:
        return redirect(url_for('login_view'))
    coleccion_completa = Elemento.obtener_todos(usuario_id=session['usuario_id'])
    return render_template('index.html', elementos=coleccion_completa)


@app.route('/profile', endpoint='profile')
def ruta_perfil():
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return redirect(url_for('login_view'))
    
    usuario = User.get_by_id(usuario_id)
    # Obtenemos sus logs recientes para mostrar actividad
    actividad = Log.get_by_user(usuario_id)
    
    # Calculo de estadisticas del usuario
    todos_elementos = Elemento.obtener_todos()
    # Filtrar solo los aportes creados por el usuario actual
    mis_elementos = [e for e in todos_elementos if getattr(e, 'usuario_id', None) == usuario_id]
    
    total_aportes = len(mis_elementos)
    total_libros = sum(1 for e in mis_elementos if e.tipo == 'libro')
    total_peliculas = sum(1 for e in mis_elementos if e.tipo == 'pelicula')
    total_series = sum(1 for e in mis_elementos if e.tipo == 'serie')
    total_likes_recibidos = sum(e.total_likes for e in mis_elementos)
    
    # Promedio de calificacion dada por el usuario
    if total_aportes > 0:
        promedio_calificacion = round(sum(e.calificacion for e in mis_elementos) / total_aportes, 1)
    else:
        promedio_calificacion = 0.0

    estadisticas = {
        'total': total_aportes,
        'libros': total_libros,
        'peliculas': total_peliculas,
        'series': total_series,
        'promedio_nota': promedio_calificacion,
        'likes_recibidos': total_likes_recibidos
    }
    
    return render_template('profile.html', usuario=usuario, logs=actividad, stats=estadisticas)



# --- RUTAS DE API ---

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'success': False, 'message': 'Faltan datos'}), 400

    usuario = User.authenticate(username, password)

    if usuario:
        session['usuario_id'] = usuario.id
        session['username'] = usuario.username
        session['nombre'] = usuario.nombre
        session['rol'] = usuario.rol

        Log.save_log(usuario, "Inicio de sesion", LogType.LOGIN)
        return jsonify({'success': True, 'redirect': url_for('index')})

    return jsonify({'success': False, 'message': 'Usuario o contraseña incorrectos'}), 401


@app.route("/logout")
def api_logout():
    session.clear()
    return redirect(url_for("login_view"))


@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json() or {}
    nombre = data.get('name', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    confirm_password = data.get('confirm_password', '').strip()

    # Validaciones básicas
    if not nombre or not username or not password:
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios'}), 400

    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Las contraseñas no coinciden'}), 400

    exito, mensaje = User.create(nombre, username, password)

    if exito:
        return jsonify({'success': True, 'message': '¡Cuenta creada con éxito! Ahora puedes iniciar sesión.'})

    if mensaje and 'ocupado' in mensaje.lower():
        return jsonify({'success': False, 'message': mensaje}), 409

    return jsonify({'success': False, 'message': mensaje or 'Error al crear la cuenta'}), 500


def _sanitize_text(value, required=False, max_length=255):
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


def _sanitize_url(value):
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


def _validate_elemento_payload(data, require_id=False):
    if not isinstance(data, dict):
        return False, 'Datos inválidos', None

    titulo = _sanitize_text(data.get('titulo'), required=True, max_length=200)
    tipo = _sanitize_text(data.get('tipo'), required=True, max_length=20)
    autor_director = _sanitize_text(data.get('autor_director'), required=True, max_length=150)
    genero = _sanitize_text(data.get('genero'), required=False, max_length=50) or ''
    descripcion = _sanitize_text(data.get('descripcion'), required=False, max_length=1000)
    opinion = _sanitize_text(data.get('opinion'), required=False, max_length=1000)
    imagen_url_raw = data.get('imagen_url', '')
    imagen_url = _sanitize_url(imagen_url_raw)

    if titulo is None:
        return False, 'El título es obligatorio', None
    if tipo not in ('libro', 'pelicula', 'serie'):
        return False, 'El tipo debe ser libro, pelicula o serie', None
    if autor_director is None:
        return False, 'Autor / Director / Creador es obligatorio', None

    if imagen_url_raw and imagen_url is None:
        return False, 'La URL de la imagen no es válida', None

    calificacion_raw = data.get('calificacion')
    try:
        calificacion = int(calificacion_raw)
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
        'id': elemento_id
    }


def _buscar_datos_openlibrary(titulo):
    url = f"https://openlibrary.org/search.json?title={quote_plus(titulo)}&limit=1"
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
        'imagen_url': imagen_url
    }


def _buscar_datos_omdb(titulo, tipo):
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
        'imagen_url': imagen_url
    }


def _buscar_datos_tmdb(titulo, tipo):
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
    descripcion = item.get('overview', '')
    imagen_url = ''
    poster_path = item.get('poster_path')
    if poster_path:
        imagen_url = f"https://image.tmdb.org/t/p/w500{poster_path}"

    return {
        'titulo': item.get('name') or item.get('title') or titulo,
        'descripcion': descripcion,
        'imagen_url': imagen_url
    }


def _buscar_datos_externos(tipo, titulo):
    if tipo == 'libro':
        return _buscar_datos_openlibrary(titulo)

    buscador_omdb = _buscar_datos_omdb(titulo, tipo)
    if buscador_omdb:
        return buscador_omdb

    buscador_tmdb = _buscar_datos_tmdb(titulo, tipo)
    if buscador_tmdb:
        return buscador_tmdb

    return None


@app.route('/api/buscar-external')
def api_buscar_externos():
    tipo = (request.args.get('tipo') or '').strip().lower()
    titulo = (request.args.get('titulo') or '').strip()

    if not titulo:
        return jsonify({'success': False, 'message': 'Debes ingresar un título para buscar.'}), 400
    if tipo not in ('libro', 'pelicula', 'serie'):
        return jsonify({'success': False, 'message': 'Tipo inválido para buscar datos externos.'}), 400

    datos = _buscar_datos_externos(tipo, titulo)
    if datos is None:
        mensaje = 'No se pudo obtener información adicional. Verifica que el título exista o configura OMDB_API_KEY/TMDB_API_KEY para películas y series.'
        return jsonify({'success': False, 'message': mensaje}), 404

    return jsonify({'success': True, **datos})


@app.route('/api/guardar', methods=['POST'])
def api_guardar_elemento():
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({'success': False, 'message': 'No hay sesión activa'}), 401

    success, message, payload = _validate_elemento_payload(request.json or {})
    if not success:
        return jsonify({'success': False, 'message': message}), 400

    exito = Elemento.save(
        titulo=payload['titulo'],
        tipo=payload['tipo'],
        autor_director=payload['autor_director'],
        genero=payload['genero'],
        descripcion=payload['descripcion'],
        calificacion=payload['calificacion'],
        opinion=payload['opinion'],
        imagen_url=payload['imagen_url'],
        usuario_id=usuario_id
    )

    if exito:
        usuario = User(id=usuario_id, username=session.get('username', ''), nombre=session.get('nombre', ''), password='', rol=session.get('rol', 'usuario'))
        Log.save_log(usuario, f"Guardó el elemento '{payload['titulo']}'", LogType.SAVE)
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'Error interno al guardar el elemento'}), 500


@app.route('/api/editar', methods=['POST'])
def api_editar_elemento():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No hay sesión activa'}), 401

    success, message, payload = _validate_elemento_payload(request.json or {}, require_id=True)
    if not success:
        return jsonify({'success': False, 'message': message}), 400

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
        user_role=session.get('rol', 'usuario')
    )

    if exito:
        usuario = User(id=session['usuario_id'], username=session.get('username', ''), nombre=session.get('nombre', ''), password='', rol=session.get('rol', 'usuario'))
        Log.save_log(usuario, f"Editó el elemento '{payload['titulo']}'", LogType.EDIT)
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'No autorizado o no se encontró el elemento'}), 403


@app.route('/api/borrar/<int:elemento_id>', methods=['DELETE'])
def api_borrar_elemento(elemento_id):
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No hay sesión activa'}), 401

    exito = Elemento.delete(
        id_elemento=elemento_id,
        usuario_id=session['usuario_id'],
        user_role=session.get('rol', 'usuario')
    )

    if exito:
        usuario = User(id=session['usuario_id'], username=session.get('username', ''), nombre=session.get('nombre', ''), password='', rol=session.get('rol', 'usuario'))
        Log.save_log(usuario, f"Eliminó el elemento con ID {elemento_id}", LogType.DELETE)
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'No autorizado o no se encontró el elemento'}), 403


@app.route('/api/like/<int:elemento_id>', methods=['POST'])
def api_toggle_like(elemento_id):
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({'success': False, 'message': 'No hay sesión activa'}), 401

    resultado = Elemento.toggle_like(usuario_id, elemento_id)
    if resultado is None:
        return jsonify({'success': False, 'message': 'Elemento no encontrado o error interno'}), 404

    return jsonify({
        'success': True,
        'liked': resultado['liked'],
        'total_likes': resultado['total_likes']
    })


@app.route('/api/elemento/<int:elemento_id>')
def api_obtener_elemento_por_id(elemento_id):
    el = Elemento.obtener_por_id(elemento_id)
    if el:
        # Retornamos las propiedades como JSON para rellenar los inputs al editar
        return jsonify({
            'id': el.id, 'titulo': el.titulo, 'tipo': el.tipo,
            'autor_director': el.autor_director, 'genero': getattr(el, 'genero', ''), 'descripcion': el.descripcion,
            'calificacion': el.calificacion, 'opinion': el.opinion,
            'imagen_url': getattr(el, 'imagen_url', '')
        })
    return jsonify({"error": "No encontrado"}), 404


@app.route('/api/usuario/cambiar-password', methods=['POST'])
def api_cambiar_password():
    # Asegurar que el usuario tiene sesión activa
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({'success': False, 'message': 'Sesión no válida o expirada.'}), 401

    data = request.get_json() or {}
    pass_actual = data.get('pass_actual', '').strip()
    pass_nueva = data.get('pass_nueva', '').strip()

    if not pass_actual or not pass_nueva:
        return jsonify({'success': False, 'message': 'Todos los campos son obligatorios.'}), 400

    # Usamos el username en sesión para validar que conozca su contraseña actual
    username_actual = session.get('username')
    usuario_validado = User.authenticate(username_actual, pass_actual)

    if not usuario_validado:
        return jsonify({'success': False, 'message': 'La contraseña actual es incorrecta.'}), 401

    # Guardar la nueva contraseña. 
    exito, mensaje = User.update_password(usuario_id, pass_nueva)

    if exito:
        usuario = User(id=usuario_id, username=username_actual, nombre=session.get('nombre', ''), password='', rol=session.get('rol', 'usuario'))
        Log.save_log(usuario, "El usuario cambió su contraseña de seguridad", LogType.EDIT)
        return jsonify({'success': True, 'message': 'Tu contraseña ha sido actualizada con éxito.'})
    
    return jsonify({'success': False, 'message': mensaje or 'Error interno al actualizar la contraseña.'}), 500


@app.template_filter('formato_fecha')
def formato_fecha_filter(val):
    if not val:
        return ""
    
    # Si la fecha viene como string desde la BD, la convierte a objeto datetime
    if isinstance(val, str):
        try:
            val = datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                val = datetime.strptime(val, "%Y-%m-%d")
            except ValueError:
                return val

    return val.strftime("%d/%m/%Y a las %I:%M %p")



# Ejecutar la aplicación Flask
if __name__ == '__main__':
    app.run()
