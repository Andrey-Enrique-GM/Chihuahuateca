// ==========================================================================
// CONFIGURACION INICIAL Y SELECCION DE ELEMENTOS DOM
// ==========================================================================



document.addEventListener('DOMContentLoaded', () => {
    // Modales
    const modalAgregar = document.getElementById('modal-agregar');
    const modalEditar = document.getElementById('modal-editar');

    // Botones apertura
    document.getElementById('btn-abrir-agregar').addEventListener('click', () => abrirModal('modal-agregar'));
    document.getElementById('btn-abrir-editar').addEventListener('click', () => abrirModal('modal-editar'));

    // Buscador y Filtros de Tarjetas
    const buscador = document.getElementById('buscador');
    buscador.addEventListener('input', filtrarColeccion);

    document.getElementById('btn-todos').addEventListener('click', (e) => cambiarFiltroTipo('todos', e.target));
    document.getElementById('btn-libros').addEventListener('click', (e) => cambiarFiltroTipo('libro', e.target));
    document.getElementById('btn-peliculas').addEventListener('click', (e) => cambiarFiltroTipo('pelicula', e.target));

    // Formularios y Eventos CRUD
    document.getElementById('form-agregar').addEventListener('submit', guardarNuevoElemento);
    document.getElementById('select-editar-elemento').addEventListener('change', cargarDatosParaEditar);
    document.getElementById('form-editar').addEventListener('submit', actualizarElemento);
    document.getElementById('btn-borrar-elemento').addEventListener('click', borrarElemento);
});

// Variable global para mantener el estado del filtro de tipo activo ('todos', 'libro', 'pelicula')
let filtroTipoActual = 'todos';





// ==========================================================================
// CONTROL DE VENTANAS MODALES
// ==========================================================================



function abrirModal(idModal) {
    document.getElementById(idModal).classList.add('mostrar');
}



function cerrarModal(idModal) {
    document.getElementById(idModal).classList.remove('mostrar');
    
    // Limpieza al cerrar
    if (idModal === 'modal-agregar') {
        document.getElementById('form-agregar').reset();
    } else if (idModal === 'modal-editar') {
        document.getElementById('form-editar').reset();
        document.getElementById('select-editar-elemento').value = "";
        document.getElementById('form-editar').classList.add('deshabilitado');
    }
}





// ==========================================================================
// FILTRADO DINAMICO DE TARJETAS
// ==========================================================================



function cambiarFiltroTipo(tipo, botonClickeado) {
    // Cambiar clase activa visual en los botones
    document.querySelectorAll('.btn-filtro').forEach(btn => btn.classList.remove('activo'));
    botonClickeado.classList.add('activo');

    filtroTipoActual = tipo;
    filtrarColeccion(); // Re-ejecutamos el filtro combinado
}



function filtrarColeccion() {
    const textoBusqueda = buscador.value.toLowerCase().trim();
    const tarjetas = document.querySelectorAll('.tarjeta-item');

    tarjetas.forEach(tarjeta => {
        // Leemos los atributos personalizados que se configuraron en el HTML
        const tipoTarjeta = tarjeta.getAttribute('data-tipo');
        const tituloTarjeta = tarjeta.getAttribute('data-titulo');
        const autorTarjeta = tarjeta.getAttribute('data-autor');

        // Condicion 1: Coincide con el boton de filtro seleccionado?
        const pasaFiltroTipo = (filtroTipoActual === 'todos' || tipoTarjeta === filtroTipoActual);

        // Condicion 2: Coincide con lo que se escribio en el buscador?
        const pasaBuscador = (tituloTarjeta.includes(textoBusqueda) || autorTarjeta.includes(textoBusqueda));

        // Si cumple ambas condiciones, JavaScript la muestra, si no, la oculta al instante
        if (pasaFiltroTipo && pasaBuscador) {
            tarjeta.style.display = 'flex';
        } else {
            tarjeta.style.display = 'none';
        }
    });
}





// ==========================================================================
// OPERACIONES ASINCRONAS CON LA API DE PYTHON (FETCH CRUD)
// ==========================================================================



// --- CREATE (Guardar) ---
function guardarNuevoElemento(e) {
    e.preventDefault(); // Evita que la página se recargue por el submit tradicional

    const datos = {
        tipo: document.getElementById('add-tipo').value,
        titulo: document.getElementById('add-titulo').value,
        autor_director: document.getElementById('add-autor').value,
        calificacion: document.getElementById('add-calificacion').value,
        descripcion: document.getElementById('add-descripcion').value,
        opinion: document.getElementById('add-opinion').value
    };

    fetch('/api/guardar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datos)
    })
    .then(res => res.json())
    .then(resultado => {
        if (resultado.success) {
            Swal.fire({
            icon: 'success',
            title: 'Registro Exitoso',
            text: 'El elemento se guardó correctamente en la Chihuahuateca.',
            confirmButtonColor: '#2c3e50',
            timer: 1500,
            timerProgressBar: true
        }).then(() => {
            location.reload(); // Recarga la colección para ver el nuevo item
        });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error al guardar',
                text: 'No se pudo guardar el elemento en la Chihuahuateca.',
                confirmButtonColor: '#2c3e50'
            });
        }
    })
    .catch(err => console.error('Error:', err));
}



// --- READ SINGLE (Cargar datos en el formulario de edicion) ---
function cargarDatosParaEditar() {
    const idElemento = this.value;
    const formularioEditar = document.getElementById('form-editar');

    if (!idElemento) {
        formularioEditar.classList.add('deshabilitado');
        formularioEditar.reset();
        return;
    }

    // Peticion a Python para traer los datos actuales de ese ID
    fetch(`/api/elemento/${idElemento}`)
    .then(res => res.json())
    .then(data => {
        if (!data.error) {
            // Rellenamos los inputs
            document.getElementById('edit-id').value = data.id;
            document.getElementById('edit-tipo').value = data.tipo;
            document.getElementById('edit-titulo').value = data.titulo;
            document.getElementById('edit-autor').value = data.autor_director;
            document.getElementById('edit-calificacion').value = data.calificacion;
            document.getElementById('edit-descripcion').value = data.descripcion;
            document.getElementById('edit-opinion').value = data.opinion;

            // Activamos visualmente el formulario quitando la clase deshabilitada
            formularioEditar.classList.remove('deshabilitado');
        }
    })
    .catch(err => console.error('Error:', err));
}



// --- UPDATE (Actualizar) ---
function actualizarElemento(e) {
    e.preventDefault();

    const datos = {
        id: document.getElementById('edit-id').value,
        tipo: document.getElementById('edit-tipo').value,
        titulo: document.getElementById('edit-titulo').value,
        autor_director: document.getElementById('edit-autor').value,
        calificacion: document.getElementById('edit-calificacion').value,
        descripcion: document.getElementById('edit-descripcion').value,
        opinion: document.getElementById('edit-opinion').value
    };

    fetch('/api/editar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datos)
    })
    .then(res => res.json())
    .then(resultado => {
        if (resultado.success) {
            Swal.fire({
                icon: 'success',
                title: 'Actualización Exitosa',
                text: 'Los cambios se guardaron correctamente.',
                confirmButtonColor: '#2c3e50',
                timer: 1500,
                timerProgressBar: true
            }).then(() => {
                location.reload();
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error al actualizar',
                text: 'No se pudieron guardar los cambios.',
                confirmButtonColor: '#2c3e50'
            });
        }
    })
    .catch(err => console.error('Error:', err));
}



// --- DELETE (Borrar) ---
function borrarElemento() {
    const idElemento = document.getElementById('edit-id').value;
    const titulo = document.getElementById('edit-titulo').value;

    if (!idElemento) return;

    // Confirmacion antes de destruir un dato
    Swal.fire({
        title: '¿Estás seguro?',
        text: "¡No podrás revertir este cambio!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d35400',
        cancelButtonColor: '#7f8c8d',
        confirmButtonText: 'Sí, borrar de la colección',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/api/borrar/${idElemento}`, {
                method: 'DELETE'
            })
            .then(res => res.json())
            .then(resultado => {
                if (resultado.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Elemento Borrado Permanentemente',
                        text: 'El elemento fue eliminado de tu colección.',
                        confirmButtonColor: '#2c3e50'
                    }).then(() => {
                        location.reload();
                    });
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error al borrar',
                        text: 'No se pudo eliminar el elemento.',
                        confirmButtonColor: '#2c3e50'
                    });
                }
            })
            .catch(err => console.error('Error:', err));
        }
    });
}



// Clic sobre la opción del menú desplegable
document.getElementById('btn-cambiar-pass').addEventListener('click', function(e) {
    e.preventDefault();
    if (typeof abrirModal === "function") {
        abrirModal('modal-password');
    } else {
        document.getElementById('modal-password').classList.add('activo');
    }
});



// Procesar el formulario de cambio de credenciales
document.getElementById('form-cambiar-password').addEventListener('submit', function(e) {
    e.preventDefault();

    const passActual = document.getElementById('pass-actual').value;
    const passNueva = document.getElementById('pass-nueva').value;
    const passConfirmar = document.getElementById('pass-confirmar').value;

    if (passNueva !== passConfirmar) {
        Swal.fire({
            icon: 'error',
            title: '¡Oops!',
            text: 'La nueva contraseña y su confirmación no coinciden.'
        });
        return;
    }

    // Petición asíncrona a la API de Flask
    fetch('/api/usuario/cambiar-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            pass_actual: passActual,
            pass_nueva: passNueva
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: '¡Excelente!',
                text: data.message
            }).then(() => {
                // Limpiar inputs del formulario y cerrar
                document.getElementById('form-cambiar-password').reset();
                if (typeof cerrarModal === "function") {
                    cerrarModal('modal-password');
                } else {
                    document.getElementById('modal-password').classList.remove('activo');
                }
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.message || 'No se pudo realizar la actualización.'
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error de servidor',
            text: 'Hubo un problema al conectar con el servidor.'
        });
    });
});
