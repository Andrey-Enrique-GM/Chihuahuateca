# Chihuahuateca 🐾

El guardián ideal de libros, películas y series. Una aplicación web dinámica y responsiva diseñada para gestionar colecciones de entretenimiento en tiempo real con un toque único.

## ✨ Características Principales
* **CRUD Completo en Tiempo Real:** Permite agregar, visualizar, editar y eliminar libros o películas de forma asíncrona mediante peticiones HTTP `fetch` sin recargar la página.
* **Sistema de Autenticación Dinámico:** Registro e inicio de sesión seguro para múltiples usuarios con sesiones cifradas. Cada usuario administra de forma exclusiva sus propios elementos guardados.
* **Filtrado y Búsqueda Instantánea:** Barra de búsqueda integrada por coincidencia de texto (título, autor o director), categorías rápidas (Libros 📚, Películas 🎬, Series 📺 o Todos 🐾) y panel de filtros avanzados por género, calificación y orden.
* **Sistema de Categorías (Tags):** Clasificación por géneros visuales para organizar y filtrar las obras rápidamente.
* **Interacción Social (Likes ❤️):** Permite a los usuarios dar "Me gusta" a los elementos publicados por otros miembros de la comunidad en tiempo real.
* **Auditoría del Sistema (Logs):** Registro histórico automático de la actividad de los usuarios en la base de datos (inicios de sesión, actualizaciones, modificaciones, etc.).
* **Interfaz Pulida y Moderna:** Menú desplegable de perfil, modales interactivos para la gestión de elementos y alertas estéticas mediante **SweetAlert2**.

---

## 🛠️ Tecnologías Utilizadas
* **Backend:** Python + Flask (Framework web ágil)
* **Frontend:** HTML5, CSS3 (Diseño responsivo y variables nativas), JavaScript (Vanilla ES6)
* **Plantillas:** Jinja2 (Renderizado dinámico de componentes en el servidor)
* **Base de Datos:** MySQL (Alojado en la nube con la plataforma **Aiven**)
* **Aplicación:** Alojada en la nube con la plataforma **Render**
* **Componentes de Terceros:** SweetAlert2 (Notificaciones de interfaz)

---

## 🗄️ Arquitectura de la Base de Datos

La aplicación utiliza la base de datos `chihuahuadb` y está compuesta por las siguientes estructuras relacionales:

### Tabla: `usuarios`
Almacena las credenciales y perfiles de los usuarios que acceden al sistema.
* `id` (INT, Primary Key, Auto-increment)
* `username` (VARCHAR, Unique): Identificador único para el inicio de sesión.
* `nombre` (VARCHAR): Nombre real del usuario que inició sesión.
* `password` (VARCHAR): Contraseña segura encriptada.
* `fecha_registro` (DATETIME): Fecha en la que se registro el usuario.
* `rol` (VARCHAR): Nivel de privilegios ('USER', 'ADMIN').

### Tabla: `coleccion`
Guarda los libros, películas y series agregados por la comunidad, vinculados a su respectivo creador.
* `id` (INT, Primary Key, Auto-increment)
* `titulo` (VARCHAR): Nombre de la obra.
* `tipo` (VARCHAR): Define si el elemento es `'libro'`, `'pelicula'` o `'serie'`.
* `genero` (VARCHAR): Clasificación o género temático (ej. Fantasía, Terror, Sci-Fi, Drama).
* `autor_director` (VARCHAR): Creador del material.
* `descripcion` (TEXT): Sinopsis o resumen corto.
* `calificacion` (INT): Puntuación personal de la escala del 1 al 5 representada con estrellas (⭐).
* `opinion` (TEXT): Reseña crítica personal.
* `fecha_creacion` (TIMESTAMP): Registro automático de la fecha de alta.
* `fecha_actualizacion` (TIMESTAMP): Registro automático al realizar modificaciones.
* `usuario_id` (INT): Llave foránea vinculada al `id` de la tabla `usuarios`.

### Tabla: `me_gusta`
Gestiona la interacción social de los usuarios mediante "likes" en los elementos de la colección.
* `id` (INT, Primary Key, Auto-increment)
* `usuario_id` (INT): Llave foránea vinculada al `id` del usuario que da el like (`ON DELETE CASCADE`).
* `elemento_id` (INT): Llave foránea vinculada al `id` del elemento en `coleccion` (`ON DELETE CASCADE`).
* `fecha` (TIMESTAMP): Registro de fecha y hora del like (`DEFAULT CURRENT_TIMESTAMP`).

### Tabla: `log`
Tabla de auditoría para monitorizar los eventos críticos ocurridos dentro del ecosistema.
* `id` (INT, Primary Key, Auto-increment)
* `fecha` (TIMESTAMP): Estampa de tiempo generada por el servidor de forma nativa (`DEFAULT CURRENT_TIMESTAMP`).
* `id_user` (INT): Llave foránea vinculada al usuario que ejecutó la acción (`ON DELETE CASCADE`).
* `descripcion` (TEXT): Información extendida del evento en cuestión.
* `type` (VARCHAR): Breve descripción de la actividad efectuada (ej: `'Inicio de sesión'`, `'Guardó el elemento'`).

---

## 📦 Dependencias del Proyecto (`requirements.txt`)
El entorno de ejecución requiere las siguientes librerías core instaladas:
```text
Flask==3.1.3
Jinja2==3.1.6
Werkzeug==3.1.8
itsdangerous==2.2.0
MarkupSafe==3.0.3
click==8.4.1
blinker==1.9.0
python-dotenv==1.2.2
PyMySQL==1.2.0
mysql-connector-python==9.7.0
colorama==0.4.6
gunicorn==26.0.0
packaging==26.2