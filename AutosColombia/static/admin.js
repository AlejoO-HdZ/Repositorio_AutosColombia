// static/admin.js
// Gestion Usuarios y Manejo del login
// Gestion de Pagos
// Ajustes UI adicionales: topbar (bienvenida + acciones), posicionamiento de tarifas,
// registro vehículo, botones generar recibo, y pequeñas mejoras visuales.
document.addEventListener('DOMContentLoaded', () => {
  // --- 1) Topbar: actualizar bienvenida y acciones ---
  (function topbarSetup() {
    const welcomeEl = document.getElementById('welcome-text');
    const btnLogout = document.getElementById('btn-logout');
    const btnEditar = document.getElementById('btn-editar-perfil');
    const btnEliminar = document.getElementById('btn-eliminar-cuenta');

    // Si el frontend ya tiene currentUser expuesto, usarlo; si no, esperar a que se establezca.
    function refreshWelcome() {
      try {
        const user = window.currentUser || null;
        if (!welcomeEl) return;
        if (user) {
          const nombre = user.nombre || user.name || user.email || 'Usuario';
          const rol = user.rol || user.role || 'operador';
          welcomeEl.textContent = `Bienvenido, ${nombre} · Rol: ${rol}`;
        } else {
          welcomeEl.textContent = 'Bienvenido';
        }
      } catch (e) { /* no bloquear */ }
    }

    // Intentar refrescar ahora y cada 500ms hasta que currentUser exista (límite 6s)
    refreshWelcome();
    let tries = 0;
    const interval = setInterval(() => {
      refreshWelcome();
      tries++;
      if ((window.currentUser) || tries > 12) clearInterval(interval);
    }, 500);

    // Logout: si existe función global logout en script.js, usarla; si no, limpiar UI localmente
    if (btnLogout) {
      btnLogout.addEventListener('click', () => {
        if (typeof window.logout === 'function') {
          window.logout();
        } else {
          // Fallback: ocultar app y mostrar login
          const appRoot = document.getElementById('app-root');
          const loginRoot = document.getElementById('login-root');
          if (appRoot) appRoot.style.display = 'none';
          if (loginRoot) loginRoot.style.display = 'block';
          // limpiar currentUser
          window.currentUser = null;
          window.isAuthenticated = false;
        }
        // actualizar bienvenida
        if (welcomeEl) welcomeEl.textContent = 'Sesión cerrada';
      });
    }

    // Editar perfil placeholder: si existe función editarPerfil, usarla
    if (btnEditar) {
      btnEditar.addEventListener('click', () => {
        if (typeof window.editarPerfil === 'function') return window.editarPerfil();
        alert('Editar perfil (pendiente).');
      });
    }

    // Eliminar cuenta placeholder
    if (btnEliminar) {
      btnEliminar.addEventListener('click', () => {
        if (typeof window.eliminarCuenta === 'function') return window.eliminarCuenta();
        if (confirm('¿Eliminar su cuenta? Esta acción no se puede deshacer.')) {
          alert('Cuenta eliminada (simulado).');
          if (typeof window.logout === 'function') window.logout();
        }
      });
    }
  })();

  // --- 2) Forzar que el panel de tarifas aparezca a la derecha ---
  (function posicionarPanelTarifas() {
    const row = document.getElementById('entrada-tarifa-row') || document.getElementById('entrada-tarifa-row');
    const registroBlock = document.getElementById('registro-entrada-block');
    const tarifasSide = document.querySelector('.tarifas-side') || document.getElementById('tarifas-side');
    // Usar grid/status-row layout si existe
    const statusRow = document.querySelector('.status-row');
    if (statusRow && tarifasSide) {
      tarifasSide.style.order = '3';
      tarifasSide.style.flex = '0 0 340px';
      tarifasSide.style.minWidth = '260px';
    }
    if (!statusRow && row && registroBlock && tarifasSide) {
      row.style.display = 'flex';
      row.style.flexDirection = 'row';
      row.style.alignItems = 'flex-start';
      row.style.gap = '12px';
      registroBlock.style.order = '1';
      registroBlock.style.flex = '1 1 0';
      tarifasSide.style.order = '2';
      tarifasSide.style.flex = '0 0 340px';
      tarifasSide.style.minWidth = '260px';
    }
  })();

  // --- 3) Auto-cerrar registro de vehículo tras creación exitosa ---
  (function autoCerrarRegistroVehiculo() {
    const crearMensaje = document.getElementById('crear-mensaje');
    const registroVehBlock = document.getElementById('registro-entrada-block') || document.getElementById('registro-vehiculo-block');
    if (!crearMensaje || !registroVehBlock) return;

    const obs = new MutationObserver(muts => {
      muts.forEach(m => {
        const txt = (crearMensaje.textContent || '').toLowerCase();
        if (txt.includes('vehículo creado') || txt.includes('vehículo creado con éxito') || txt.includes('creado con éxito') || txt.includes('creado')) {
          registroVehBlock.style.display = 'none';
          const inputs = registroVehBlock.querySelectorAll('input, select, textarea');
          inputs.forEach(i => {
            if (i.type === 'checkbox') i.checked = false;
            else i.value = '';
          });
          if (typeof window.cargarActivos === 'function') try { window.cargarActivos(); } catch (e) {}
          if (typeof window.cargarHistorial === 'function') try { window.cargarHistorial(); } catch (e) {}
        }
      });
    });
    obs.observe(crearMensaje, { childList: true, characterData: true, subtree: true });
  })();

  // --- 4) Añadir columna de novedad en tablas ya generadas (si falta) ---
  (function asegurarColumnaNovedad() {
    const observerRoot = document.getElementById('app-root') || document.body;
    if (!observerRoot) return;
    const obs = new MutationObserver(() => {
      const activosTable = document.querySelector('#activos-table-card table');
      if (activosTable) {
        const thead = activosTable.querySelector('thead tr');
        if (thead && !thead.querySelector('th.novedad-col')) {
          const th = document.createElement('th');
          th.className = 'novedad-col';
          th.textContent = 'Novedad';
          // Insertar antes de Tarifa si existe
          const tarifaTh = Array.from(thead.children).find(h => /Tarifa/i.test(h.textContent));
          if (tarifaTh) tarifaTh.parentNode.insertBefore(th, tarifaTh);
          else thead.appendChild(th);
        }
      }
      const historialTable = document.getElementById('tabla-historial');
      if (historialTable) {
        const thead = historialTable.querySelector('thead tr');
        if (thead && !thead.querySelector('th.novedad-col')) {
          const th = document.createElement('th');
          th.className = 'novedad-col';
          th.textContent = 'Novedad';
          // Insertar antes de Pagos si existe
          const pagosTh = Array.from(thead.children).find(h => /Pagos/i.test(h.textContent));
          if (pagosTh) pagosTh.parentNode.insertBefore(th, pagosTh);
          else thead.appendChild(th);
        }
      }
    });
    obs.observe(observerRoot, { childList: true, subtree: true });
  })();

  // --- 5) Botón Cobrar y Salida en verde ---
  (function estilizarBotonCobrar() {
    const aplicar = () => {
      const botones = document.querySelectorAll('.btn-salida, #btn-confirmar-cobro');
      botones.forEach(btn => {
        btn.style.backgroundColor = '#16a34a';
        btn.style.color = '#fff';
        btn.style.border = '1px solid rgba(0,0,0,0.06)';
        btn.style.boxShadow = 'none';
      });
    };
    aplicar();
    const obs = new MutationObserver(aplicar);
    obs.observe(document.body, { childList: true, subtree: true });
  })();

  // --- 6) Añadir botón "Generar recibo" en filas de historial y en modal (UI only) ---
  (function agregarBotonGenerarRecibo() {
    // En historial: observar tabla y añadir botones en acciones si no existen
    const tabla = document.getElementById('tabla-historial');
    if (!tabla) return;
    const obs = new MutationObserver(() => {
      const tbody = tabla.querySelector('tbody');
      if (!tbody) return;
      Array.from(tbody.querySelectorAll('tr')).forEach(tr => {
        if (tr.querySelector('.generar-recibo')) return;
        // Añadir celda de acciones si no existe
        const pagosTd = Array.from(tr.children).find(td => td.classList.contains('pagos-cell'));
        const accTd = document.createElement('td');
        accTd.style.whiteSpace = 'nowrap';
        const btn = document.createElement('button');
        btn.className = 'generar-recibo';
        btn.textContent = 'Generar recibo';
        btn.addEventListener('click', () => {
          btn.textContent = 'Recibo (pendiente)';
          setTimeout(() => btn.textContent = 'Generar recibo', 1200);
        });
        accTd.appendChild(btn);
        // Insertar al final de la fila
        tr.appendChild(accTd);
      });
    });
    obs.observe(tabla, { childList: true, subtree: true });

    // Modal: añadir botón si no existe
    const cobroModal = document.getElementById('cobro-modal');
    if (cobroModal) {
      const footer = cobroModal.querySelector('.form-actions') || cobroModal.querySelector('.modal-footer') || cobroModal.querySelector('div');
      if (footer && !cobroModal.querySelector('.btn-generar-recibo')) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn-generar-recibo';
        btn.textContent = 'Generar recibo';
        btn.style.marginLeft = '8px';
        btn.addEventListener('click', () => {
          btn.textContent = 'Recibo (pendiente)';
          setTimeout(() => btn.textContent = 'Generar recibo', 1200);
        });
        footer.appendChild(btn);
      }
    }
  })();

  // --- 7) Mejoras de visualización: evitar desbordes y ajustar tablas ---
  (function mejorarVisualizacion() {
    // Añadir clase para tablas scrollables si son anchas
    const tables = document.querySelectorAll('table');
    tables.forEach(t => {
      const wrapper = document.createElement('div');
      wrapper.style.overflowX = 'auto';
      wrapper.style.width = '100%';
      wrapper.style.marginBottom = '8px';
      if (t.parentNode && !t.parentNode.classList.contains('table-wrapper')) {
        t.parentNode.insertBefore(wrapper, t);
        wrapper.appendChild(t);
        wrapper.classList.add('table-wrapper');
      }
    });

    // Ajustar celdas largas: truncar texto en novedades y pagos
    const style = document.createElement('style');
    style.innerHTML = `
      td.novedad-cell, td.pagos-cell { max-width: 260px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .table-wrapper { margin-bottom: 10px; }
    `;
    document.head.appendChild(style);
  })();

  // --- 8) Integración con búsqueda de placa: foco y comportamiento ---
  (function integrarBusquedaPlaca() {
    const btnBuscar = document.getElementById('btn-buscar-placa');
    const inputBuscar = document.getElementById('buscar-placa-input');
    if (btnBuscar && typeof window.buscarPlaca === 'function') {
      btnBuscar.addEventListener('click', () => {
        window.buscarPlaca();
      });
    } else if (btnBuscar && inputBuscar) {
      // fallback: trigger enter key on input to reuse existing handlers
      btnBuscar.addEventListener('click', () => {
        inputBuscar.dispatchEvent(new Event('input'));
      });
    }
  })();

  // --- 9) Mensaje en consola sobre ejecución local ---
  console.info('Admin UI helper cargado: topbar, posicionamiento y mejoras visuales aplicadas.');

});