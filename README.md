# Chihuahuateca 🐾

El guardián ideal de libros, películas y series. Una aplicación web dinámica y responsiva diseñada para gestionar colecciones de entretenimiento en tiempo real con un toque único.

## ✨ Características Principales
* **CRUD Completo en Tiempo Real:** Permite agregar, visualizar, editar y eliminar libros o películas de forma asíncrona mediante peticiones HTTP `fetch` sin recargar la página.
* **Sistema de Autenticación Dinámico:** Registro e inicio de sesión seguro para múltiples usuarios con sesiones cifradas. Cada usuario administra de forma exclusiva sus propios elementos guardados.
* **Red Social y Sistema de Seguidores:** Modelo de interacción que permite seguir y dejar de seguir a otros usuarios de la comunidad, así como visualizar estadísticas de seguidores y seguidos en el perfil personal.
* **Centro de Notificaciones en Tiempo Real:** Sistema de alertas y notificaciones con contador visual (campana) para informar al usuario de interacciones clave (nuevos seguidores, likes en sus publicaciones y comentarios).
* **Filtrado y Búsqueda Instantánea:** Barra de búsqueda integrada por coincidencia de texto (título, autor o director), categorías rápidas (Libros 📚, Películas 🎬, Series 📺 o Todos 🐾) y modal/panel emergente compacto para filtros avanzados (género, calificación y orden).
* **Sistema de Categorías (Tags):** Clasificación por géneros visuales para organizar y filtrar las obras rápidamente.
* **Soporte para Portadas y Autocompletado Online:** Muestra imágenes de portada o póster en cada tarjeta. Incluye botones de asistencia técnica para buscar y autocompletar dinámicamente la portada y la sinopsis desde APIs públicas (Open Library / TMDB / OMDb).
* **Exportación de Colección a PDF Enriquecida:** Generación e impresión en PDF descargable desde el perfil del usuario, maquetando una ficha completa formateada por cada página, autor de publicación y fecha de modificación para su consulta offline.
* **Interacción Social (Likes ❤️):** Permite a los usuarios dar "Me gusta" a los elementos publicados por otros miembros de la comunidad en tiempo real.
* **Auditoría Extendida del Sistema (Logs):** Registro histórico automático de la actividad de los usuarios en la base de datos (inicios de sesión, cierres de sesión, registros, me gusta, exportaciones PDF y modificaciones).
* **Interfaz Pulida y Moderna:** Menú desplegable de perfil, centro de notificaciones, panel organizado de estadísticas personales, modales interactivos para la gestión de elementos y alertas estéticas mediante **SweetAlert2**.

---

## 🛠️ Tecnologías Utilizadas
* **Backend:** Python + Flask (Framework web ágil)
* **Frontend:** HTML5, CSS3 (Diseño responsivo y variables nativas), JavaScript (Vanilla ES6)
* **Plantillas:** Jinja2 (Renderizado dinámico de componentes en el servidor)
* **Generación de Reportes:** ReportLab / Pillow (Renderizado de documentos PDF)
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
* `fecha_registro` (DATETIME): Fecha en la que se registró el usuario.
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
* `imagen_url` (TEXT): Enlace a la imagen de portada o póster de la obra.
* `fecha_creacion` (TIMESTAMP): Registro automático de la fecha de alta.
* `fecha_actualizacion` (TIMESTAMP): Registro automático al realizar modificaciones.
* `usuario_id` (INT): Llave foránea vinculada al `id` de la tabla `usuarios`.

### Tabla: `seguidores`
Gestiona la red de conexiones y seguimiento entre los usuarios de la plataforma.
* `id` (INT, Primary Key, Auto-increment)
* `seguidor_id` (INT): Llave foránea vinculada al usuario que realiza el seguimiento (`ON DELETE CASCADE`).
* `seguido_id` (INT): Llave foránea vinculada al usuario que recibe el seguimiento (`ON DELETE CASCADE`).
* `fecha` (TIMESTAMP): Registro de fecha y hora del seguimiento (`DEFAULT CURRENT_TIMESTAMP`).

### Tabla: `notificaciones`
Almacena la actividad e interacciones destinadas a avisar a los usuarios.
* `id` (INT, Primary Key, Auto-increment)
* `usuario_id` (INT): Llave foránea vinculada al usuario receptor (`ON DELETE CASCADE`).
* `emisor_id` (INT): Llave foránea vinculada al usuario que originó la interacción (`ON DELETE CASCADE`).
* `tipo` (INT): Identificador numérico mapeado vía Enum en Python (`1: LIKE`, `2: FOLLOW`, `3: COMMENT`).
* `referencia_id` (INT): Llave foránea opcional vinculada al elemento de `coleccion` (`ON DELETE CASCADE`).
* `titulo_referencia` (VARCHAR): En caso de ser un me gusta, se menciona el elemento al que se le dio me gusta.
* `mensaje` (TEXT): Mensaje descriptivo de la notificación.
* `leido` (TINYINT): Estado de lectura (`1` significa leido).
* `fecha` (DATETIME): Fecha de la notificación.

### Tabla: `me_gusta`
Gestiona la interacción social de los usuarios mediante "likes" en los elementos de la colección.
* `id` (INT, Primary Key, Auto-increment)
* `usuario_id` (INT): Llave foránea vinculada al `id` del usuario que da el me gusta (`ON DELETE CASCADE`).
* `elemento_id` (INT): Llave foránea vinculada al `id` del elemento en `coleccion` (`ON DELETE CASCADE`).
* `fecha` (TIMESTAMP): Registro de fecha y hora del me gusta (`DEFAULT CURRENT_TIMESTAMP`).

### Tabla: `log`
Tabla de auditoría para monitorizar los eventos críticos ocurridos dentro del ecosistema.
* `id` (INT, Primary Key, Auto-increment)
* `fecha` (TIMESTAMP): Estampa de tiempo generada por el servidor de forma nativa (`DEFAULT CURRENT_TIMESTAMP`).
* `id_user` (INT): Llave foránea vinculada al usuario que ejecutó la acción (`ON DELETE CASCADE`).
* `descripcion` (TEXT): Información extendida del evento en cuestión.
* `type` (INT): Categoría numérica del evento expresada vía Enum (ej: `LOGIN`, `LOGOUT`, `REGISTER`, `SAVE`, `EDIT`, `DELETE`, `LIKE`, `UNLIKE`, `PDF_EXPORT`, `FOLLOW`, `UNFOLLOW`).

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
reportlab
Pillow