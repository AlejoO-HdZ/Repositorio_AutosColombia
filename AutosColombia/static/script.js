// static/script.js
/* CAPA DE PRESENTACION */
document.addEventListener('DOMContentLoaded', function () {
  // Elementos
  const inputPlaca = document.getElementById('input-placa');
  const btnConsultar = document.getElementById('btn-consultar');
  const consultaMensaje = document.getElementById('consulta-mensaje');

  const registroVehBlock = document.getElementById('registro-vehiculo-block');
  const registroEntradaBlock = document.getElementById('registro-entrada-block');
  const registroSalidaBlock = document.getElementById('registro-salida-block');

  const nuevoPlaca = document.getElementById('nuevo-placa');
  const nuevoTipo = document.getElementById('nuevo-tipo');
  const nuevoColor = document.getElementById('nuevo-color');
  const nuevoMarca = document.getElementById('nuevo-marca');
  const btnCrearVehiculo = document.getElementById('btn-crear-vehiculo');
  const crearMensaje = document.getElementById('crear-mensaje');

  const entradaPlaca = document.getElementById('entrada-placa');
  const entradaNovedad = document.getElementById('entrada-novedad');
  const btnRegistrarEntrada = document.getElementById('btn-registrar-entrada');
  const entradaMensaje = document.getElementById('entrada-mensaje');
  const entradaCeldaSelect = document.getElementById('entrada-celda-select');
  const entradaAutoCheckbox = document.getElementById('entrada-auto-checkbox');

  const salidaId = document.getElementById('salida-id');
  const salidaPlaca = document.getElementById('salida-placa');
  const salidaDescripcion = document.getElementById('salida-descripcion');
  const btnRegistrarSalida = document.getElementById('btn-registrar-salida');
  const salidaMensaje = document.getElementById('salida-mensaje');

  const tablaBody = document.querySelector('#tabla-historial tbody');
  const tablaHead = document.querySelector('#tabla-historial thead');
  const resumenEstadisticas = document.getElementById('resumen-estadisticas');

  const btnVolver1 = document.getElementById('btn-volver-1');
  const btnVolver2 = document.getElementById('btn-volver-2');
  const btnVolver3 = document.getElementById('btn-volver-3');

  function ocultarBloques() {
    if (registroVehBlock) registroVehBlock.style.display = 'none';
    if (registroEntradaBlock) registroEntradaBlock.style.display = 'none';
    if (registroSalidaBlock) registroSalidaBlock.style.display = 'none';
  }

  // Escape simple para evitar inyección en HTML/title
  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str).replace(/[&<>"'`=\/]/g, function (s) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;', '/': '&#x2F;', '`': '&#x60;', '=': '&#x3D;' })[s];
    });
  }

  // Cuando el usuario inicia sesión, la app principal dispara este evento
  window.addEventListener('user-logged-in', (e) => {
    cargarHistorial();
    cargarActivos();
  });

  // Consultar placa
  if (btnConsultar) {
    btnConsultar.addEventListener('click', async () => {
      consultaMensaje.textContent = '';
      ocultarBloques();
      const placa = (inputPlaca.value || '').trim().toUpperCase();
      if (!placa) { consultaMensaje.textContent = 'Ingrese placa'; return; }
      consultaMensaje.textContent = 'Consultando...';
      try {
        const res = await fetch('/api/vehiculo/' + encodeURIComponent(placa));
        const txt = await res.text(); let data = null; try { data = JSON.parse(txt); } catch (e) { data = null; }
        if (!res.ok) { consultaMensaje.textContent = (data && data.error) ? data.error : 'Error al consultar'; return; }
        if (data.vehiculo) {
          // Vehículo registrado: permitir registrar entrada o novedad
          entradaPlaca.textContent = placa;
          entradaNovedad.value = '';
          // Cargar celdas y preparar selector
          await cargarCeldasEnSelect();
          // Por defecto, asignación automática activada
          if (entradaAutoCheckbox) {
            entradaAutoCheckbox.checked = true;
            entradaCeldaSelect.disabled = true;
          }
          registroEntradaBlock.style.display = 'block';
        } else {
          // No registrado: mostrar formulario de registro
          nuevoPlaca.value = placa;
          registroVehBlock.style.display = 'block';
        }
      } catch (e) {
        consultaMensaje.textContent = 'Error de red';
        console.error('Consultar placa error', e);
      }
    });
  }

  // Habilitar/deshabilitar select de celda según checkbox
  if (entradaAutoCheckbox) {
    entradaAutoCheckbox.addEventListener('change', () => {
      if (!entradaCeldaSelect) return;
      entradaCeldaSelect.disabled = entradaAutoCheckbox.checked;
      if (entradaAutoCheckbox.checked) {
        entradaCeldaSelect.value = '';
      }
    });
  }

  // Cargar celdas en el select de entrada
  async function cargarCeldasEnSelect() {
    if (!entradaCeldaSelect) return;
    try {
      const res = await fetch('/api/celdas');
      const txt = await res.text(); let data = null; try { data = JSON.parse(txt); } catch (e) { data = null; }
      if (!res.ok) {
        entradaCeldaSelect.innerHTML = '<option value="">Automático (error al cargar celdas)</option>';
        return;
      }
      const celdas = (data && data.celdas) ? data.celdas : [];
      // Primer opción: automático
      entradaCeldaSelect.innerHTML = '<option value="">Automático (recomendado)</option>';
      celdas.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = `${c.descripcion} — ${c.estado}`;
        // Si la celda no está disponible, marcarla como deshabilitada para selección manual
        if (c.estado !== 'disponible') {
          opt.disabled = true;
          opt.textContent += ' (no disponible)';
        }
        entradaCeldaSelect.appendChild(opt);
      });
    } catch (e) {
      console.error('cargarCeldasEnSelect error', e);
      entradaCeldaSelect.innerHTML = '<option value="">Automático (error)</option>';
    }
  }

  // Crear vehículo y registrar entrada (manejo duplicado)
  if (btnCrearVehiculo) {
    btnCrearVehiculo.addEventListener('click', async () => {
      crearMensaje.textContent = '';
      const placa = (nuevoPlaca.value || '').trim().toUpperCase();
      const tipo = (nuevoTipo.value || '').trim();
      if (!placa || !tipo) { crearMensaje.textContent = 'Placa y tipo obligatorios'; return; }
      crearMensaje.textContent = 'Creando vehículo...';
      try {
        const res = await fetch('/api/vehiculo', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ placa, tipo, color: nuevoColor.value, marca: nuevoMarca.value })
        });
        const text = await res.text(); let data = null; try { data = JSON.parse(text); } catch (e) { data = null; }

        if (res.status === 409 || (data && data.error === 'vehiculo_existente')) {
          // Vehículo ya existe: registrar entrada
          crearMensaje.textContent = 'Vehículo ya existe. Registrando entrada...';
          const res2 = await fetch('/api/registro/entrada', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ placa, descripcion: null, tipo_id: null, celda_id: null })
          });
          const txt2 = await res2.text(); let d2 = null; try { d2 = JSON.parse(txt2); } catch (e) { d2 = null; }
          if (!res2.ok) { crearMensaje.textContent = 'Error al registrar entrada: ' + ((d2 && d2.error) ? d2.error : txt2); return; }
          crearMensaje.textContent = 'Entrada registrada para vehículo existente.';
          ocultarBloques(); inputPlaca.value = ''; await cargarHistorial(); await cargarActivos();
          return;
        }

        if (!res.ok) {
          crearMensaje.textContent = (data && data.error) ? data.error : 'Error al crear vehículo';
          return;
        }

        // Vehículo creado -> registrar entrada (automática)
        crearMensaje.textContent = 'Vehículo creado. Registrando entrada...';
        const res3 = await fetch('/api/registro/entrada', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ placa, descripcion: null, tipo_id: null, celda_id: null })
        });
        const txt3 = await res3.text(); let d3 = null; try { d3 = JSON.parse(txt3); } catch (e) { d3 = null; }
        if (!res3.ok) { crearMensaje.textContent = 'Veh creado, pero error al registrar entrada: ' + ((d3 && d3.error) ? d3.error : txt3); return; }
        crearMensaje.textContent = 'Vehículo creado y entrada registrada';
        ocultarBloques(); inputPlaca.value = ''; await cargarHistorial(); await cargarActivos();
      } catch (e) {
        crearMensaje.textContent = 'Error de red';
        console.error('Crear vehiculo exception', e);
      }
    });
  }

  // Registrar entrada (desde bloque)
  if (btnRegistrarEntrada) {
    btnRegistrarEntrada.addEventListener('click', async () => {
      entradaMensaje.textContent = 'Registrando...';
      const placa = entradaPlaca.textContent;
      const descripcion = (entradaNovedad.value || '').trim() || null;
      // Si auto está marcado, enviar celda_id null para que el backend asigne
      const auto = entradaAutoCheckbox ? entradaAutoCheckbox.checked : true;
      const celda_id = (!auto && entradaCeldaSelect && entradaCeldaSelect.value) ? entradaCeldaSelect.value : null;
      try {
        const res = await fetch('/api/registro/entrada', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ placa, descripcion, tipo_id: null, celda_id: celda_id })
        });
        const txt = await res.text(); let data = null; try { data = JSON.parse(txt); } catch (e) { data = null; }
        if (!res.ok) { entradaMensaje.textContent = (data && data.error) ? data.error : 'Error al registrar entrada'; return; }
        entradaMensaje.textContent = 'Entrada registrada';
        ocultarBloques(); await cargarHistorial(); await cargarActivos();
      } catch (e) {
        entradaMensaje.textContent = 'Error de red';
        console.error('Registrar entrada error', e);
      }
    });
  }

  // Abrir bloque salida
  function abrirSalida(id, placa) {
    ocultarBloques();
    salidaId.textContent = id;
    salidaPlaca.textContent = placa;
    salidaDescripcion.value = '';
    registroSalidaBlock.style.display = 'block';
  }

  // Registrar salida
  if (btnRegistrarSalida) {
    btnRegistrarSalida.addEventListener('click', async () => {
      salidaMensaje.textContent = 'Registrando salida...';
      const registro_id = salidaId.textContent;
      const descripcion = (salidaDescripcion.value || '').trim() || null;
      try {
        const res = await fetch('/api/registro/salida', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ registro_id, descripcion, tipo_id: null })
        });
        const txt = await res.text(); let data = null; try { data = JSON.parse(txt); } catch (e) { data = null; }
        if (!res.ok) { salidaMensaje.textContent = (data && data.error) ? data.error : 'Error al registrar salida'; return; }
        salidaMensaje.textContent = 'Salida registrada';
        ocultarBloques(); await cargarHistorial(); await cargarActivos();
      } catch (e) {
        salidaMensaje.textContent = 'Error de red';
        console.error('Registrar salida error', e);
      }
    });
  }

  // Volver botones
  [btnVolver1, btnVolver2, btnVolver3].forEach(b => { if (!b) return; b.addEventListener('click', () => { ocultarBloques(); }) });

  // Cargar historial (sin mostrar ID)
  async function cargarHistorial() {
    try {
      const res = await fetch('/api/historial');
      const txt = await res.text(); let data = null; try { data = JSON.parse(txt); } catch (e) { data = null; }
      if (!res.ok) { if (tablaBody) tablaBody.innerHTML = '<tr><td colspan="5">Error cargando historial</td></tr>'; return; }
      const rows = data.historial || [];

      // Ajustar encabezado para no mostrar ID
      if (tablaHead) {
        tablaHead.innerHTML = '<tr><th>Placa</th><th>Entrada</th><th>Salida</th><th>Estado</th><th>Acción</th></tr>';
      }

      if (tablaBody) tablaBody.innerHTML = '';
      rows.forEach(r => {
        const tr = document.createElement('tr');
        const estadoBadge = `<span class="badge ${r.estado === 'activo' ? 'activo' : 'cerrado'}">${r.estado}</span>`;
        const accionHtml = r.estado === 'activo' ? `<button class="action-btn" data-id="${r.id}" data-placa="${r.placa}">Registrar salida</button>` : '';
        tr.innerHTML = `<td>${escapeHtml(r.placa)}</td><td>${escapeHtml(r.hora_entrada || '')}</td><td>${escapeHtml(r.hora_salida || '')}</td><td>${estadoBadge}</td><td>${accionHtml}</td>`;
        tablaBody.appendChild(tr);
      });
      document.querySelectorAll('.action-btn').forEach(btn => btn.addEventListener('click', () => abrirSalida(btn.dataset.id, btn.dataset.placa)));

      // actualizar resumen
      const activosCount = rows.filter(r => r.estado === 'activo').length;
      resumenEstadisticas.innerHTML = '';
      resumenEstadisticas.appendChild(crearCard('Vehículos activos', activosCount));
      resumenEstadisticas.appendChild(crearCard('Registros totales', rows.length));
      // también mostrar tabla de activos detallada
      await renderActivosTable();
    } catch (e) {
      console.error('cargarHistorial error', e);
      if (tablaBody) tablaBody.innerHTML = '<tr><td colspan="5">Error cargando historial</td></tr>';
    }
  }

  function crearCard(titulo, valor) {
    const div = document.createElement('div');
    div.className = 'resumen-card';
    div.innerHTML = `<h4>${escapeHtml(titulo)}</h4><p>${escapeHtml(String(valor))}</p>`;
    return div;
  }

  // Cargar activos y renderizar tabla con placa, celda asignada, hora entrada, novedad y botón registrar salida
  async function cargarActivos() {
    try {
      const res = await fetch('/api/activos');
      const txt = await res.text(); let data = null; try { data = JSON.parse(txt); } catch (e) { data = null; }
      if (!res.ok) { console.error('Error cargarActivos', txt); return; }
      const activos = data.activos || [];
      // Obtener celdas para mapear id -> descripcion (por si el backend no trae celda_descripcion)
      const celdasRes = await fetch('/api/celdas');
      const celdasTxt = await celdasRes.text(); let celdasData = null; try { celdasData = JSON.parse(celdasTxt); } catch (e) { celdasData = null; }
      const celdasList = (celdasData && celdasData.celdas) ? celdasData.celdas : [];
      const celdaMap = {};
      celdasList.forEach(c => { celdaMap[c.id] = c.descripcion; });

      // Construir tabla de activos dentro un card
      const existing = document.getElementById('activos-table-card');
      if (existing) existing.remove();

      const card = document.createElement('div');
      card.className = 'resumen-card';
      card.id = 'activos-table-card';
      card.style.gridColumn = '1 / -1';
      card.innerHTML = `<h4>Activos</h4>`;

      const table = document.createElement('table');
      table.style.width = '100%';
      table.style.borderCollapse = 'collapse';
      table.innerHTML = `<thead><tr style="background:#f8fafc"><th style="padding:8px;text-align:left">Placa</th><th style="padding:8px;text-align:left">Celda</th><th style="padding:8px;text-align:left">Entrada</th><th style="padding:8px;text-align:left">Novedad</th><th style="padding:8px;text-align:left">Acción</th></tr></thead><tbody></tbody>`;
      const tbody = table.querySelector('tbody');

      activos.forEach(a => {
        const tr = document.createElement('tr');
        const celdaCodigo = a.celda_descripcion || (a.celda_id ? (celdaMap[a.celda_id] || ('#' + a.celda_id)) : 'Sin asignar');
        // Novedad: si el backend no la incluye, mostramos '-' (puedo actualizar backend para incluirla)
        const novText = a.novedad || '-';
        const novHtml = (novText && novText !== '-') ? `<span class="novedad" title="${escapeHtml(novText)}">${escapeHtml(novText)}</span>` : '-';
        tr.innerHTML = `<td style="padding:8px;border-bottom:1px solid #f1f5f9">${escapeHtml(a.placa)}</td>
                        <td style="padding:8px;border-bottom:1px solid #f1f5f9">${escapeHtml(celdaCodigo)}</td>
                        <td style="padding:8px;border-bottom:1px solid #f1f5f9">${escapeHtml(a.hora_entrada || '')}</td>
                        <td style="padding:8px;border-bottom:1px solid #f1f5f9">${novHtml}</td>
                        <td style="padding:8px;border-bottom:1px solid #f1f5f9">${a.id ? `<button class="action-btn activo-salida" data-id="${a.id}" data-placa="${escapeHtml(a.placa)}">Registrar salida</button>` : ''}</td>`;
        tbody.appendChild(tr);
      });

      card.appendChild(table);
      resumenEstadisticas.appendChild(card);

      // Attach handlers for salida buttons
      document.querySelectorAll('.activo-salida').forEach(btn => btn.addEventListener('click', () => abrirSalida(btn.dataset.id, btn.dataset.placa)));
    } catch (e) {
      console.error('cargarActivos error', e);
    }
  }

  // Renderizar tabla de activos (llama a cargarActivos internamente)
  async function renderActivosTable() {
    await cargarActivos();
  }

  // Inicial
  ocultarBloques();
  cargarHistorial();
  cargarActivos();

  // Exponer funciones para debug o uso externo
  window.cargarHistorial = cargarHistorial;
  window.cargarActivos = cargarActivos;
});