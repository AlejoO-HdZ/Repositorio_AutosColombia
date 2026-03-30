// static/script.js
/* CAPA DE PRESENTACION */
// Versión completa :
// - Manejo de token en login (si backend devuelve token).
// - Editar / Eliminar con Authorization si hay token, o con cookies si backend usa sesión.
// - Asegura clases y bindings para botones Editar/Eliminar/Cerrar.
// - Limpia mensajes antiguos al abrir modal de cobro y al mostrar formulario de entrada.
// - Flujo vehículo/entrada robusto.
// - Gestion listado de tarifas y pagos

(function () {
  'use strict';

  /* ---------- Helpers DOM ---------- */
  function qs(sel, root = document) { return (root || document).querySelector(sel); }
  function qsa(sel, root = document) { return Array.from((root || document).querySelectorAll(sel)); }
  function el(tag, attrs = {}, children = []) {
    const e = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([k, v]) => {
      if (k === 'text') e.textContent = v;
      else if (k === 'html') e.innerHTML = v;
      else e.setAttribute(k, v);
    });
    (Array.isArray(children) ? children : [children]).forEach(c => {
      if (!c) return;
      if (typeof c === 'string') e.appendChild(document.createTextNode(c));
      else e.appendChild(c);
    });
    return e;
  }

  /* ---------- Utilities ---------- */
  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
  function normPlaca(raw) { return (raw || '').toString().trim().toUpperCase(); }
  function apiOk(res) { return res && (res.ok === true || res.success === true); }

  /* ---------- API fetch wrapper (incluye token si existe) ---------- */
  window.authToken = null;
  async function apiFetchJson(path, opts = {}) {
    const headers = Object.assign({}, opts.headers || {});
    if (window.authToken) headers['Authorization'] = 'Bearer ' + window.authToken;
    if (!headers['Content-Type'] && opts.body) headers['Content-Type'] = 'application/json';
    try {
      const r = await fetch(path, Object.assign({ credentials: 'same-origin' }, opts, { headers }));
      const text = await r.text();
      try { return { status: r.status, json: text ? JSON.parse(text) : null }; } catch (e) { return { status: r.status, json: null }; }
    } catch (e) {
      console.error('apiFetchJson error', e);
      return { status: 0, json: null };
    }
  }
  async function apiGet(path) { const r = await apiFetchJson(path, { method: 'GET' }); return r.json; }
  async function apiPost(path, body) { const r = await apiFetchJson(path, { method: 'POST', body: JSON.stringify(body || {}) }); return r.json; }
  async function apiPut(path, body) { const r = await apiFetchJson(path, { method: 'PUT', body: JSON.stringify(body || {}) }); return r.json; }
  async function apiDelete(path) { const r = await apiFetchJson(path, { method: 'DELETE' }); return r.json; }

  /* ---------- UI helpers ---------- */
  function showMessage(text, selector = '#login-mensaje') {
    const elMsg = qs(selector);
    if (elMsg) elMsg.textContent = text;
    else console.log('MSG:', text);
  }

  window.currentUser = null;

  function updateWelcome() {
    const welcome = qs('#welcome-text');
    const label = qs('.welcome-label');
    if (!welcome || !label) return;
    const u = window.currentUser;
    if (u) {
      const nombre = u.nombre || u.name || u.email || 'Usuario';
      const rol = (u.rol || u.role || 'operador').toString();
      label.textContent = 'Bienvenido';
      label.style.fontWeight = '700';
      label.style.color = 'var(--accent)';
      welcome.textContent = `${rol} · ${nombre}`;
      welcome.style.fontWeight = '700';
      welcome.style.color = 'var(--accent)';
    } else {
      label.textContent = 'Bienvenido';
      welcome.textContent = 'operador · Usuario';
    }
  }

  /* ---------- Cargas (tarifas, celdas, activos, historial) ---------- */
  async function cargarCeldas() {
    try {
      const data = await apiGet('/api/celdas');
      const sel = qs('#entrada-celda');
      const list = qs('#celdas-list');
      if (sel) {
        sel.innerHTML = '<option value="">(Seleccionar o dejar vacío para asignación automática)</option>';
        if (data && Array.isArray(data.celdas)) {
          data.celdas.filter(c => c.estado === 'disponible').forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.textContent = `#${c.id} ${c.descripcion || ''}`;
            sel.appendChild(opt);
          });
        }
      }
      if (list) {
        if (!data || !Array.isArray(data.celdas)) list.innerHTML = '<div>No hay celdas</div>';
        else {
          const estados = { disponible:0, ocupada:0, reservada:0, bloqueada:0 };
          data.celdas.forEach(c => { if (c.estado && estados.hasOwnProperty(c.estado)) estados[c.estado]++; });
          list.innerHTML = `<div style="display:flex;gap:12px;flex-wrap:wrap">
            <div class="resumen-card"><h4>Disponibles</h4><p style="color:#0f5132">${estados.disponible}</p></div>
            <div class="resumen-card"><h4>Ocupadas</h4><p style="color:#7c2d12">${estados.ocupada}</p></div>
            <div class="resumen-card"><h4>Reservadas</h4><p style="color:#0f5132">${estados.reservada}</p></div>
            <div class="resumen-card"><h4>Bloqueadas</h4><p style="color:#7c2d12">${estados.bloqueada}</p></div>
          </div>`;
        }
      }
    } catch (e) { console.error('cargarCeldas error', e); }
  }

  async function cargarTarifas() {
    try {
      const data = await apiGet('/api/tarifas');
      const sel = qs('#entrada-tarifa');
      const list = qs('#tarifas-list');
      if (sel) {
        sel.innerHTML = '<option value="">(Seleccionar tarifa)</option>';
        if (data && Array.isArray(data.tarifas)) {
          data.tarifas.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = `${t.nombre} — ${Number(t.valor).toFixed(2)} (${t.tipo})`;
            sel.appendChild(opt);
          });
        }
      }
      if (list) {
        list.innerHTML = '';
        if (!data || !Array.isArray(data.tarifas)) list.appendChild(el('div', { text: 'No hay tarifas' }));
        else data.tarifas.forEach(t => {
          const item = el('div', { class: 'tarifa-item', html: `<div><strong>${t.nombre}</strong><div class="meta">${t.tipo}</div></div><div style="text-align:right"><div class="tarifa-valor">${Number(t.valor).toFixed(2)}</div></div>` });
          list.appendChild(item);
        });
      }
    } catch (e) { console.error('cargarTarifas error', e); }
  }

  async function cargarActivos() {
    try {
      const data = await apiGet('/api/activos');
      const cont = qs('#activos-block');
      if (!cont) return;
      cont.innerHTML = '';
      const activos = (data && data.activos) ? data.activos : [];
      const table = el('table');
      const thead = el('thead'); thead.innerHTML = '<tr><th>Placa</th><th>Entrada</th><th>Celda</th><th>Tipo</th><th>Novedad</th><th>Tarifa</th><th>Acción</th></tr>';
      const tbody = el('tbody');
      if (activos.length === 0) tbody.innerHTML = '<tr><td colspan="7">No hay vehículos activos</td></tr>';
      else activos.forEach(a => {
        const tr = el('tr');
        tr.appendChild(el('td', { text: a.placa || '' }));
        tr.appendChild(el('td', { text: a.hora_entrada || '' }));
        tr.appendChild(el('td', { text: a.celda_descripcion || (a.celda_id ? ('#' + a.celda_id) : 'Sin asignar') }));
        tr.appendChild(el('td', { text: a.tipo || '' }));
        tr.appendChild(el('td', { class: 'novedad-cell', text: a.novedad || '-' }));
        tr.appendChild(el('td', { text: a.tarifa_valor != null ? Number(a.tarifa_valor).toFixed(2) : '-' }));
        const tdAcc = el('td');
        const btnCobrar = el('button', { class: 'btn-salida', text: 'Cobrar y Salida' });
        btnCobrar.addEventListener('click', () => abrirModalCobro(a));
        tdAcc.appendChild(btnCobrar);
        tr.appendChild(tdAcc);
        tbody.appendChild(tr);
      });
      table.appendChild(thead); table.appendChild(tbody);
      const wrapper = el('div', { class: 'table-wrapper' });
      wrapper.appendChild(table);
      cont.appendChild(wrapper);
    } catch (e) { console.error('cargarActivos error', e); }
  }

  async function cargarHistorial() {
    try {
      const data = await apiGet('/api/historial');
      const tabla = qs('#tabla-historial'); if (!tabla) return;
      const tbody = tabla.querySelector('tbody'); const thead = tabla.querySelector('thead');
      tbody.innerHTML = '';
      thead.innerHTML = '<tr><th>Placa</th><th>Entrada</th><th>Salida</th><th>Estado</th><th>Precio cobrado</th><th>Pagos</th><th>Acción</th></tr>';
      const rows = (data && data.historial) ? data.historial : [];
      const pagosAllRes = await apiGet('/api/pagos?limit=1000'); const pagosAll = (pagosAllRes && pagosAllRes.pagos) ? pagosAllRes.pagos : [];
      const totalRecaudado = pagosAll.reduce((s, p) => s + (parseFloat(p.monto || 0) || 0), 0);
      for (const r of rows) {
        const tr = el('tr');
        tr.appendChild(el('td', { text: r.placa || '' }));
        tr.appendChild(el('td', { text: r.hora_entrada || '' }));
        tr.appendChild(el('td', { text: r.hora_salida || '' }));
        tr.appendChild(el('td', { text: r.estado || '' }));
        tr.appendChild(el('td', { text: r.tarifa_valor != null ? Number(r.tarifa_valor).toFixed(2) : '-' }));
        const tdPagos = el('td', { class: 'pagos-cell', text: 'Cargando...' });
        tr.appendChild(tdPagos);

        const tdAcc = el('td');
        const btnRecibo = el('button', { class: 'btn-receipt-soft', text: 'Generar recibo' });
        btnRecibo.addEventListener('click', () => {
          btnRecibo.textContent = 'Generando...';
          setTimeout(() => btnRecibo.textContent = 'Generar recibo', 900);
        });
        tdAcc.appendChild(btnRecibo);
        tr.appendChild(tdAcc);

        tbody.appendChild(tr);

        (async function (registroId, td) {
          try {
            if (r.pagos && Array.isArray(r.pagos)) {
              if (r.pagos.length === 0) td.textContent = '-';
              else td.innerHTML = r.pagos.map(p => `${p.fecha} — ${Number(p.monto).toFixed(2)} (${p.metodo||'--'})`).join('<br>');
              return;
            }
            const pagosRes = await apiGet('/api/pago/registro/' + encodeURIComponent(registroId));
            const pagos = (pagosRes && pagosRes.pagos) ? pagosRes.pagos : [];
            if (pagos.length === 0) td.textContent = '-';
            else td.innerHTML = pagos.map(p => `${p.fecha} — ${Number(p.monto).toFixed(2)} (${p.metodo||'--'})`).join('<br>');
          } catch (e) { td.textContent = '-'; }
        })(r.id, tdPagos);
      }

      let tfoot = tabla.querySelector('tfoot'); if (!tfoot) { tfoot = el('tfoot'); tabla.appendChild(tfoot); }
      tfoot.innerHTML = '';
      const trTotal = el('tr');
      const tdLabel = el('td', { text: 'Total recaudado (historial):' }); tdLabel.colSpan = 5; tdLabel.style.textAlign = 'right'; tdLabel.style.fontWeight = '700';
      trTotal.appendChild(tdLabel);
      const tdValue = el('td', { text: Number(totalRecaudado).toFixed(2) }); tdValue.colSpan = 2; tdValue.style.fontWeight = '700';
      trTotal.appendChild(tdValue);
      tfoot.appendChild(trTotal);
    } catch (e) { console.error('cargarHistorial error', e); }
  }

  /* ---------- Cobro modal ---------- */
  function abrirModalCobro(registro) {
    const modal = qs('#cobro-modal'); if (!modal) return;
    // limpiar mensajes previos
    const cobroMsg = qs('#cobro-mensaje'); if (cobroMsg) cobroMsg.textContent = '';
    qs('#cobro-registro-id').textContent = registro.id || '';
    qs('#cobro-placa').textContent = registro.placa || '';
    qs('#cobro-monto').textContent = 'Calculando...';
    qs('#cobro-novedad') && (qs('#cobro-novedad').value = '');
    qs('#cobro-metodo') && (qs('#cobro-metodo').value = 'efectivo');
    modal.style.display = 'flex';
    fetch(`/api/registro/${encodeURIComponent(registro.id)}/calcular_monto`)
      .then(r => r.json())
      .then(d => {
        if (d && d.ok && d.monto_calculado != null) qs('#cobro-monto').textContent = Number(d.monto_calculado).toFixed(2);
        else qs('#cobro-monto').textContent = registro.tarifa_valor != null ? Number(registro.tarifa_valor).toFixed(2) : '-';
      }).catch(() => {
        qs('#cobro-monto').textContent = registro.tarifa_valor != null ? Number(registro.tarifa_valor).toFixed(2) : '-';
      });
  }
  function cerrarModalCobro() { const modal = qs('#cobro-modal'); if (!modal) return; modal.style.display = 'none'; }

  async function confirmarCobro() {
    const registroId = qs('#cobro-registro-id').textContent;
    const montoText = qs('#cobro-monto').textContent;
    const metodo = qs('#cobro-metodo').value;
    const novedad = qs('#cobro-novedad').value || null;
    const monto = parseFloat((montoText || '').replace(',', '')) || 0;
    const cobroMsg = qs('#cobro-mensaje');
    if (cobroMsg) cobroMsg.textContent = '';
    if (!registroId) return;
    try {
      const pagoRes = await apiPost('/api/pago', { registro_id: Number(registroId), monto: monto, metodo: metodo, detalle: novedad });
      if (!apiOk(pagoRes)) { if (cobroMsg) cobroMsg.textContent = 'Error al crear pago.'; return; }
      if (novedad) {
        try { await apiPost('/api/novedad', { registro_id: Number(registroId), descripcion: novedad }); } catch (e) {}
      }
      const salidaRes = await apiPost('/api/registro/salida', { registro_id: Number(registroId) });
      if (!apiOk(salidaRes)) { if (cobroMsg) cobroMsg.textContent = 'Pago registrado pero error al cerrar registro.'; cerrarModalCobro(); await cargarActivos(); await cargarHistorial(); return; }
      if (cobroMsg) cobroMsg.textContent = 'Cobro y salida registrados correctamente.';
      setTimeout(() => { cerrarModalCobro(); cargarActivos(); cargarHistorial(); cargarListadoPagos(); }, 600);
    } catch (e) { console.error('confirmarCobro error', e); if (cobroMsg) cobroMsg.textContent = 'Error interno.'; }
  }

  /* ---------- Vehículo: crear y entrada ---------- */
  async function crearVehiculoInlineYContinuar() {
    const placaEl = qs('#nuevo-placa-inline');
    const tipoEl = qs('#nuevo-tipo-inline');
    const marcaEl = qs('#nuevo-marca-inline');
    const colorEl = qs('#nuevo-color-inline');
    const msg = qs('#crear-veh-inline-mensaje');

    const placa = normPlaca(placaEl && placaEl.value);
    const tipo = (tipoEl && tipoEl.value) || '';
    const marca = (marcaEl && marcaEl.value) || null;
    const color = (colorEl && colorEl.value) || null;

    if (!placa || !tipo) { if (msg) msg.textContent = 'Placa y tipo requeridos.'; return; }
    if (msg) msg.textContent = 'Creando vehículo...';

    try {
      const crear = await apiPost('/api/vehiculo', { placa: placa, tipo: tipo, marca: marca, color: color });
      if (!apiOk(crear)) {
        if (msg) msg.textContent = 'Error creando vehículo: ' + (crear && (crear.error || crear.message) ? (crear.error || crear.message) : JSON.stringify(crear));
        return;
      }

      // confirmar existencia
      let confirmado = false;
      for (let i = 0; i < 6; i++) {
        const check = await apiGet('/api/vehiculo/' + encodeURIComponent(placa));
        if (apiOk(check) && check.vehiculo) { confirmado = true; break; }
        await sleep(400);
      }
      if (!confirmado) {
        if (msg) msg.textContent = 'Vehículo creado pero no confirmado aún. Intenta de nuevo en unos segundos.';
        return;
      }

      if (msg) msg.textContent = 'Vehículo creado correctamente. Complete los datos de entrada.';
      qs('#crear-vehiculo-inline') && (qs('#crear-vehiculo-inline').style.display = 'none');
      qs('#form-entrada-block') && (qs('#form-entrada-block').style.display = 'block');
      const entradaPlaca = qs('#entrada-placa'); if (entradaPlaca) entradaPlaca.value = placa;
      // limpiar mensaje de entrada anterior
      const entradaMsg = qs('#entrada-mensaje'); if (entradaMsg) entradaMsg.textContent = '';
      await cargarCeldas(); await cargarTarifas();
      const tarifaSel = qs('#entrada-tarifa'); if (tarifaSel) tarifaSel.focus();
    } catch (e) {
      console.error('crearVehiculoInlineYContinuar error', e);
      if (msg) msg.textContent = 'Error interno al crear vehículo.';
    }
  }

  async function registrarEntrada() {
    const placa = normPlaca(qs('#entrada-placa') && qs('#entrada-placa').value);
    const descripcion = (qs('#entrada-descripcion') && qs('#entrada-descripcion').value) || null;
    const celdaId = (qs('#entrada-celda') && qs('#entrada-celda').value) || null;
    const tarifaId = (qs('#entrada-tarifa') && qs('#entrada-tarifa').value) || null;
    const autoCelda = qs('#entrada-auto-celda') ? qs('#entrada-auto-celda').checked : true;
    const msg = qs('#entrada-mensaje');

    if (msg) msg.textContent = '';
    if (!placa) { if (msg) msg.textContent = 'Placa requerida.'; return; }

    try {
      const vehCheck = await apiGet('/api/vehiculo/' + encodeURIComponent(placa));
      if (!apiOk(vehCheck) || !vehCheck.vehiculo) {
        qs('#crear-vehiculo-inline') && (qs('#crear-vehiculo-inline').style.display = 'block');
        qs('#nuevo-placa-inline') && (qs('#nuevo-placa-inline').value = placa);
        if (msg) msg.textContent = 'Vehículo no existe. Cree el vehículo antes de registrar la entrada.';
        return;
      }
    } catch (e) {
      console.error('verificar vehiculo error', e);
      if (msg) msg.textContent = 'Error verificando vehículo.';
      return;
    }

    const body = { placa: placa, descripcion: descripcion };
    if (!autoCelda && celdaId) body.celda_id = Number(celdaId);
    if (tarifaId) body.tarifa_id = Number(tarifaId);

    let attempts = 0;
    const maxAttempts = 3;
    while (attempts < maxAttempts) {
      attempts++;
      try {
        const res = await apiPost('/api/registro/entrada', body);
        if (apiOk(res)) {
          if (msg) msg.textContent = 'Entrada registrada correctamente.';
          qs('#form-entrada-block') && (qs('#form-entrada-block').style.display = 'none');
          await cargarActivos(); await cargarHistorial(); await cargarCeldas();
          return;
        } else {
          const errText = (res && (res.error || res.message)) ? String(res.error || res.message) : JSON.stringify(res);
          if (errText.includes('1452') || errText.toLowerCase().includes('foreign key') || errText.toLowerCase().includes('registro_ibfk_1')) {
            if (attempts < maxAttempts) {
              if (msg) msg.textContent = `Error FK al registrar (intento ${attempts}). Reintentando...`;
              await sleep(600);
              continue;
            } else {
              if (msg) msg.textContent = 'Error registrando entrada: vehículo no encontrado (FK). Cree el vehículo primero.';
              return;
            }
          } else {
            if (msg) msg.textContent = 'Error registrando entrada: ' + errText;
            return;
          }
        }
      } catch (e) {
        console.error('registrarEntrada error', e);
        if (attempts < maxAttempts) {
          if (msg) msg.textContent = `Error interno (intento ${attempts}). Reintentando...`;
          await sleep(600);
          continue;
        } else {
          if (msg) msg.textContent = 'Error interno al registrar entrada.';
          return;
        }
      }
    }
  }

  /* ---------- Buscar placa ---------- */
  async function buscarPlaca() {
    const input = qs('#buscar-placa-input'); const result = qs('#buscar-placa-result');
    if (!input || !result) return;
    const placa = normPlaca(input.value);
    qs('#form-entrada-block') && (qs('#form-entrada-block').style.display = 'none');
    qs('#crear-vehiculo-inline') && (qs('#crear-vehiculo-inline').style.display = 'none');
    result.textContent = 'Buscando...';
    if (!placa) { result.textContent = 'Ingrese una placa válida.'; return; }

    try {
      const res = await apiGet('/api/vehiculo/' + encodeURIComponent(placa));
      if (!apiOk(res) || !res.vehiculo) {
        result.innerHTML = `<div style="color:var(--muted)">Vehículo no encontrado. Complete los datos para registrarlo y luego registrar la entrada.</div>`;
        qs('#crear-vehiculo-inline') && (qs('#crear-vehiculo-inline').style.display = 'block');
        qs('#nuevo-placa-inline') && (qs('#nuevo-placa-inline').value = placa);
        qs('#form-entrada-block') && (qs('#form-entrada-block').style.display = 'none');
        await cargarCeldas();
        await cargarTarifas();
        return;
      }

      const veh = res.vehiculo || null;
      const reg = res.registro_activo || null;
      let html = `<div><strong>Placa:</strong> ${placa}</div>`;
      if (veh) html += `<div class="meta">Tipo: ${veh.tipo || '-'} · Marca: ${veh.marca || '-'} · Color: ${veh.color || '-'}</div>`;
      if (reg) {
        html += `<div style="margin-top:6px"><strong>Registro activo:</strong> Entrada: ${reg.hora_entrada || '-'} · Celda: ${reg.celda_id || '-'}</div>`;
        result.innerHTML = html;
        const btnSalida = el('button', { class: 'btn-accent', text: 'Registrar salida' });
        btnSalida.addEventListener('click', () => abrirModalCobro(reg));
        result.appendChild(btnSalida);
      } else {
        html += `<div style="margin-top:6px;color:var(--muted)">Vehículo registrado y sin registro activo. Puede registrar la entrada.</div>`;
        result.innerHTML = html;
        qs('#form-entrada-block') && (qs('#form-entrada-block').style.display = 'block');
        const entradaPlaca = qs('#entrada-placa'); if (entradaPlaca) entradaPlaca.value = placa;
        // limpiar mensaje de entrada anterior
        const entradaMsg = qs('#entrada-mensaje'); if (entradaMsg) entradaMsg.textContent = '';
        await cargarCeldas();
        await cargarTarifas();
      }
    } catch (e) {
      console.error('buscarPlaca error', e);
      result.textContent = 'Error buscando placa.';
    }
  }

  /* ---------- Editar / Eliminar usuario (manejo de autorización) ---------- */
  async function handleEditarPerfil() {
    const user = window.currentUser;
    if (!user) { alert('No hay usuario autenticado.'); return; }
    const id = user.id || user.user_id || null;
    const currentName = user.nombre || user.name || '';
    const currentRole = user.rol || user.role || 'operador';

    const nuevoNombre = prompt('Nuevo nombre:', currentName);
    if (nuevoNombre === null) return;
    const nuevoRol = prompt('Nuevo rol (operador/empleado/admin):', currentRole);
    if (nuevoRol === null) return;

    const msgEl = qs('#login-mensaje') || qs('#reg-mensaje');
    if (msgEl) msgEl.textContent = 'Actualizando usuario...';

    try {
      let res = null;
      if (id) {
        // usar Authorization si existe token, si no, confiar en cookies de sesión
        const headers = {};
        if (window.authToken) headers['Authorization'] = 'Bearer ' + window.authToken;
        const r = await fetch('/api/usuario/' + encodeURIComponent(id), {
          method: 'PUT',
          credentials: 'same-origin',
          headers: Object.assign({ 'Content-Type': 'application/json' }, headers),
          body: JSON.stringify({ nombre: nuevoNombre.trim(), rol: nuevoRol.trim() })
        });
        if (r.status === 401 || r.status === 403) { if (msgEl) msgEl.textContent = 'No autorizado.'; alert('No autorizado para editar.'); return; }
        res = await (r.headers.get('content-type') && r.headers.get('content-type').includes('application/json') ? r.json() : null);
      } else {
        res = await apiPost('/api/usuario/update', { nombre: nuevoNombre.trim(), rol: nuevoRol.trim(), email: user.email || null });
      }

      if (!res) { if (msgEl) msgEl.textContent = 'Error: sin respuesta del servidor.'; alert('No se pudo actualizar: sin respuesta'); return; }
      if (!apiOk(res)) {
        const err = res && (res.error || res.message) ? (res.error || res.message) : 'Error actualizando usuario';
        if (msgEl) msgEl.textContent = err;
        alert('No se pudo actualizar: ' + err);
        return;
      }

      window.currentUser = Object.assign({}, window.currentUser, { nombre: nuevoNombre.trim(), rol: nuevoRol.trim() });
      updateWelcome();
      if (msgEl) msgEl.textContent = 'Perfil actualizado.';
      alert('Perfil actualizado correctamente.');
    } catch (e) {
      console.error('handleEditarPerfil error', e);
      if (msgEl) msgEl.textContent = 'Error interno al actualizar.';
      alert('Error interno al actualizar perfil.');
    }
  }

  async function handleEliminarCuenta() {
    const user = window.currentUser;
    if (!user) { alert('No hay usuario autenticado.'); return; }
    if (!confirm('¿Confirma que desea eliminar su cuenta? Esta acción no se puede deshacer.')) return;
    const id = user.id || user.user_id || null;
    const msgEl = qs('#login-mensaje') || qs('#reg-mensaje');
    if (msgEl) msgEl.textContent = 'Eliminando cuenta...';
    try {
      let res = null;
      if (id) {
        const headers = {};
        if (window.authToken) headers['Authorization'] = 'Bearer ' + window.authToken;
        const r = await fetch('/api/usuario/' + encodeURIComponent(id), {
          method: 'DELETE',
          credentials: 'same-origin',
          headers: headers
        });
        if (r.status === 401 || r.status === 403) { if (msgEl) msgEl.textContent = 'No autorizado.'; alert('No autorizado para eliminar.'); return; }
        res = await (r.headers.get('content-type') && r.headers.get('content-type').includes('application/json') ? r.json() : {});
      } else {
        res = await apiPost('/api/usuario/delete', { email: user.email || null, nombre: user.nombre || null });
      }

      if (!res) { if (msgEl) msgEl.textContent = 'Error: sin respuesta del servidor.'; alert('No se pudo eliminar: sin respuesta'); return; }
      if (!apiOk(res)) {
        const err = res && (res.error || res.message) ? (res.error || res.message) : 'Error eliminando cuenta';
        if (msgEl) msgEl.textContent = err;
        alert('No se pudo eliminar la cuenta: ' + err);
        return;
      }

      window.currentUser = null;
      window.authToken = null;
      updateWelcome();
      hideApp();
      if (msgEl) msgEl.textContent = 'Cuenta eliminada.';
      alert('Cuenta eliminada correctamente (si el backend la procesó).');
    } catch (e) {
      console.error('handleEliminarCuenta error', e);
      if (msgEl) msgEl.textContent = 'Error interno al eliminar cuenta.';
      alert('Error interno al eliminar cuenta.');
    }
  }

  /* ---------- Login / registro ---------- */
  async function handleLogin() {
    const idEl = qs('#login-identifier'); const pwEl = qs('#login-password'); const msg = qs('#login-mensaje');
    if (!idEl || !pwEl) return;
    const identifier = (idEl.value || '').trim(); const password = (pwEl.value || '').trim();
    if (!identifier || !password) { if (msg) msg.textContent = 'Usuario y contraseña requeridos.'; return; }
    try {
      const r = await fetch('/api/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'same-origin', body: JSON.stringify({ nombre: identifier, password: password }) });
      const data = await (r.headers.get('content-type') && r.headers.get('content-type').includes('application/json') ? r.json() : null);
      if (!data || !data.ok) { if (msg) msg.textContent = data && data.error ? data.error : 'Credenciales inválidas'; return; }
      window.currentUser = data.user || null;
      if (data.token) window.authToken = data.token;
      if (msg) msg.textContent = 'Inicio de sesión correcto.';
      showApp();
      updateWelcome();
      await cargarTarifas(); await cargarCeldas(); await cargarActivos(); await cargarHistorial(); await cargarListadoPagos();
      // asegurar botones de usuario y bindings
      ensureUserButtons();
      bindUserButtons();
    } catch (e) { console.error('login error', e); if (msg) msg.textContent = 'Error interno al iniciar sesión.'; }
  }

  function logout() {
    window.currentUser = null; window.authToken = null;
    hideApp();
    qs('#login-identifier') && (qs('#login-identifier').value = '');
    qs('#login-password') && (qs('#login-password').value = '');
    qs('#login-mensaje') && (qs('#login-mensaje').textContent = 'Sesión cerrada.');
  }

  async function handleRegistrarUsuario() {
    const nombre = (qs('#reg-nombre') || {}).value || '';
    const email = (qs('#reg-email') || {}).value || '';
    const password = (qs('#reg-password') || {}).value || '';
    const rol = (qs('#reg-rol') || {}).value || 'operador';
    const msgEl = qs('#reg-mensaje');
    if (!nombre || !password) { if (msgEl) msgEl.textContent = 'Nombre y contraseña son obligatorios.'; return; }
    try {
      const res = await apiPost('/api/usuario', { nombre: nombre.trim(), email: email.trim() || null, password: password, rol: rol });
      if (!apiOk(res)) { if (msgEl) msgEl.textContent = res && (res.error || res.message) ? (res.error || res.message) : 'Error creando usuario'; return; }
      if (msgEl) msgEl.textContent = 'Usuario creado correctamente. Ya puedes iniciar sesión.';
      qs('#register-block') && (qs('#register-block').style.display = 'none');
    } catch (e) { console.error('registrar usuario error', e); if (msgEl) msgEl.textContent = 'Error interno al crear usuario.'; }
  }

  /* ---------- Pagos listado ---------- */
  async function cargarListadoPagos() {
    try {
      const res = await apiGet('/api/pagos?limit=1000');
      const pagos = (res && res.pagos) ? res.pagos : [];
      const cont = qs('#pagos-listado'); if (!cont) return;
      cont.innerHTML = '';
      if (pagos.length === 0) { cont.appendChild(el('div', { text: 'No hay pagos registrados' })); return; }
      pagos.forEach(p => {
        const item = el('div', { class: 'pagos-item', html: `<div><strong>${p.placa || ('Registro ' + p.registro_id)}</strong></div><div class="meta">${p.fecha} · ${Number(p.monto).toFixed(2)} · ${p.metodo || '--'}</div>` });
        cont.appendChild(item);
      });
      const total = pagos.reduce((s, p) => s + (parseFloat(p.monto || 0) || 0), 0);
      cont.appendChild(el('div', { style: 'margin-top:10px;font-weight:700', text: 'Total pagos: ' + Number(total).toFixed(2) }));
    } catch (e) { console.error('cargarListadoPagos error', e); }
  }

  /* ---------- Ensure user buttons classes and binding ---------- */
  function ensureUserButtons() {
    const btnEdit = qs('#btn-editar-perfil');
    const btnDelete = qs('#btn-eliminar-cuenta');
    const btnLogout = qs('#btn-logout');

    if (btnEdit && !btnEdit.classList.contains('btn-edit-soft')) btnEdit.classList.add('btn-edit-soft');
    if (btnDelete && !btnDelete.classList.contains('btn-delete-soft')) btnDelete.classList.add('btn-delete-soft');
    if (btnLogout && !btnLogout.classList.contains('btn-logout-soft')) btnLogout.classList.add('btn-logout-soft');
  }

  function bindUserButtons() {
    const btnEdit = qs('#btn-editar-perfil');
    const btnDelete = qs('#btn-eliminar-cuenta');
    const btnLogout = qs('#btn-logout');

    if (btnEdit) { btnEdit.removeEventListener('click', handleEditarPerfil); btnEdit.addEventListener('click', handleEditarPerfil); }
    if (btnDelete) { btnDelete.removeEventListener('click', handleEliminarCuenta); btnDelete.addEventListener('click', handleEliminarCuenta); }
    if (btnLogout) { btnLogout.removeEventListener('click', logout); btnLogout.addEventListener('click', logout); }
  }

  /* ---------- Bind events general ---------- */
  function bindEventos() {
    qs('#btn-login') && qs('#btn-login').addEventListener('click', handleLogin);
    qs('#btn-toggle-register') && qs('#btn-toggle-register').addEventListener('click', () => { const r = qs('#register-block'); if (r) r.style.display = r.style.display === 'none' ? 'block' : 'none'; });
    qs('#btn-cancelar-registrar') && qs('#btn-cancelar-registrar').addEventListener('click', () => { const r = qs('#register-block'); if (r) r.style.display = 'none'; });
    qs('#btn-registrar-usuario') && qs('#btn-registrar-usuario').addEventListener('click', handleRegistrarUsuario);

    qs('#btn-buscar-placa') && qs('#btn-buscar-placa').addEventListener('click', buscarPlaca);
    qs('#btn-limpiar-busqueda') && qs('#btn-limpiar-busqueda').addEventListener('click', () => {
      qs('#buscar-placa-input') && (qs('#buscar-placa-input').value = '');
      qs('#buscar-placa-result') && (qs('#buscar-placa-result').textContent = '');
      qs('#form-entrada-block') && (qs('#form-entrada-block').style.display = 'none');
      qs('#crear-vehiculo-inline') && (qs('#crear-vehiculo-inline').style.display = 'none');
    });

    qs('#btn-crear-vehiculo-inline') && qs('#btn-crear-vehiculo-inline').addEventListener('click', crearVehiculoInlineYContinuar);
    qs('#btn-registrar-entrada') && qs('#btn-registrar-entrada').addEventListener('click', registrarEntrada);
    qs('#btn-crear-tarifa') && qs('#btn-crear-tarifa').addEventListener('click', async () => {
      const nombre = (qs('#tar-nombre') && qs('#tar-nombre').value) || '';
      const tipo = (qs('#tar-tipo') && qs('#tar-tipo').value) || 'por_hora';
      const valor = parseFloat((qs('#tar-valor') && qs('#tar-valor').value) || 0) || 0;
      try { const d = await apiPost('/api/tarifa', { nombre: nombre, tipo: tipo, valor: valor }); if (!apiOk(d)) { alert('Error creando tarifa: ' + (d && (d.error || d.message) ? (d.error || d.message) : JSON.stringify(d))); return; } await cargarTarifas(); } catch (e) { console.error('crear tarifa error', e); }
    });

    qs('#btn-refrescar-historial') && qs('#btn-refrescar-historial').addEventListener('click', () => { cargarHistorial(); cargarActivos(); cargarListadoPagos(); });
    qs('#btn-confirmar-cobro') && qs('#btn-confirmar-cobro').addEventListener('click', confirmarCobro);
    qs('#btn-cancelar-cobro') && qs('#btn-cancelar-cobro').addEventListener('click', cerrarModalCobro);
    qs('#btn-generar-recibo-modal') && qs('#btn-generar-recibo-modal').addEventListener('click', () => {
      const btn = qs('#btn-generar-recibo-modal');
      btn.textContent = 'Generando...';
      setTimeout(() => btn.textContent = 'Generar recibo', 900);
    });

    // asegurar botones de usuario
    ensureUserButtons();
    bindUserButtons();
  }

  /* ---------- Init ---------- */
  function showApp() {
    qs('#login-root') && (qs('#login-root').style.display = 'none');
    qs('#app-root') && (qs('#app-root').style.display = 'block');
    updateWelcome();
  }
  function hideApp() {
    qs('#login-root') && (qs('#login-root').style.display = 'block');
    qs('#app-root') && (qs('#app-root').style.display = 'none');
  }

  function init() {
    bindEventos();
    hideApp();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();

  /* ---------- Expose for debugging ---------- */
  window.cargarActivos = cargarActivos;
  window.cargarHistorial = cargarHistorial;
  window.cargarListadoPagos = cargarListadoPagos;
  window.abrirModalCobro = abrirModalCobro;
  window.ensureUserButtons = ensureUserButtons;
  window.bindUserButtons = bindUserButtons;

})();