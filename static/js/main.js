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
            alert('Agregado con exito a la Chihuahuateca! 🐾');
            window.location.reload(); // Recargamos para ver la nueva tarjeta pintada por Python
        } else {
            alert('Hubo un error al guardar.');
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
            alert('Chihuahuateca actualizada! 🐾');
            window.location.reload();
        } else {
            alert('Error al actualizar.');
        }
    })
    .catch(err => console.error('Error:', err));
}



// --- DELETE (Borrar) ---
function borrarElemento() {
    const idElemento = document.getElementById('edit-id').value;
    const titulo = document.getElementById('edit-titulo').value;

    if (!idElemento) return;

    // Confirmacion clasica antes de destruir un dato
    if (confirm(`Estas seguro de que quieres eliminar permanentemente "${titulo}" de tu coleccion?`)) {
        fetch(`/api/borrar/${idElemento}`, {
            method: 'DELETE'
        })
        .then(res => res.json())
        .then(resultado => {
            if (resultado.success) {
                alert('Registro eliminado para siempre 🐾💔');
                window.location.reload();
            } else {
                alert('No se pudo borrar el registro');
            }
        })
        .catch(err => console.error('Error:', err));
    }
}
