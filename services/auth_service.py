from entities.log import Log
from entities.user import User
from enums.log_type import LogType


def get_user_session(session):
    user_id = session.get('user_id') or session.get('usuario_id')
    if not user_id:
        return None

    return User(
        id=user_id,
        username=session.get('username', ''),
        name=session.get('name') or session.get('nombre', ''),
        password='',
        role=(session.get('role') or session.get('rol', 'USER') or 'USER'),
        timezone=(session.get('timezone') or session.get('zona_horaria') or 'AUTO')
    )


def login_user(session, data):
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return False, 'Faltan datos', 400

    user = User.authenticate(username, password)
    if not user:
        return False, 'Usuario o contraseña incorrectos', 401

    session['user_id'] = user.id
    session['usuario_id'] = user.id
    session['username'] = user.username
    session['name'] = user.name
    session['nombre'] = user.name
    session['role'] = user.role.upper()
    session['rol'] = user.role.upper()
    session['timezone'] = user.timezone if getattr(user, 'timezone', None) else 'AUTO'
    session['zona_horaria'] = session['timezone']

    Log.save_log(user, 'Inicio de sesión', LogType.LOGIN)
    return True, {'redirect': '/coleccion'}, 200


def logout_user(session):
    user = get_user_session(session)
    if user:
        try:
            Log.save_log(user, 'Cierre de sesión', LogType.LOGOUT)
        except Exception:
            pass

    session.clear()


def register_user(data):
    name = (data.get('name') or '').strip()
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    confirm_password = (data.get('confirm_password') or '').strip()

    if not name or not username or not password:
        return False, 'Todos los campos son obligatorios', 400

    if password != confirm_password:
        return False, 'Las contraseñas no coinciden', 400

    success, message = User.create(name=name, username=username, password=password, role='USER')
    if success:
        return True, '¡Cuenta creada con éxito! Ahora puedes iniciar sesión.', 200

    if message and 'ocupado' in message.lower():
        return False, message, 409

    return False, message or 'Error al crear la cuenta', 500


def change_user_password(session, data):
    user_id = session.get('user_id') or session.get('usuario_id')
    if not user_id:
        return False, 'Sesión no válida o expirada.', 401

    current_password = (data.get('pass_actual') or '').strip()
    new_password = (data.get('pass_nueva') or '').strip()

    if not current_password or not new_password:
        return False, 'Todos los campos son obligatorios.', 400

    current_username = session.get('username')
    validated_user = User.authenticate(current_username, current_password)
    if not validated_user:
        return False, 'La contraseña actual es incorrecta.', 401

    success, message = User.update_password(user_id=user_id, new_password=new_password)
    if success:
        user = get_user_session(session)
        Log.save_log(user, 'El usuario cambió su contraseña', LogType.EDIT)
        return True, 'Tu contraseña ha sido actualizada con éxito.', 200

    return False, message or 'Error interno al actualizar la contraseña.', 500
