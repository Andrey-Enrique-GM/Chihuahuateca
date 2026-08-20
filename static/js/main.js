// ==========================================================================
// CONFIGURACION INICIAL Y SELECCION DE ELEMENTOS DOM
// ==========================================================================

let filtroTipoActual = 'todos';
let filtroGeneroActual = 'todos';

function obtenerZonaHorariaActual() {
    const valor = (window.__zonaHorariaActual || 'AUTO');
    return (valor === null || valor === undefined || valor === '') ? 'AUTO' : String(valor).trim();
}

function parsearFechaUtc(fechaUTCString) {
    if (!fechaUTCString) return null;

    const texto = String(fechaUTCString).trim();
    if (!texto) return null;

    const iso = texto.includes('T') ? texto : texto.replace(' ', 'T');
    const conZ = iso.endsWith('Z') ? iso : `${iso}Z`;
    const fecha = new Date(conZ);

    if (Number.isNaN(fecha.getTime())) {
        return null;
    }

    return fecha;
}

function formatearFechaLocal(fechaUTCString, offsetGuardado = obtenerZonaHorariaActual()) {
    const fechaUtc = parsearFechaUtc(fechaUTCString);
    if (!fechaUtc) return 'Sin fecha';

    if (offsetGuardado === 'AUTO') {
        return fechaUtc.toLocaleString('es-MX', {
            dateStyle: 'medium',
            timeStyle: 'short'
        });
    }

    const desplazamiento = Number(offsetGuardado);
    if (Number.isNaN(desplazamiento)) {
        return fechaUtc.toLocaleString('es-MX', {
            dateStyle: 'medium',
            timeStyle: 'short'
        });
    }

    const fechaAjustada = new Date(fechaUtc.getTime() + (desplazamiento * 60 * 60 * 1000));
    return fechaAjustada.toLocaleString('es-MX', {
        dateStyle: 'medium',
        timeStyle: 'short'
    });
}

function actualizarFechasEnPantalla() {
    const offsetActual = obtenerZonaHorariaActual();
    document.querySelectorAll('.fecha-utc').forEach((elemento) => {
        const valor = elemento.dataset.fechaUtc;
        if (!valor) return;
        const texto = formatearFechaLocal(valor, offsetActual);
        elemento.textContent = elemento.textContent.includes('Registrado:') ? `Registrado: ${texto}` : elemento.textContent.includes('Editado:') ? `Editado: ${texto}` : texto;
    });

    document.querySelectorAll('.log-fecha').forEach((elemento) => {
        const valor = elemento.dataset.fechaUtc;
        if (!valor) return;
        elemento.textContent = `🕒 ${formatearFechaLocal(valor, offsetActual)}`;
    });

    document.querySelectorAll('.notificacion-tiempo').forEach((elemento) => {
        const valor = elemento.dataset.fechaUtc || elemento.textContent;
        if (!valor || valor === 'ahora') return;
        const fechaOriginal = valor.includes('Hace ') ? null : valor;
        if (fechaOriginal) {
            elemento.textContent = formatearFechaLocal(fechaOriginal, offsetActual);
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const actualizarBotonesSeguir = (usuarioId, siguiendo) => {
        document.querySelectorAll('.btn-seguir, .btn-siguiendo').forEach((button) => {
            if (String(button.dataset.usuarioId) !== String(usuarioId)) return;

            button.dataset.siguiendo = siguiendo ? 'true' : 'false';
            button.classList.toggle('btn-siguiendo', siguiendo);
            button.classList.toggle('btn-seguir', !siguiendo);
            button.textContent = siguiendo ? '✓ Siguiendo' : '+ Seguir';
        });
    };

    const listaUsuarios = document.querySelector('.lista-usuarios');
    if (listaUsuarios) {
        listaUsuarios.addEventListener('click', (event) => {
            const botonSeguir = event.target.closest('.btn-seguir, .btn-siguiendo');
            if (!botonSeguir) return;

            event.preventDefault();
            const usuarioId = botonSeguir.dataset.usuarioId;
            if (!usuarioId) return;

            fetch(`/api/seguir/${usuarioId}`, { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (!data.success) {
                        mostrarErrorSeguimiento(data.message || 'No se pudo cambiar el seguimiento.');
                        return;
                    }

                    actualizarBotonesSeguir(usuarioId, Boolean(data.siguiendo));
                })
                .catch(error => {
                    console.error('Error seguimiento:', error);
                    mostrarErrorSeguimiento('No se pudo actualizar el seguimiento en este momento.');
                });
        });
        return;
    }

    const btnNotificaciones = document.getElementById('btn-notificaciones');
    const dropdownNotificaciones = document.getElementById('dropdown-notificaciones');
    const badgeNotificaciones = document.getElementById('badge-notificaciones');
    const listaNotificaciones = document.getElementById('lista-notificaciones');

    function formatearTiempo(fecha) {
        if (!fecha) return 'ahora';

        const fechaUtc = parsearFechaUtc(fecha);
        if (!fechaUtc) return 'ahora';

        const diferenciaMin = Math.max(1, Math.round((Date.now() - fechaUtc.getTime()) / 60000));

        if (diferenciaMin < 60) return `Hace ${diferenciaMin} min`;

        const diferenciaHoras = Math.round(diferenciaMin / 60);
        if (diferenciaHoras < 24) return `Hace ${diferenciaHoras} h`;

        const diferenciaDias = Math.round(diferenciaHoras / 24);
        return `Hace ${diferenciaDias} d`;
    }

    function renderNotificaciones(items) {
        if (!listaNotificaciones) return;

        if (!items || !items.length) {
            listaNotificaciones.innerHTML = '<div class="notificacion-item"><p class="notificacion-texto">No tienes notificaciones.</p></div>';
            return;
        }

        listaNotificaciones.innerHTML = items.map(item => {
            const avatar = (item.emisor && item.emisor.username) ? item.emisor.username.charAt(0).toUpperCase() : 'N';
            const claseNoLeida = item.leido ? '' : 'no-leida';
            return `
                <div class="notificacion-item ${claseNoLeida}" data-id="${item.id}">
                    <div class="notificacion-avatar">${avatar}</div>
                    <div>
                        <p class="notificacion-texto">${item.mensaje}</p>
                        <span class="notificacion-tiempo" data-fecha-utc="${item.fecha}">${formatearTiempo(item.fecha)}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    function cargarNotificaciones() {
        fetch('/api/notificaciones')
            .then(res => res.json())
            .then(data => {
                if (!data.success) return;

                if ((data.unread_count || 0) > 0) {
                    badgeNotificaciones.textContent = data.unread_count;
                    badgeNotificaciones.classList.remove('hidden');
                } else {
                    badgeNotificaciones.classList.add('hidden');
                    badgeNotificaciones.textContent = '';
                }

                renderNotificaciones(data.items || []);
            })
            .catch(err => console.error('Error al cargar notificaciones:', err));
    }

    if (btnNotificaciones && dropdownNotificaciones) {
        btnNotificaciones.addEventListener('click', () => {
            const mostrar = dropdownNotificaciones.classList.toggle('hidden');

            if (!mostrar) {
                fetch('/api/notificaciones/marcar-leidas', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            badgeNotificaciones.classList.add('hidden');
                            badgeNotificaciones.textContent = '';
                            cargarNotificaciones();
                        }
                    })
                    .catch(err => console.error('Error al marcar notificaciones como leídas:', err));
            }
        });
    }

    document.addEventListener('click', (event) => {
        if (!dropdownNotificaciones) return;
        const clicDentro = dropdownNotificaciones.contains(event.target) || btnNotificaciones?.contains(event.target);
        if (!clicDentro) {
            dropdownNotificaciones.classList.add('hidden');
        }
    });

    cargarNotificaciones();
    setInterval(cargarNotificaciones, 30000);

    const selectZonaHoraria = document.getElementById('select-zona-horaria');
    const btnGuardarZonaHoraria = document.getElementById('btn-guardar-zona-horaria');

    if (selectZonaHoraria) {
        selectZonaHoraria.value = obtenerZonaHorariaActual();
    }

    if (btnGuardarZonaHoraria) {
        btnGuardarZonaHoraria.addEventListener('click', async () => {
            const zonaSeleccionada = selectZonaHoraria ? selectZonaHoraria.value : 'AUTO';

            try {
                const respuesta = await fetch('/api/ajustes/zona-horaria', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ zona_horaria: zonaSeleccionada })
                });
                const data = await respuesta.json();

                if (!data.success) {
                    Swal.fire({ icon: 'error', title: 'No se pudo guardar', text: data.message || 'Hubo un problema al actualizar la zona horaria.' });
                    return;
                }

                window.__zonaHorariaActual = zonaSeleccionada;
                actualizarFechasEnPantalla();
                Swal.fire({
                    icon: 'success',
                    title: 'Zona horaria actualizada',
                    text: data.message || 'Se actualizó correctamente la zona horaria.',
                    confirmButtonColor: '#2c3e50'
                });
            } catch (error) {
                console.error('Error al guardar zona horaria:', error);
                Swal.fire({ icon: 'error', title: 'Error', text: 'No se pudo conectar con el servidor.' });
            }
        });
    }

    actualizarFechasEnPantalla();

    // Modales
    const modalAgregar = document.getElementById('modal-agregar');
    const modalEditar = document.getElementById('modal-editar');

    // Botones apertura
    const btnAbrirAgregar = document.getElementById('btn-abrir-agregar');
    const btnAbrirEditar = document.getElementById('btn-abrir-editar');
    if (btnAbrirAgregar) {
        btnAbrirAgregar.addEventListener('click', () => abrirModal('modal-agregar'));
    }
    if (btnAbrirEditar) {
        btnAbrirEditar.addEventListener('click', () => abrirModal('modal-editar'));
    }

    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', function (event) {
            if (event.target === this) {
                cerrarModal(this.id);
            }
        });
    });

    // Buscador y Filtros Avanzados
    const buscador = document.getElementById('input-busqueda');
    const selectOrden = document.getElementById('select-orden');
    const selectEstrellas = document.getElementById('select-estrellas');
    const selectGenero = document.getElementById('filtro-genero');
    const btnFiltros = document.getElementById('btn-filtros-avanzados');
    const popoverFiltros = document.getElementById('popover-filtros');
    const btnCerrarFiltros = document.getElementById('btn-cerrar-filtros');
    const btnAplicarFiltros = document.getElementById('btn-aplicar-filtros');
    const btnLimpiarFiltros = document.getElementById('btn-limpiar-filtros');

    if (buscador) {
        buscador.addEventListener('input', filtrarYOrdenarColeccion);
    }
    if (selectOrden) {
        selectOrden.addEventListener('change', () => {
            filtrarYOrdenarColeccion();
            actualizarIndicadorFiltros();
        });
    }
    if (selectEstrellas) {
        selectEstrellas.addEventListener('change', () => {
            filtrarYOrdenarColeccion();
            actualizarIndicadorFiltros();
        });
    }
    if (selectGenero) {
        selectGenero.addEventListener('change', () => {
            filtroGeneroActual = selectGenero.value;
            filtrarYOrdenarColeccion();
            actualizarIndicadorFiltros();
        });
    }

    if (btnFiltros) {
        btnFiltros.addEventListener('click', togglePopoverFiltros);
    }
    if (btnCerrarFiltros) {
        btnCerrarFiltros.addEventListener('click', cerrarPopoverFiltros);
    }
    if (btnAplicarFiltros) {
        btnAplicarFiltros.addEventListener('click', () => {
            filtrarYOrdenarColeccion();
            actualizarIndicadorFiltros();
            cerrarPopoverFiltros();
        });
    }
    if (btnLimpiarFiltros) {
        btnLimpiarFiltros.addEventListener('click', () => {
            if (selectOrden) selectOrden.value = 'reciente';
            if (selectEstrellas) selectEstrellas.value = 'todas';
            if (selectGenero) selectGenero.value = 'todos';
            filtroGeneroActual = 'todos';
            filtrarYOrdenarColeccion();
            actualizarIndicadorFiltros();
            cerrarPopoverFiltros();
        });
    }

    if (popoverFiltros && btnFiltros) {
        document.addEventListener('click', (event) => {
            const dentroPopover = popoverFiltros.contains(event.target);
            const clicEnBoton = btnFiltros.contains(event.target);
            if (!dentroPopover && !clicEnBoton && popoverFiltros.classList.contains('mostrar')) {
                cerrarPopoverFiltros();
            }
        });
    }

    const btnTodos = document.getElementById('btn-todos');
    const btnLibros = document.getElementById('btn-libros');
    const btnPeliculas = document.getElementById('btn-peliculas');
    const btnSeries = document.getElementById('btn-series');

    if (btnTodos) btnTodos.addEventListener('click', (e) => cambiarFiltroTipo('todos', e.target));
    if (btnLibros) btnLibros.addEventListener('click', (e) => cambiarFiltroTipo('libro', e.target));
    if (btnPeliculas) btnPeliculas.addEventListener('click', (e) => cambiarFiltroTipo('pelicula', e.target));
    if (btnSeries) btnSeries.addEventListener('click', (e) => cambiarFiltroTipo('serie', e.target));

    // Formularios y Eventos CRUD
    const formAgregar = document.getElementById('form-agregar');
    if (formAgregar) {
        formAgregar.addEventListener('submit', guardarNuevoElemento);
    }
    document.getElementById('add-imagen-url')?.addEventListener('input', () => actualizarPreviewImagen('add-imagen-url', 'add-preview-imagen'));
    document.getElementById('btn-buscar-poster-add')?.addEventListener('click', () => buscarDatosExternos('add', 'poster'));
    document.getElementById('btn-buscar-sinopsis-add')?.addEventListener('click', () => buscarDatosExternos('add', 'sinopsis'));
    const selectEditarElemento = document.getElementById('select-editar-elemento');
    if (selectEditarElemento) {
        selectEditarElemento.addEventListener('change', cargarDatosParaEditar);
    }
    document.getElementById('edit-imagen-url')?.addEventListener('input', () => actualizarPreviewImagen('edit-imagen-url', 'edit-preview-imagen'));
    document.getElementById('btn-buscar-poster-edit')?.addEventListener('click', () => buscarDatosExternos('edit', 'poster'));
    document.getElementById('btn-buscar-sinopsis-edit')?.addEventListener('click', () => buscarDatosExternos('edit', 'sinopsis'));
    const formEditar = document.getElementById('form-editar');
    if (formEditar) {
        formEditar.addEventListener('submit', actualizarElemento);
    }
    const btnBorrarElemento = document.getElementById('btn-borrar-elemento');
    if (btnBorrarElemento) {
        btnBorrarElemento.addEventListener('click', borrarElemento);
    }

    const gridColeccion = document.getElementById('grid-coleccion');
    if (gridColeccion) {
        gridColeccion.addEventListener('click', (event) => {
        const likeButton = event.target.closest('.btn-like');
        if (likeButton) {
            event.preventDefault();
            const elementoId = likeButton.dataset.elementoId;
            if (!elementoId) return;

            fetch(`/api/like/${elementoId}`, { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        likeButton.classList.toggle('liked', data.liked);
                        likeButton.dataset.liked = data.liked ? 'true' : 'false';
                        likeButton.querySelector('.icon-like').textContent = data.liked ? '❤️' : '🤍';
                        likeButton.querySelector('.like-count').textContent = data.total_likes;
                    } else {
                        if (window.Swal) {
                            Swal.fire({ icon: 'error', title: 'Error', text: data.message || 'No se pudo actualizar el like.' });
                        } else {
                            alert(data.message || 'No se pudo actualizar el like.');
                        }
                    }
                })
                .catch(err => {
                    console.error('Error like:', err);
                    if (window.Swal) {
                        Swal.fire({ icon: 'error', title: 'Error de servidor', text: 'No se pudo actualizar el like en este momento.' });
                    } else {
                        alert('No se pudo actualizar el like en este momento.');
                    }
                });
            return;
        }

        const followButton = event.target.closest('.btn-seguir, .btn-siguiendo');
        if (followButton) {
            event.preventDefault();
            const usuarioId = followButton.dataset.usuarioId;
            if (!usuarioId) return;

            fetch(`/api/seguir/${usuarioId}`, { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (!data.success) {
                        if (window.Swal) {
                            Swal.fire({ icon: 'error', title: 'Error', text: data.message || 'No se pudo cambiar el seguimiento.' });
                        } else {
                            alert(data.message || 'No se pudo cambiar el seguimiento.');
                        }
                        return;
                    }

                    const siguiendo = Boolean(data.siguiendo);
                    actualizarBotonesSeguir(usuarioId, siguiendo);

                    const contadorSeguidores = document.getElementById('seguidores-total');
                    if (contadorSeguidores) {
                        contadorSeguidores.textContent = data.total_seguidores;
                    }
                })
                .catch(err => {
                    console.error('Error seguimiento:', err);
                    if (window.Swal) {
                        Swal.fire({ icon: 'error', title: 'Error de servidor', text: 'No se pudo actualizar el seguimiento en este momento.' });
                    } else {
                        alert('No se pudo actualizar el seguimiento en este momento.');
                    }
                });
            return;
        }

            const tagFiltro = event.target.closest('.tag-filtro');
            if (!tagFiltro) return;

            const generoSeleccionado = tagFiltro.getAttribute('data-genero') || 'sin-genero';
            const selectGenero = document.getElementById('filtro-genero');
            if (selectGenero) {
                selectGenero.value = generoSeleccionado || 'sin-genero';
                filtroGeneroActual = selectGenero.value;
            }
            filtrarYOrdenarColeccion();
        });
    }

    // Ejecutar filtrado inicial para ordenar y actualizar contador al cargar la pagina
    if (document.getElementById('grid-coleccion')) {
        filtrarYOrdenarColeccion();
    }
});

function mostrarErrorSeguimiento(mensaje) {
    if (window.Swal) {
        Swal.fire({ icon: 'error', title: 'Error', text: mensaje });
    } else {
        alert(mensaje);
    }
}



// ==========================================================================
// CONTROL DE VENTANAS MODALES
// ==========================================================================

function abrirModal(idModal) {
    document.getElementById(idModal).classList.add('mostrar');
}

function cerrarModal(idModal) {
    const modal = document.getElementById(idModal);
    if (!modal) return;

    modal.classList.remove('mostrar');

    if (idModal === 'modal-agregar') {
        document.getElementById('form-agregar').reset();
    } else if (idModal === 'modal-editar') {
        document.getElementById('form-editar').reset();
        document.getElementById('select-editar-elemento').value = "";
        document.getElementById('form-editar').classList.add('deshabilitado');
    } else if (idModal === 'modal-password') {
        document.getElementById('form-cambiar-password').reset();
    }
}



// ==========================================================================
// FILTRADO, REORDENAMIENTO Y CONTADOR DE TARJETAS
// ==========================================================================

function cambiarFiltroTipo(tipo, botonClickeado) {
    document.querySelectorAll('.btn-filtro').forEach(btn => btn.classList.remove('activo'));
    botonClickeado.classList.add('activo');

    filtroTipoActual = tipo;
    filtrarYOrdenarColeccion();
}

function togglePopoverFiltros() {
    const popoverFiltros = document.getElementById('popover-filtros');
    const btnFiltros = document.getElementById('btn-filtros-avanzados');
    if (!popoverFiltros || !btnFiltros) return;

    const mostrar = !popoverFiltros.classList.contains('mostrar');
    popoverFiltros.classList.toggle('mostrar', mostrar);
    btnFiltros.setAttribute('aria-expanded', mostrar ? 'true' : 'false');
}

function cerrarPopoverFiltros() {
    const popoverFiltros = document.getElementById('popover-filtros');
    const btnFiltros = document.getElementById('btn-filtros-avanzados');
    if (!popoverFiltros || !btnFiltros) return;

    popoverFiltros.classList.remove('mostrar');
    btnFiltros.setAttribute('aria-expanded', 'false');
}

function actualizarIndicadorFiltros() {
    const btnFiltros = document.getElementById('btn-filtros-avanzados');
    if (!btnFiltros) return;

    const orden = document.getElementById('select-orden')?.value || 'reciente';
    const estrellas = document.getElementById('select-estrellas')?.value || 'todas';
    const genero = document.getElementById('filtro-genero')?.value || 'todos';
    const hayFiltros = orden !== 'reciente' || estrellas !== 'todas' || genero !== 'todos';

    btnFiltros.classList.toggle('con-filtros', hayFiltros);
}

function filtrarYOrdenarColeccion() {
    const textoBusqueda = document.getElementById('input-busqueda').value.toLowerCase().trim();
    const ordenSeleccionado = document.getElementById('select-orden').value;
    const estrellasSeleccionadas = document.getElementById('select-estrellas').value;
    const generoSeleccionado = filtroGeneroActual || 'todos';
    
    const contenedorGrid = document.getElementById('grid-coleccion');
    const tarjetasArray = Array.from(document.querySelectorAll('.tarjeta-item'));
    const totalElementos = tarjetasArray.length;

    let elementosVisibles = 0;

    // Filtrar visibilidad
    tarjetasArray.forEach(tarjeta => {
        const tipoTarjeta = tarjeta.getAttribute('data-tipo');
        const tituloTarjeta = tarjeta.getAttribute('data-titulo');
        const autorTarjeta = tarjeta.getAttribute('data-autor');
        const calificacionTarjeta = tarjeta.getAttribute('data-calificacion');
        const generoTarjeta = (tarjeta.getAttribute('data-genero') || '').toLowerCase().trim();

        const pasaTipo = (filtroTipoActual === 'todos' || tipoTarjeta === filtroTipoActual);
        const pasaBuscador = (tituloTarjeta.includes(textoBusqueda) || autorTarjeta.includes(textoBusqueda));
        const pasaEstrellas = (estrellasSeleccionadas === 'todas' || calificacionTarjeta === estrellasSeleccionadas);
        const generoFiltro = generoSeleccionado === 'todos' ? 'todos' : generoSeleccionado;
        const generoComparado = generoFiltro === 'sin-genero' ? '' : generoFiltro;
        const pasaGenero = generoFiltro === 'todos' || generoTarjeta === generoComparado;

        if (pasaTipo && pasaBuscador && pasaEstrellas && pasaGenero) {
            tarjeta.style.display = 'flex';
            elementosVisibles++;
        } else {
            tarjeta.style.display = 'none';
        }
    });

    // Reordenar las tarjetas en el DOM
    tarjetasArray.sort((a, b) => {
        const idA = parseInt(a.getAttribute('data-id')) || 0;
        const idB = parseInt(b.getAttribute('data-id')) || 0;
        const tituloA = a.getAttribute('data-titulo');
        const tituloB = b.getAttribute('data-titulo');
        const califA = parseInt(a.getAttribute('data-calificacion')) || 0;
        const califB = parseInt(b.getAttribute('data-calificacion')) || 0;

        switch (ordenSeleccionado) {
            case 'reciente':
                return idB - idA; // ID autonumerico ascendente
            case 'antiguo':
                return idA - idB;
            case 'nota-desc':
                return califB - califA;
            case 'nota-asc':
                return califA - califB;
            case 'titulo-asc':
                return tituloA.localeCompare(tituloB);
            case 'titulo-desc':
                return tituloB.localeCompare(tituloA);
            default:
                return idB - idA;
        }
    });

    // Reinsertar las tarjetas ordenadas en el contenedor
    tarjetasArray.forEach(tarjeta => contenedorGrid.appendChild(tarjeta));

    // Actualizar el contador
    const contadorBadge = document.getElementById('contador-resultados');
    if (contadorBadge) {
        if (totalElementos === 0) {
            contadorBadge.textContent = "Sin elementos en la colección 🐾";
        } else {
            contadorBadge.textContent = `Mostrando ${elementosVisibles} de ${totalElementos} elementos`;
        }
    }
}



// ==========================================================================
// OPERACIONES ASINCRONAS CON LA API DE PYTHON (FETCH CRUD)
// ==========================================================================

function guardarNuevoElemento(e) {
    e.preventDefault();

    const datos = {
        tipo: document.getElementById('add-tipo').value,
        titulo: document.getElementById('add-titulo').value,
        autor_director: document.getElementById('add-autor').value,
        genero: document.getElementById('add-genero').value,
        calificacion: document.getElementById('add-calificacion').value,
        descripcion: document.getElementById('add-descripcion').value,
        opinion: document.getElementById('add-opinion').value,
        imagen_url: document.getElementById('add-imagen-url').value
    };

    const errorMensaje = validarPayloadElemento(datos);
    if (errorMensaje) {
        Swal.fire({
            icon: 'error',
            title: 'Validación inválida',
            text: errorMensaje,
            confirmButtonColor: '#2c3e50'
        });
        return;
    }

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
                location.reload();
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error al guardar',
                text: resultado.message || 'No se pudo guardar el elemento en la Chihuahuateca.',
                confirmButtonColor: '#2c3e50'
            });
        }
    })
    .catch(err => {
        console.error('Error:', err);
        Swal.fire({
            icon: 'error',
            title: 'Error de servidor',
            text: 'No se pudo conectar con el servidor. Intenta de nuevo más tarde.',
            confirmButtonColor: '#2c3e50'
        });
    });
}

function cargarDatosParaEditar() {
    const idElemento = this.value;
    const formularioEditar = document.getElementById('form-editar');

    if (!idElemento) {
        formularioEditar.classList.add('deshabilitado');
        formularioEditar.reset();
        return;
    }

    fetch(`/api/elemento/${idElemento}`)
    .then(res => res.json())
    .then(data => {
        if (!data.error) {
            document.getElementById('edit-id').value = data.id;
            document.getElementById('edit-tipo').value = data.tipo;
            document.getElementById('edit-titulo').value = data.titulo;
            document.getElementById('edit-autor').value = data.autor_director;
            document.getElementById('edit-genero').value = data.genero || '';
            document.getElementById('edit-calificacion').value = data.calificacion;
            document.getElementById('edit-descripcion').value = data.descripcion;
            document.getElementById('edit-imagen-url').value = data.imagen_url || '';
            actualizarPreviewImagen('edit-imagen-url', 'edit-preview-imagen');
            document.getElementById('edit-opinion').value = data.opinion;

            formularioEditar.classList.remove('deshabilitado');
        }
    })
    .catch(err => console.error('Error:', err));
}

function validarPayloadElemento(datos) {
    const titulo = (datos.titulo || '').trim();
    const tipo = (datos.tipo || '').trim();
    const autor_director = (datos.autor_director || '').trim();
    const calificacion = Number(datos.calificacion);

    if (!titulo) {
        return 'El título es obligatorio.';
    }
    if (!['libro', 'pelicula', 'serie'].includes(tipo)) {
        return 'Selecciona un tipo válido: libro, película o serie.';
    }
    if (!autor_director) {
        return 'El autor / director / creador es obligatorio.';
    }
    if (!Number.isInteger(calificacion) || calificacion < 1 || calificacion > 5) {
        return 'La calificación debe ser un número entero entre 1 y 5.';
    }
    return '';
}

function actualizarPreviewImagen(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    if (!input || !preview) return;

    const url = input.value.trim();
    if (!url) {
        preview.textContent = 'Ingresa una URL válida para ver la vista previa';
        preview.style.backgroundImage = 'none';
        return;
    }

    preview.textContent = '';
    preview.style.backgroundImage = `url('${url}')`;
}

function setBotonCargando(boton, activo) {
    if (!boton) return;
    boton.disabled = activo;
    boton.classList.toggle('btn-cargando', activo);
    boton.textContent = activo ? 'Buscando...' : boton.dataset.originalText || boton.textContent;
}

function buscarDatosExternos(formPrefix, campoObjetivo) {
    const tipo = document.getElementById(`${formPrefix}-tipo`)?.value;
    const titulo = document.getElementById(`${formPrefix}-titulo`)?.value.trim();
    const btnId = `btn-buscar-${campoObjetivo}-${formPrefix}`;
    const boton = document.getElementById(btnId);

    if (!titulo) {
        Swal.fire({ icon: 'warning', title: 'Falta título', text: 'Ingresa el título antes de buscar datos externos.' });
        return;
    }
    if (!tipo || !['libro', 'pelicula', 'serie'].includes(tipo)) {
        Swal.fire({ icon: 'warning', title: 'Tipo inválido', text: 'Selecciona el tipo de elemento antes de buscar.' });
        return;
    }

    if (boton && !boton.dataset.originalText) {
        boton.dataset.originalText = boton.textContent;
    }
    setBotonCargando(boton, true);

    fetch(`/api/buscar-external?tipo=${encodeURIComponent(tipo)}&titulo=${encodeURIComponent(titulo)}`)
        .then(res => res.json())
        .then(data => {
            setBotonCargando(boton, false);
            if (!data.success) {
                Swal.fire({ icon: 'error', title: 'No se encontró', text: data.message || 'No se obtuvieron resultados de búsqueda.' });
                return;
            }

            if (campoObjetivo === 'poster') {
                if (!data.imagen_url) {
                    Swal.fire({ icon: 'info', title: 'Sin portada', text: 'No se encontró una portada o póster para ese título.' });
                    return;
                }
                const imagenInput = document.getElementById(`${formPrefix}-imagen-url`);
                imagenInput.value = data.imagen_url;
                actualizarPreviewImagen(`${formPrefix}-imagen-url`, `${formPrefix}-preview-imagen`);
                Swal.fire({ icon: 'success', title: 'Portada encontrada', text: 'Se actualizó la URL de la imagen automáticamente.' });
                return;
            }

            if (campoObjetivo === 'sinopsis') {
                if (!data.descripcion) {
                    Swal.fire({ icon: 'info', title: 'Sinopsis no encontrada', text: 'No se encontró una sinopsis para ese título.' });
                    return;
                }
                const descripcionInput = document.getElementById(`${formPrefix}-descripcion`);
                descripcionInput.value = data.descripcion;
                Swal.fire({ icon: 'success', title: 'Sinopsis encontrada', text: 'Se completó la sinopsis automáticamente.' });
                return;
            }
        })
        .catch(err => {
            setBotonCargando(boton, false);
            console.error('Error en búsqueda externa:', err);
            Swal.fire({ icon: 'error', title: 'Error de búsqueda', text: 'No se pudo conectar con el servicio de búsqueda externa.' });
        });
}

function actualizarElemento(e) {
    e.preventDefault();

    const datos = {
        id: document.getElementById('edit-id').value,
        tipo: document.getElementById('edit-tipo').value,
        titulo: document.getElementById('edit-titulo').value,
        autor_director: document.getElementById('edit-autor').value,
        genero: document.getElementById('edit-genero').value,
        calificacion: document.getElementById('edit-calificacion').value,
        descripcion: document.getElementById('edit-descripcion').value,
        opinion: document.getElementById('edit-opinion').value,
        imagen_url: document.getElementById('edit-imagen-url').value
    };

    const errorMensaje = validarPayloadElemento(datos);
    if (errorMensaje) {
        Swal.fire({
            icon: 'error',
            title: 'Validación inválida',
            text: errorMensaje,
            confirmButtonColor: '#2c3e50'
        });
        return;
    }

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
                text: resultado.message || 'No se pudieron guardar los cambios.',
                confirmButtonColor: '#2c3e50'
            });
        }
    })
    .catch(err => {
        console.error('Error:', err);
        Swal.fire({
            icon: 'error',
            title: 'Error de servidor',
            text: 'No se pudo conectar con el servidor. Intenta de nuevo más tarde.',
            confirmButtonColor: '#2c3e50'
        });
    });
}

function borrarElemento() {
    const idElemento = document.getElementById('edit-id').value;

    if (!idElemento) return;

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

// Clic sobre la opcion del menu desplegable
const btnCambiarPass = document.getElementById('btn-cambiar-pass');
if (btnCambiarPass) {
    btnCambiarPass.addEventListener('click', function(e) {
        e.preventDefault();
        if (typeof abrirModal === "function") {
            abrirModal('modal-password');
        } else {
            const modalPassword = document.getElementById('modal-password');
            if (modalPassword) {
                modalPassword.classList.add('activo');
            }
        }
    });
}

// Procesar el formulario de cambio de credenciales
const formCambiarPassword = document.getElementById('form-cambiar-password');
if (formCambiarPassword) {
    formCambiarPassword.addEventListener('submit', function(e) {
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
}

