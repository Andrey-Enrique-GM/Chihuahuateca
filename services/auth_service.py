from entities.log import Log
from entities.usuario import User
from enums.log_type import LogType


def get_usuario_sesion(session):
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return None

    return User(
        id=usuario_id,
        username=session.get('username', ''),
        nombre=session.get('nombre', ''),
        password='',
        rol=(session.get('rol', 'USER') or 'USER')
    )


def login_usuario(session, data):
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return False, 'Faltan datos', 400

    usuario = User.authenticate(username, password)
    if not usuario:
        return False, 'Usuario o contraseña incorrectos', 401

    session['usuario_id'] = usuario.id
    session['user_id'] = usuario.id
    session['username'] = usuario.username
    session['nombre'] = usuario.nombre
    session['rol'] = usuario.rol.upper()

    Log.save_log(usuario, 'Inicio de sesión', LogType.LOGIN)
    return True, {'redirect': '/coleccion'}, 200


def logout_usuario(session):
    usuario = get_usuario_sesion(session)
    if usuario:
        try:
            Log.save_log(usuario, 'Cierre de sesión', LogType.LOGOUT)
        except Exception:
            pass

    session.clear()


def registrar_usuario(data):
    nombre = (data.get('name') or '').strip()
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    confirm_password = (data.get('confirm_password') or '').strip()

    if not nombre or not username or not password:
        return False, 'Todos los campos son obligatorios', 400

    if password != confirm_password:
        return False, 'Las contraseñas no coinciden', 400

    exito, mensaje = User.create(nombre, username, password, rol='USER')
    if exito:
        return True, '¡Cuenta creada con éxito! Ahora puedes iniciar sesión.', 200

    if mensaje and 'ocupado' in mensaje.lower():
        return False, mensaje, 409

    return False, mensaje or 'Error al crear la cuenta', 500


def cambiar_password_usuario(session, data):
    usuario_id = session.get('usuario_id')
    if not usuario_id:
        return False, 'Sesión no válida o expirada.', 401

    pass_actual = (data.get('pass_actual') or '').strip()
    pass_nueva = (data.get('pass_nueva') or '').strip()

    if not pass_actual or not pass_nueva:
        return False, 'Todos los campos son obligatorios.', 400

    username_actual = session.get('username')
    usuario_validado = User.authenticate(username_actual, pass_actual)
    if not usuario_validado:
        return False, 'La contraseña actual es incorrecta.', 401

    exito, mensaje = User.update_password(usuario_id, pass_nueva)
    if exito:
        usuario = get_usuario_sesion(session)
        Log.save_log(usuario, 'El usuario cambió su contraseña', LogType.EDIT)
        return True, 'Tu contraseña ha sido actualizada con éxito.', 200

    return False, mensaje or 'Error interno al actualizar la contraseña.', 500
