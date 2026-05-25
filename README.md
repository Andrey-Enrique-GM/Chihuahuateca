# Chihuahuateca 🐾

Este es un proyecto de una aplicación web para llevar el control de mis libros y películas favoritas (mi colección personal). Te permite agregar, ver, editar y borrar registros sin tener que recargar la página todo el tiempo.

## 🛠️ ¿Cómo está hecho?

Es una aplicación web hecha con las siguientes herramientas:
* **Python y Flask:** Para el servidor y las rutas de la página.
* **MySQL:** Para la base de datos donde se guarda todo de verdad.
* **HTML y CSS:** Para el diseño visual de las tarjetas y las ventanas flotantes (modales).
* **JavaScript:** Para buscar en tiempo real, filtrar entre libros/peliculas y guardar cosas usando `fetch`.

## 🗄️ La Base de Datos

La base de datos se llama `chihuahuadb` y usa una tabla llamada `coleccion` con estas columnas:
* `id`: El número de registro (autoincrementable).
* `titulo`: El nombre del libro o película.
* `tipo`: Si es 'libro' o 'pelicula'.
* `autor_director`: El creador.
* `descripcion`: La sinopsis.
* `calificacion`: La nota personal del 1 al 5.
* `opinion`: Mi reseña personal.
* `fecha_creacion` y `fecha_actualizacion`: Las fechas de registro y edición.
