import os
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from dotenv import load_dotenv
from pymysql.cursors import DictCursor

from entities.elemento import Elemento
from entities.log import Log
from entities.usuario import User
from enums.log_type import LogType
from persistence.db import get_connection
from services.auth_service import cambiar_password_usuario, get_usuario_sesion, login_usuario, logout_usuario, registrar_usuario
from services.elemento_service import (
    alternar_like,
    alternar_seguimiento,
    borrar_elemento,
    buscar_datos_externos,
    editar_elemento,
    guardar_elemento,
    normalizar_titulo,
    validate_elemento_payload,
)
from services.pdf_service import exportar_coleccion_pdf



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

    try:
        conexion = get_connection()
        cursor = conexion.cursor(DictCursor)
        cursor.execute("SELECT COUNT(*) AS total FROM seguidores WHERE seguido_id = %s", (usuario_id,))
        seguidores = int(cursor.fetchone()['total'] or 0)
        cursor.execute("SELECT COUNT(*) AS total FROM seguidores WHERE seguidor_id = %s", (usuario_id,))
        siguiendo = int(cursor.fetchone()['total'] or 0)
        cursor.close(); conexion.close()
    except Exception as ex:
        print(f"Error al consultar estadísticas sociales: {ex}")
        seguidores = 0
        siguiendo = 0

    estadisticas = {
        'total': total_aportes,
        'libros': total_libros,
        'peliculas': total_peliculas,
        'series': total_series,
        'promedio_nota': promedio_calificacion,
        'likes_recibidos': total_likes_recibidos,
        'seguidores': seguidores,
        'siguiendo': siguiendo
    }
    
    return render_template('profile.html', usuario=usuario, logs=actividad, stats=estadisticas)


@app.route('/exportar-pdf')
def exportar_pdf():
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return redirect(url_for('login_view'))

    elementos = Elemento.obtener_todos(usuario_id=usuario_id)
    return exportar_coleccion_pdf(elementos, session)



# --- RUTAS DE API ---

@app.route('/api/login', methods=['POST'])
def api_login():
    ok, result, status = login_usuario(session, request.get_json() or {})
    if ok:
        return jsonify({'success': True, 'redirect': url_for('index')}), status
    return jsonify({'success': False, 'message': result}), status


@app.route("/logout")
def api_logout():
    logout_usuario(session)
    return redirect(url_for('login_view'))


@app.route('/api/signup', methods=['POST'])
def api_signup():
    ok, message, status = registrar_usuario(request.get_json() or {})
    if ok:
        return jsonify({'success': True, 'message': message}), status
    return jsonify({'success': False, 'message': message}), status




@app.route('/api/buscar-external')
def api_buscar_externos():
    tipo = (request.args.get('tipo') or '').strip().lower()
    titulo = (request.args.get('titulo') or '').strip()
    titulo_normalizado = normalizar_titulo(titulo)

    if not titulo_normalizado:
        return jsonify({'success': False, 'message': 'Debes ingresar un título válido para buscar.'}), 400
    if tipo not in ('libro', 'pelicula', 'serie'):
        return jsonify({'success': False, 'message': 'Tipo inválido para buscar datos externos.'}), 400

    datos = buscar_datos_externos(tipo, titulo_normalizado)
    if not datos:
        mensaje = 'No se pudo obtener información adicional. Verifica que el título exista o prueba con una versión alternativa del título.'
        return jsonify({'success': False, 'message': mensaje}), 404

    try:
        usuario_id = session.get('usuario_id')
        if usuario_id:
            usuario = get_usuario_sesion(session)
            Log.save_log(usuario, f"Búsqueda automática de portada/sinopsis para: {titulo}", LogType.AUTOCOMPLETE_QUERY)
    except Exception:
        pass

    return jsonify({
        'success': True,
        'titulo': datos.get('titulo') or titulo,
        'descripcion': datos.get('descripcion') or None,
        'imagen_url': datos.get('imagen_url') or None,
    })


@app.route('/api/guardar', methods=['POST'])
def api_guardar_elemento():
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return jsonify({'success': False, 'message': 'No hay sesión activa'}), 401

    success, message, payload = validate_elemento_payload(request.json or {})
    if not success:
        return jsonify({'success': False, 'message': message}), 400

    exito, error = guardar_elemento(usuario_id, payload)
    if exito:
        usuario = get_usuario_sesion(session)
        Log.save_log(usuario, f"Guardó el elemento '{payload['titulo']}'", LogType.SAVE)
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': error}), 500


@app.route('/api/editar', methods=['POST'])
def api_editar_elemento():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No hay sesión activa'}), 401

    success, message, payload = validate_elemento_payload(request.json or {}, require_id=True)
    if not success:
        return jsonify({'success': False, 'message': message}), 400

    exito, error = editar_elemento(session, payload)
    if exito:
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': error}), 403


@app.route('/api/borrar/<int:elemento_id>', methods=['DELETE'])
def api_borrar_elemento(elemento_id):
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No hay sesión activa'}), 401

    exito, error = borrar_elemento(session, elemento_id)
    if exito:
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': error}), 403


@app.route('/api/like/<int:elemento_id>', methods=['POST'])
def api_toggle_like(elemento_id):
    ok, result, status = alternar_like(session, elemento_id)
    if not ok:
        return jsonify({'success': False, 'message': result}), status

    return jsonify({'success': True, 'liked': result['liked'], 'total_likes': result['total_likes']})


@app.route('/api/seguir/<int:usuario_id>', methods=['POST'])
def api_seguir_usuario(usuario_id):
    ok, result, status = alternar_seguimiento(session, usuario_id)
    if not ok:
        return jsonify({'success': False, 'message': result}), status

    return jsonify({'success': True, **result})


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
    ok, message, status = cambiar_password_usuario(session, request.get_json() or {})
    if ok:
        return jsonify({'success': True, 'message': message}), status
    return jsonify({'success': False, 'message': message}), status


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
