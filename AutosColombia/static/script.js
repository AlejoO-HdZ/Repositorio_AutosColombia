// static/script.js
/* CAPA DE PRESENTACION */
document.addEventListener('DOMContentLoaded', function(){
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
  const nuevoTipoNovedad = document.getElementById('nuevo-tipo-novedad');
  const nuevoDescripcionNovedad = document.getElementById('nuevo-descripcion-novedad');

  const entradaPlaca = document.getElementById('entrada-placa');
  const entradaTipo = document.getElementById('entrada-tipo');
  const entradaTipoNovedad = document.getElementById('entrada-tipo-novedad');
  const entradaDescripcionNovedad = document.getElementById('entrada-descripcion-novedad');
  const btnRegistrarEntrada = document.getElementById('btn-registrar-entrada');
  const entradaMensaje = document.getElementById('entrada-mensaje');

  const salidaId = document.getElementById('salida-id');
  const salidaPlaca = document.getElementById('salida-placa');
  const salidaHoraEntrada = document.getElementById('salida-hora-entrada');
  const salidaTipoNovedad = document.getElementById('salida-tipo-novedad');
  const salidaDescripcion = document.getElementById('salida-descripcion');
  const btnRegistrarSalida = document.getElementById('btn-registrar-salida');
  const salidaMensaje = document.getElementById('salida-mensaje');

  const btnVolver1 = document.getElementById('btn-volver-1');
  const btnVolver2 = document.getElementById('btn-volver-2');
  const btnVolver3 = document.getElementById('btn-volver-3');

  const resumenEstadisticas = document.getElementById('resumen-estadisticas');
  const tablaHistorialBody = document.querySelector('#tabla-historial tbody');
  const listaActivos = document.getElementById('lista-activos');

  function resetMensajes(){
    consultaMensaje.textContent = '';
    crearMensaje.textContent = '';
    entradaMensaje.textContent = '';
    salidaMensaje.textContent = '';
  }

  function ocultarBloques(){
    registroVehBlock.style.display = 'none';
    registroEntradaBlock.style.display = 'none';
    registroSalidaBlock.style.display = 'none';
  }

  async function cargarHistorial(){
    const res = await fetch('/api/historial');
    const data = await res.json();
    const rows = data.historial || [];
    tablaHistorialBody.innerHTML = '';
    let activos = 0;
    rows.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${r.id}</td>
        <td>${r.placa}</td>
        <td>${r.tipo || ''}</td>
        <td>${r.marca || ''}</td>
        <td>${r.hora_entrada || ''}</td>
        <td>${r.hora_salida || ''}</td>
        <td><span class="badge ${r.estado === 'activo' ? 'activo' : 'cerrado'}">${r.estado}</span></td>
        <td>
          ${r.estado === 'activo' ? `<button class="btn-accion" data-id="${r.id}" data-placa="${r.placa}">Registrar salida</button>` : ''}
        </td>
      `;
      tablaHistorialBody.appendChild(tr);
      if(r.estado === 'activo') activos++;
    });

    resumenEstadisticas.innerHTML = '';
    const total = rows.length;
    resumenEstadisticas.appendChild(crearCard('Vehículos activos', activos));
    resumenEstadisticas.appendChild(crearCard('Registros totales', total));

    document.querySelectorAll('.btn-accion').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.id;
        const placa = btn.dataset.placa;
        abrirBloqueSalida(id, placa);
      });
    });
  }

  function crearCard(titulo, valor){
    const div = document.createElement('div');
    div.className = 'resumen-card';
    div.innerHTML = `<h4>${titulo}</h4><p>${valor}</p>`;
    return div;
  }

  // Cargar lista de activos y tipos de novedad
  async function cargarActivosYTipos(){
    // activos
    try{
      const res = await fetch('/api/activos');
      const data = await res.json();
      const activos = data.activos || [];
      listaActivos.innerHTML = '';
      if(activos.length === 0){
        listaActivos.textContent = 'No hay vehículos activos.';
      } else {
        const ul = document.createElement('ul');
        ul.style.listStyle = 'none';
        ul.style.padding = '0';
        activos.forEach(a => {
          const li = document.createElement('li');
          li.style.padding = '8px';
          li.style.borderBottom = '1px solid #eef2ff';
          li.innerHTML = `<strong>${a.placa}</strong> — ${a.tipo || 'N/A'} — ${a.hora_entrada}`;
          ul.appendChild(li);
        });
        listaActivos.appendChild(ul);
      }
    }catch(e){
      listaActivos.textContent = 'Error cargando activos.';
    }

    // tipos de novedad (llenar selects)
    try{
      // usamos la consulta de una placa genérica para obtener tipos (o podríamos crear endpoint específico)
      const res2 = await fetch('/api/vehiculo/XXX');
      const data2 = await res2.json();
      const tipos = data2.tipos_novedad || [];
      // limpiar y llenar
      [nuevoTipoNovedad, entradaTipoNovedad, salidaTipoNovedad].forEach(sel => {
        if(!sel) return;
        sel.innerHTML = '<option value="">-- Ninguna --</option>';
        tipos.forEach(t => {
          const opt = document.createElement('option');
          opt.value = t.id;
          opt.textContent = t.nombre;
          sel.appendChild(opt);
        });
      });
    }catch(e){
      // si falla, dejamos selects con la opción por defecto
    }
  }

  btnConsultar.addEventListener('click', async () => {
    resetMensajes();
    ocultarBloques();
    const placa = (inputPlaca.value || '').trim().toUpperCase();
    if(!placa){
      consultaMensaje.textContent = 'Ingrese una placa válida.';
      return;
    }
    consultaMensaje.textContent = 'Consultando...';
    try{
      const res = await fetch(`/api/vehiculo/${encodeURIComponent(placa)}`);
      const data = await res.json();
      consultaMensaje.textContent = '';
      if(data.vehiculo){
        const veh = data.vehiculo;
        const registro = data.registro_activo;
        if(registro){
          abrirBloqueSalida(registro.id, placa, registro.hora_entrada, data.tipos_novedad);
        } else {
          abrirBloqueEntrada(veh, data.tipos_novedad);
        }
      } else {
        nuevoPlaca.value = placa;
        registroVehBlock.style.display = 'flex';
        // llenar tipos de novedad en formulario de creación
        if(data.tipos_novedad){
          nuevoTipoNovedad.innerHTML = '<option value="">-- Ninguna --</option>';
          data.tipos_novedad.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = t.nombre;
            nuevoTipoNovedad.appendChild(opt);
          });
        }
      }
    }catch(err){
      consultaMensaje.textContent = 'Error al consultar. Intente de nuevo.';
    }
  });

  btnCrearVehiculo.addEventListener('click', async () => {
    resetMensajes();
    const placa = (nuevoPlaca.value || '').trim().toUpperCase();
    const tipo = (nuevoTipo.value || '').trim();
    const color = nuevoColor.value || '';
    const marca = nuevoMarca.value || '';
    const tipo_novedad = nuevoTipoNovedad.value || null;
    const descripcion_novedad = nuevoDescripcionNovedad.value || null;
    if(!placa || !tipo){
      crearMensaje.textContent = 'Placa y tipo son obligatorios.';
      return;
    }
    crearMensaje.textContent = 'Creando vehículo...';
    try{
      const res = await fetch('/api/vehiculo', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({placa, tipo, color, marca})
      });
      const data = await res.json();
      if(!data.ok){
        crearMensaje.textContent = 'Error: ' + (data.error || 'No se pudo crear');
        return;
      }
      // Registrar entrada con novedad opcional
      const res2 = await fetch('/api/registro/entrada', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({placa, descripcion: descripcion_novedad, tipo_id: tipo_novedad})
      });
      const d2 = await res2.json();
      if(!d2.ok){
        crearMensaje.textContent = 'Vehículo creado, pero error al registrar entrada: ' + (d2.error || '');
        return;
      }
      crearMensaje.textContent = 'Vehículo creado y entrada registrada.';
      ocultarBloques();
      inputPlaca.value = '';
      await cargarHistorial();
      await cargarActivosYTipos();
    }catch(err){
      crearMensaje.textContent = 'Error en la operación.';
    }
  });

  function abrirBloqueEntrada(veh, tiposNovedadServer){
    ocultarBloques();
    entradaPlaca.textContent = veh.placa;
    entradaTipo.textContent = veh.tipo || '';
    // llenar select de tipos de novedad
    let tipos = tiposNovedadServer || [];
    if(!tipos || tipos.length === 0){
      // intentar obtener desde API
      fetch(`/api/vehiculo/${encodeURIComponent(veh.placa)}`)
        .then(r => r.json())
        .then(d => {
          tipos = d.tipos_novedad || [];
          entradaTipoNovedad.innerHTML = '<option value="">-- Ninguna --</option>';
          tipos.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = t.nombre;
            entradaTipoNovedad.appendChild(opt);
          });
        }).catch(()=>{});
    } else {
      entradaTipoNovedad.innerHTML = '<option value="">-- Ninguna --</option>';
      tipos.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = t.nombre;
        entradaTipoNovedad.appendChild(opt);
      });
    }
    registroEntradaBlock.style.display = 'flex';
  }

  btnRegistrarEntrada.addEventListener('click', async () => {
    resetMensajes();
    const placa = entradaPlaca.textContent;
    const tipo_novedad = entradaTipoNovedad.value || null;
    const descripcion_novedad = entradaDescripcionNovedad.value || null;
    entradaMensaje.textContent = 'Registrando entrada...';
    try{
      const res = await fetch('/api/registro/entrada', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({placa, descripcion: descripcion_novedad, tipo_id: tipo_novedad})
      });
      const data = await res.json();
      if(!data.ok){
        entradaMensaje.textContent = 'Error: ' + (data.error || '');
        return;
      }
      entradaMensaje.textContent = 'Entrada registrada correctamente.';
      ocultarBloques();
      inputPlaca.value = '';
      entradaDescripcionNovedad.value = '';
      await cargarHistorial();
      await cargarActivosYTipos();
    }catch(err){
      entradaMensaje.textContent = 'Error al registrar entrada.';
    }
  });

  async function abrirBloqueSalida(id, placa, horaEntrada, tiposNovedadServer){
    ocultarBloques();
    salidaId.textContent = id;
    salidaPlaca.textContent = placa;
    salidaHoraEntrada.textContent = horaEntrada || '';
    let tipos = tiposNovedadServer || [];
    if(!tipos || tipos.length === 0){
      const res = await fetch(`/api/vehiculo/${encodeURIComponent(placa)}`);
      const data = await res.json();
      tipos = data.tipos_novedad || [];
    }
    salidaTipoNovedad.innerHTML = '<option value="">-- Ninguna --</option>';
    tipos.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.textContent = t.nombre;
      salidaTipoNovedad.appendChild(opt);
    });
    registroSalidaBlock.style.display = 'flex';
  }

  btnRegistrarSalida.addEventListener('click', async () => {
    resetMensajes();
    const registro_id = salidaId.textContent;
    const tipo_id = salidaTipoNovedad.value || null;
    const descripcion = salidaDescripcion.value || null;
    salidaMensaje.textContent = 'Registrando salida...';
    try{
      const res = await fetch('/api/registro/salida', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({registro_id, tipo_id, descripcion})
      });
      const data = await res.json();
      if(!data.ok){
        salidaMensaje.textContent = 'Error: ' + (data.error || '');
        return;
      }
      salidaMensaje.textContent = 'Salida registrada correctamente.';
      ocultarBloques();
      inputPlaca.value = '';
      salidaDescripcion.value = '';
      await cargarHistorial();
      await cargarActivosYTipos();
    }catch(err){
      salidaMensaje.textContent = 'Error al registrar salida.';
    }
  });

  [btnVolver1, btnVolver2, btnVolver3].forEach(b => {
    b.addEventListener('click', () => {
      ocultarBloques();
      inputPlaca.value = '';
      resetMensajes();
    });
  });

  ocultarBloques();
  cargarHistorial();
  cargarActivosYTipos();
});