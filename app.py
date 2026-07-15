import os
from flask import Flask, redirect, render_template, jsonify, request, session, url_for
from dotenv import load_dotenv
from entities.elemento import Elemento
from entities.log import Log
from entities.usuario import User
from enums.log_type import LogType



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
    coleccion_completa = Elemento.obtener_todos() 
    return render_template('index.html', elementos=coleccion_completa)



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


@app.route('/api/guardar', methods=['POST'])
def api_guardar_elemento():
    data = request.json
    # Obtenemos el ID de quien tiene la sesión abierta
    usuario_id = session.get('usuario_id')
    exito = Elemento.save(
        titulo=data['titulo'],
        tipo=data['tipo'],
        autor_director=data['autor_director'],
        descripcion=data['descripcion'],
        calificacion=int(data['calificacion']),
        opinion=data['opinion'],
        usuario_id=usuario_id
    )
    return jsonify({'success': exito})


@app.route('/api/editar', methods=['POST'])
def api_editar_elemento():
    data = request.json
    exito = Elemento.update(
        id_elemento=int(data['id']),
        titulo=data['titulo'],
        tipo=data['tipo'],
        autor_director=data['autor_director'],
        descripcion=data['descripcion'],
        calificacion=int(data['calificacion']),
        opinion=data['opinion']
    )
    return jsonify({'success': exito})


@app.route('/api/borrar/<int:elemento_id>', methods=['DELETE'])
def api_borrar_elemento(elemento_id):
    exito = Elemento.delete(elemento_id)
    return jsonify({'success': exito})


@app.route('/api/elemento/<int:elemento_id>')
def api_obtener_elemento_por_id(elemento_id):
    el = Elemento.obtener_por_id(elemento_id)
    if el:
        # Retornamos las propiedades como JSON para rellenar los inputs al editar
        return jsonify({
            'id': el.id, 'titulo': el.titulo, 'tipo': el.tipo,
            'autor_director': el.autor_director, 'descripcion': el.descripcion,
            'calificacion': el.calificacion, 'opinion': el.opinion
        })
    return jsonify({"error": "No encontrado"}), 404



# Ejecutar la aplicación Flask
if __name__ == '__main__':
    app.run()
