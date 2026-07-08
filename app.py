import os
import pymysql
from flask import Flask, redirect, render_template, jsonify, request, session, url_for
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from entities.elemento import Elemento



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
    # Recibir datos del formulario tradicional (POST)
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        return "Faltan datos", 400

    conexion = None
    try:
        # Conexión rápida a la BD utilizando tus variables de entorno
        conexion = pymysql.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 24316)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            ssl={'ssl': {}}
        )
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        
        # Buscamos al usuario por su username
        sql = "SELECT id, username, password, rol FROM usuarios WHERE username = %s"
        cursor.execute(sql, (username,))
        usuario = cursor.fetchone()

        # Si el usuario existe y la contraseña coincide con el hash encriptado
        if usuario and check_password_hash(usuario['password'], password):
            # Guardamos los datos clave en la sesión de Flask
            session['usuario_id'] = usuario['id']
            session['username'] = usuario['username']
            session['rol'] = usuario['rol']
            
            # Login exitoso, redirigimos a la vista de la colección
            return redirect(url_for('index'))
        else:
            # Si los datos no coinciden, mandamos un mensaje simple por ahora
            return "Usuario o contraseña incorrectos. <a href='/'>Volver a intentar</a>", 401

    except Exception as ex:
        return f"Error en el servidor: {ex}", 500
    finally:
        if conexion and conexion.open:
            cursor.close()
            conexion.close()


@app.route('/api/signup', methods=['POST'])
def api_signup():
    # Obtener los datos del formulario
    nombre = request.form.get('name', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()

    # Validaciones básicas
    if not nombre or not username or not password:
        return "Todos los campos son obligatorios. <a href='/signup'>Volver</a>", 400

    if password != confirm_password:
        return "Las contraseñas no coinciden. <a href='/signup'>Volver</a>", 400

    # Hashear la contraseña antes de guardarla
    password_encriptada = generate_password_hash(password)

    conexion = None
    try:
        conexion = pymysql.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 24316)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            ssl={'ssl': {}}
        )
        cursor = conexion.cursor()

        # Insertar el nuevo usuario normal
        sql = """
            INSERT INTO usuarios (username, nombre, password) 
            VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (username, nombre, password_encriptada))
        conexion.commit()

        # Registro exitoso, lo mandamos directo al Login para que entre a su cuenta
        return "Cuenta creada con éxito. Ahora puedes <a href='/'>Iniciar Sesión aquí</a>."

    except pymysql.backends.mysqld.err.IntegrityError:
        # Esto salta si el 'username' ya existe
        return f"El nombre de usuario '{username}' ya está ocupado. <a href='/signup'>Intenta con otro</a>.", 409
    except Exception as ex:
        return f"Error en el servidor: {ex} <a href='/signup'>Volver</a>", 500
    finally:
        if conexion and conexion.open:
            cursor.close()
            conexion.close()


@app.route('/api/guardar', methods=['POST'])
def api_guardar_elemento():
    data = request.json
    exito = Elemento.save(
        titulo=data['titulo'],
        tipo=data['tipo'],
        autor_director=data['autor_director'],
        descripcion=data['descripcion'],
        calificacion=int(data['calificacion']),
        opinion=data['opinion']
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
