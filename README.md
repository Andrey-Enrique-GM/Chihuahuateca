# Chihuahuateca 🐾

¡Hola! Este es un proyecto de una aplicación web en **Python** para llevar el control de tus libros y películas favoritas (una colección personal intelectual). La aplicación te permite agregar, ver, editar y borrar registros de forma interactiva sin tener que recargar la página todo el tiempo.

## 🛠️ Tecnologías que usamos

Para armar este proyecto conectamos varias tecnologías que se complementan entre sí:
* **Backend:** Python con el framework **Flask** para manejar las rutas de la aplicación y las respuestas del servidor.
* **Base de Datos:** **MySQL** para guardar de forma permanente toda nuestra colección.
* **Frontend (Diseño e Interactividad):**
    * **HTML:** Para estructurar el esqueleto de la página y los formularios de los modales (ventanas emergentes).
    * **CSS:** Diseñado con **CSS Grid** responsivo (para que las tarjetas se acomoden solas en celular o PC) y **Flexbox**.
    * **JavaScript (Vanilla JS):** Para manejar la magia de abrir/cerrar modales, hacer búsquedas en tiempo real y comunicarse asíncronamente con Python mediante `fetch` (¡sin recargar la página!).

---

## 🗄️ Estructura de la Base de Datos

La base de datos se llama `chihuahuadb` y cuenta con una tabla principal estructurada de la siguiente manera:

### Tabla: `coleccion`
Guarda tanto los libros como las películas combinados en una sola estructura:
* `id`: INT (Llave primaria, autoincrementable).
* `titulo`: VARCHAR (El nombre del libro o película).
* `tipo`: VARCHAR (Define si es 'libro' o 'pelicula').
* `autor_director`: VARCHAR (El creador de la obra).
* `descripcion`: TEXT (La sinopsis o de qué trata).
* `calificacion`: INT (Tu nota del 1 al 5, que luego se transforma en estrellitas ⭐).
* `opinion`: TEXT (Tu comentario personal sobre la obra).
* `fecha_creacion`: DATETIME (Fecha exacta en la que lo registraste).
* `fecha_actualizacion`: DATETIME (Fecha de la última modificación).

---

## 🚀 ¿Cómo funciona por dentro?

El proyecto está organizado siguiendo una estructura limpia inspirada en el patrón **MVC (Modelo-Vista-Controlador)**:

1.  **`persistence/db.py`:** Configura la conexión directa a MySQL usando la librería `pymysql`.
2.  **`entities/elemento.py`:** Es la clase `Elemento` en Python. Contiene toda la lógica orientada a objetos y los métodos de base de datos (`obtener_todos`, `obtener_por_id`, `guardar`, `actualizar`, `borrar`) usando cursores de tipo diccionario (`DictCursor`).
3.  **`app.py`:** El archivo principal de Flask que arranca el servidor y expone las rutas que sirven la página y los endpoints de la API JSON que usa JavaScript.
4.  **`static/js/main.js`:** Captura los eventos del usuario (escribir en el buscador, hacer clic en los filtros de Libros/Películas, o enviar formularios) y hace peticiones de fondo (`fetch`) hacia Flask para actualizar la base de datos al instante.

---

## 📦 Cómo correr el proyecto localmente

Si te descargas el código y quieres ponerlo a marchar en tu computadora, sigue estos pasos:

1.  **Crea tu entorno virtual (burbuja aislada):**
    ```bash
    python -m venv venv
    ```
2.  **Activa el entorno virtual:**
    * En Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
    * En Windows (CMD): `.\venv\Scripts\activate.bat`
3.  **Instala las dependencias limpias:**
    ```bash
    pip install flask pymysql
    ```
4.  **Configura tu base de datos:** Asegúrate de tener MySQL corriendo con la tabla `coleccion` creada.
5.  **Enciende la aplicación:**
    ```bash
    python app.py
    ```
6.  Abre tu navegador e ingresa a: `http://127.0.0.1:5000`

---
🐾 *¡Proyecto guardado con éxito y listo para presumir en GitHub!*
