import os
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from dotenv import load_dotenv
from pymysql.cursors import DictCursor

from entities.element import Element
from entities.log import Log
from entities.notification import Notification
from entities.user import User
from enums.log_type import LogType
from enums.notification_type import NotificationType
from persistence.db import get_connection
from services.auth_service import (
    change_user_password,
    get_user_session,
    login_user,
    logout_user,
    register_user,
)
from services.element_service import (
    delete_element,
    edit_element,
    normalize_title,
    save_element,
    search_external_data,
    toggle_follow,
    toggle_like,
    validate_element_payload,
)
from services.pdf_service import export_collection_pdf



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
    user_id = session.get('user_id') or session.get('usuario_id')
    if not user_id:
        return redirect(url_for('login_view'))
    full_collection = Element.get_all(user_id=user_id)
    return render_template('index.html', elements=full_collection)


@app.route('/profile', endpoint='profile')
def profile_route():
    user_id = session.get('user_id') or session.get('usuario_id')
    if not user_id:
        return redirect(url_for('login_view'))

    user = User.get_by_id(user_id)
    if user:
        session['timezone'] = getattr(user, 'timezone', 'AUTO') or 'AUTO'
        session['zona_horaria'] = session['timezone']
    # Obtenemos sus logs recientes para mostrar actividad
    activity = Log.get_by_user(user_id)
    
    # Calculo de estadisticas del usuario
    all_elements = Element.get_all()
    # Filtrar solo los aportes creados por el usuario actual
    my_elements = [e for e in all_elements if e.user_id == user_id]
    
    total_contributions = len(my_elements)
    total_books = sum(1 for e in my_elements if e.element_type == 'libro')
    total_movies = sum(1 for e in my_elements if e.element_type == 'pelicula')
    total_series = sum(1 for e in my_elements if e.element_type == 'serie')
    total_likes_received = sum(e.total_likes for e in my_elements)
    
    # Promedio de calificacion dada por el usuario
    if total_contributions > 0:
        average_rating = round(sum(e.rating for e in my_elements) / total_contributions, 1)
    else:
        average_rating = 0.0

    try:
        connection = get_connection()
        cursor = connection.cursor(DictCursor)
        cursor.execute("SELECT COUNT(*) AS total FROM seguidores WHERE seguido_id = %s", (user_id,))
        followers = int(cursor.fetchone()['total'] or 0)
        cursor.execute("SELECT COUNT(*) AS total FROM seguidores WHERE seguidor_id = %s", (user_id,))
        following = int(cursor.fetchone()['total'] or 0)
        cursor.close(); connection.close()
    except Exception as ex:
        print(f"Error al consultar estadísticas sociales: {ex}")
        followers = 0
        following = 0

    statistics = {
        'total': total_contributions,
        'books': total_books,
        'movies': total_movies,
        'series': total_series,
        'average_rating': average_rating,
        'likes_received': total_likes_received,
        'followers': followers,
        'following': following
    }
    
    return render_template('profile.html', user=user, logs=activity, stats=statistics)


@app.route('/users', endpoint='users_view')
def users_view():
    user_id = session.get('user_id') or session.get('usuario_id')
    if not user_id:
        return redirect(url_for('login_view'))

    # Se obtiene la lista de usuarios, incluyendo su zona horaria
    users = User.get_all(user_id)
    return render_template('users.html', users=users)


@app.route('/exportar-pdf')
def export_pdf():
    user_id = session.get('user_id') or session.get('usuario_id')
    if not user_id:
        return redirect(url_for('login_view'))

    elements = Element.get_all(user_id=user_id)
    return export_collection_pdf(elements, session)



# --- RUTAS DE API ---

@app.route('/api/login', methods=['POST'])
def api_login():
    ok, result, status = login_user(session, request.get_json() or {})
    if ok:
        return jsonify({
            'success': True,
            'redirect': url_for('index'),
            'zona_horaria': session.get('timezone', 'AUTO')
        }), status
    return jsonify({'success': False, 'message': result}), status


@app.route("/logout")
def api_logout():
    logout_user(session)
    return redirect(url_for('login_view'))


@app.route('/api/signup', methods=['POST'])
def api_signup():
    ok, message, status = register_user(request.get_json() or {})
    if ok:
        return jsonify({'success': True, 'message': message}), status
    return jsonify({'success': False, 'message': message}), status


@app.route('/api/buscar-external')
def api_search_external():
    item_type = (request.args.get('tipo') or '').strip().lower()
    title = (request.args.get('titulo') or '').strip()
    normalized_title = normalize_title(title)

    if not normalized_title:
        return jsonify({'success': False, 'message': 'Debes ingresar un título válido para buscar.'}), 400
    if item_type not in ('libro', 'pelicula', 'serie'):
        return jsonify({'success': False, 'message': 'Tipo inválido para buscar datos externos.'}), 400

    data = search_external_data(item_type, normalized_title)
    if not data:
        message = 'No se pudo obtener información adicional. Verifica que el título exista o prueba con una versión alternativa del título.'
        return jsonify({'success': False, 'message': message}), 404

    try:
        user_id = session.get('user_id') or session.get('usuario_id')
        if user_id:
            user = get_user_session(session)
            Log.save_log(user, f"Búsqueda automática de portada/sinopsis para: {title}", LogType.AUTOCOMPLETE_QUERY)
    except Exception:
        pass

    return jsonify({
        'success': True,
        'titulo': data.get('title') or title,
        'descripcion': data.get('description') or None,
        'imagen_url': data.get('image_url') or None,
    })


@app.route('/api/guardar', methods=['POST'])
def api_save_element():
    user_id = session.get('user_id') or session.get('usuario_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'No hay sesión activa'}), 401

    success, message, payload = validate_element_payload(request.json or {})
    if not success:
        return jsonify({'success': False, 'message': message}), 400

    saved, error = save_element(user_id, payload)
    if saved:
        user = get_user_session(session)
        element_title = payload['title']
        Log.save_log(user, f"Guardó el elemento '{element_title}'", LogType.SAVE)
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': error}), 500


@app.route('/api/editar', methods=['POST'])
def api_edit_element():
    if 'user_id' not in session and 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No hay sesión activa'}), 401

    success, message, payload = validate_element_payload(request.json or {}, require_id=True)
    if not success:
        return jsonify({'success': False, 'message': message}), 400

    edited, error = edit_element(session, payload)
    if edited:
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': error}), 403


@app.route('/api/borrar/<int:elemento_id>', methods=['DELETE'])
def api_delete_element(elemento_id):
    if 'user_id' not in session and 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No hay sesión activa'}), 401

    deleted, error = delete_element(session, elemento_id)
    if deleted:
        return jsonify({'success': True})

    return jsonify({'success': False, 'message': error}), 403


@app.route('/api/like/<int:elemento_id>', methods=['POST'])
def api_toggle_like(elemento_id):
    ok, result, status = toggle_like(session, elemento_id)
    if not ok:
        return jsonify({'success': False, 'message': result}), status

    if result.get('liked'):
        element = Element.get_by_id(elemento_id)
        current_user = User.get_by_id(session.get('user_id') or session.get('usuario_id'))
        if element and current_user and element.user_id != (session.get('user_id') or session.get('usuario_id')):
            Notification.create_from_event(
                user_id=element.user_id,
                sender_id=current_user.id,
                notification_type=NotificationType.LIKE,
                reference_id=element.id,
                reference_title=element.title,
                sender_username=current_user.username,
            )

    return jsonify({'success': True, 'liked': result['liked'], 'total_likes': result['total_likes']})


@app.route('/api/seguir/<int:usuario_id>', methods=['POST'])
def api_follow_user(usuario_id):
    ok, result, status = toggle_follow(session, usuario_id)
    if not ok:
        return jsonify({'success': False, 'message': result}), status

    if result.get('siguiendo'):
        sender = User.get_by_id(session.get('user_id') or session.get('usuario_id'))
        if sender:
            Notification.create_from_event(
                user_id=usuario_id,
                sender_id=sender.id,
                notification_type=NotificationType.FOLLOW,
                reference_id=sender.id,
                reference_title=None,
                sender_username=sender.username,
            )

    return jsonify({'success': True, **result})


@app.route('/api/comentario/<int:elemento_id>', methods=['POST'])
def api_comment_element(elemento_id):
    user_id = session.get('user_id') or session.get('usuario_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'No hay sesión activa'}), 401

    payload = request.get_json(silent=True) or request.form or {}
    comment = (payload.get('comentario') or payload.get('comment') or '').strip()
    if not comment:
        return jsonify({'success': False, 'message': 'El comentario no puede estar vacío.'}), 400

    element = Element.get_by_id(elemento_id)
    if not element:
        return jsonify({'success': False, 'message': 'Elemento no encontrado'}), 404

    sender = User.get_by_id(user_id)
    if sender and element.user_id != user_id:
        Notification.create_from_event(
            user_id=element.user_id,
            sender_id=sender.id,
            notification_type=NotificationType.COMMENT,
            reference_id=element.id,
            reference_title=element.title,
            sender_username=sender.username,
        )

    return jsonify({'success': True, 'message': 'Comentario registrado.'})


@app.route('/api/notificaciones')
def api_notifications():
    Notification.ensure_structure()
    user_id = session.get('user_id') or session.get('usuario_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'No hay sesión activa'}), 401

    items = Notification.list_for_user(user_id, limit=20)
    payload = []
    for item in items:
        item_type = int(item.get('tipo', 0) or 0)
        sender_username = item.get('emisor_username') or 'Alguien'
        reference_title = item.get('titulo_referencia')
        message = NotificationType.build_message(item_type, sender_username, reference_title)
        payload.append({
            'id': item.get('id'),
            'tipo': item_type,
            'mensaje': message,
            'leido': bool(item.get('leido', 0)),
            'fecha': item.get('fecha').strftime('%Y-%m-%d %H:%M:%S') if item.get('fecha') else None,
            'emisor': {
                'id': item.get('emisor_id'),
                'username': sender_username,
                'nombre': item.get('emisor_nombre')
            },
            'titulo_referencia': reference_title,
            'referencia_id': item.get('referencia_id'),
            'icono': {
                NotificationType.LIKE: '❤️',
                NotificationType.FOLLOW: '👤',
                NotificationType.COMMENT: '💬'
            }.get(NotificationType(item_type), '🔔'),
            'link': f"/coleccion#{item.get('referencia_id') or 'notificacion'}"
        })

    return jsonify({
        'success': True,
        'items': payload,
        'unread_count': Notification.unread_count(user_id),
    })


@app.route('/api/notificaciones/marcar-leidas', methods=['POST'])
def api_mark_notifications_read():
    user_id = session.get('user_id') or session.get('usuario_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'No hay sesión activa'}), 401

    data = request.get_json(silent=True) or {}
    notification_id = data.get('notificacion_id') or data.get('notification_id')
    Notification.mark_as_read(user_id, notification_id)
    return jsonify({
        'success': True,
        'unread_count': Notification.unread_count(user_id)
    })


@app.route('/api/elemento/<int:elemento_id>')
def api_get_element_by_id(elemento_id):
    el = Element.get_by_id(elemento_id)
    if el:
        # Retornamos las propiedades como JSON para rellenar los inputs al editar
        return jsonify({
            'id': el.id,
            'titulo': el.title,
            'tipo': el.element_type,
            'autor_director': el.author_director,
            'genero': el.genre,
            'descripcion': el.description,
            'calificacion': el.rating,
            'opinion': el.review,
            'imagen_url': el.image_url
        })
    return jsonify({"error": "No encontrado"}), 404


@app.route('/api/usuario/cambiar-password', methods=['POST'])
def api_change_password():
    ok, message, status = change_user_password(session, request.get_json() or {})
    if ok:
        return jsonify({'success': True, 'message': message}), status
    return jsonify({'success': False, 'message': message}), status


@app.route('/api/ajustes/zona-horaria', methods=['POST'])
def api_update_timezone():
    user_id = session.get('user_id') or session.get('usuario_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'No hay sesión activa'}), 401

    payload = request.get_json(silent=True) or {}
    new_timezone = str(payload.get('zona_horaria') or payload.get('timezone') or '').strip()
    allowed_values = {'AUTO', '-7', '-6', '-5', '0', '-4', '-3', '-2', '-1', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'}

    if new_timezone not in allowed_values:
        return jsonify({'success': False, 'message': 'Zona horaria inválida'}), 400

    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute('UPDATE usuarios SET zona_horaria = %s WHERE id = %s', (new_timezone, user_id))
        connection.commit()
        cursor.close()
        connection.close()
    except Exception as ex:
        print(f'Error al actualizar zona horaria: {ex}')
        return jsonify({'success': False, 'message': 'No se pudo guardar la zona horaria'}), 500

    session['timezone'] = new_timezone
    session['zona_horaria'] = new_timezone
    user = get_user_session(session)
    if user:
        Log.save_log(user, f"Actualizó preferencia de zona horaria a {new_timezone}", LogType.EDIT)

    return jsonify({'success': True, 'message': 'Zona horaria actualizada correctamente'})


@app.template_filter('formato_fecha')
def date_format_filter(val):
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
