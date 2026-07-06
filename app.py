import os
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from entities.elemento import Elemento



# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Configuración de la aplicación Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


# --- RUTAS DE NAVEGACION ---

@app.route('/')
def index():
    # Manda a llamar al metodo estatico que mapea la tabla a objetos
    coleccion_completa = Elemento.obtener_todos() 
    return render_template('index.html', elementos=coleccion_completa)



# --- RUTAS DE API ---

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
