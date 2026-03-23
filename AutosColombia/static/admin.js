// static/admin.js
document.addEventListener('DOMContentLoaded', function () {
  // Elementos del panel de inicio / registro
  const adminNombre = document.getElementById('admin-nombre');
  const adminPassword = document.getElementById('admin-password');
  const btnLogin = document.getElementById('btn-login');
  const btnShowRegister = document.getElementById('btn-show-register');
  const registerArea = document.getElementById('register-area');
  const btnCancelRegister = document.getElementById('btn-cancel-register');
  const regNombre = document.getElementById('reg-nombre');
  const regEmail = document.getElementById('reg-email');
  const regRol = document.getElementById('reg-rol');
  const regPassword = document.getElementById('reg-password');
  const btnRegistrar = document.getElementById('btn-registrar');
  const loginMensaje = document.getElementById('login-mensaje');
  const registerMensaje = document.getElementById('register-mensaje');

  // Barra de usuario activo
  const activeBar = document.getElementById('active-user-bar');
  const activeUsername = document.getElementById('active-username');
  const activeRole = document.getElementById('active-role');
  const btnEditUser = document.getElementById('btn-edit-user');
  const btnDeleteUser = document.getElementById('btn-delete-user');
  const btnLogout = document.getElementById('btn-logout');

  // Modal de edición
  const editModal = document.getElementById('edit-user-modal');
  const editNombre = document.getElementById('edit-nombre');
  const editEmail = document.getElementById('edit-email');
  const editPassword = document.getElementById('edit-password');
  const btnGuardarEd = document.getElementById('btn-guardar-edicion');
  const btnCancelarEd = document.getElementById('btn-cancelar-edicion');
  const editarMensaje = document.getElementById('editar-mensaje');

  // App main y panel original
  const appMain = document.getElementById('app-main');
  const adminPanel = document.getElementById('admin-panel');

  // Helpers de localStorage
  function setToken(t) { if (t) localStorage.setItem('parq_token', t); else localStorage.removeItem('parq_token'); }
  function getToken() { return localStorage.getItem('parq_token') || null; }
  function setUser(u) { if (u) localStorage.setItem('parq_user', JSON.stringify(u)); else localStorage.removeItem('parq_user'); }
  function getUser() { const u = localStorage.getItem('parq_user'); return u ? JSON.parse(u) : null; }

  // Mostrar/ocultar registro
  btnShowRegister.addEventListener('click', () => { registerArea.style.display = 'block'; });
  btnCancelRegister.addEventListener('click', () => { registerArea.style.display = 'none'; });

  // Registro de usuario (envía rol seleccionado)
  btnRegistrar.addEventListener('click', async () => {
    registerMensaje.textContent = '';
    const nombre = (regNombre.value || '').trim();
    const email = (regEmail.value || '').trim() || null;
    const rol = (regRol.value || 'operador').trim();
    const password = (regPassword.value || '').trim();
    if (!nombre || !password) { registerMensaje.textContent = 'Nombre y password obligatorios.'; return; }
    registerMensaje.textContent = 'Creando usuario...';
    try {
      const res = await fetch('/api/usuario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre, email, password, rol })
      });
      const txt = await res.text();
      let data = null; try { data = JSON.parse(txt); } catch (e) { data = null; }
      if (!res.ok) {
        registerMensaje.textContent = (data && data.error) ? data.error : 'Error al crear usuario';
        return;
      }
      registerMensaje.textContent = 'Usuario creado. Inicia sesión.';
      regNombre.value = ''; regEmail.value = ''; regPassword.value = ''; regRol.value = 'operador';
      registerArea.style.display = 'none';
    } catch (e) {
      registerMensaje.textContent = 'Error de red';
      console.error('Registrar error', e);
    }
  });

  // Login
  btnLogin.addEventListener('click', async () => {
    loginMensaje.textContent = '';
    const nombre = (adminNombre.value || '').trim();
    const password = (adminPassword.value || '').trim();
    if (!nombre || !password) { loginMensaje.textContent = 'Nombre y password requeridos.'; return; }
    loginMensaje.textContent = 'Iniciando sesión...';
    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre, password })
      });
      const txt = await res.text();
      let data = null; try { data = JSON.parse(txt); } catch (e) { data = null; }
      if (!res.ok) {
        loginMensaje.textContent = (data && data.error) ? data.error : 'Error al iniciar sesión';
        return;
      }
      // Guardar token y usuario
      setToken(data.token || '');
      const user = data.user || { nombre: nombre, rol: (data.role || 'operador'), id: data.user_id || null };
      setUser(user);

      // Mostrar bienvenida y barra de usuario
      showActiveUser(user);

      // Emitir evento para que la app principal cargue datos
      window.dispatchEvent(new CustomEvent('user-logged-in', { detail: user }));

      // Eliminar panel de inicio y mostrar app principal
      if (adminPanel && adminPanel.parentNode) adminPanel.parentNode.removeChild(adminPanel);
      appMain.style.display = 'block';

      adminNombre.value = ''; adminPassword.value = '';
      loginMensaje.textContent = '';
    } catch (e) {
      loginMensaje.textContent = 'Error de red';
      console.error('Login error', e);
    }
  });

  // Mostrar la barra de usuario con mensaje "Bienvenido <Usuario>" en color llamativo
  function showActiveUser(user) {
    const nombre = user.nombre || user.name || 'Usuario';
    activeUsername.innerHTML = `<span style="color:var(--accent);font-weight:800">Bienvenido ${escapeHtml(nombre)}</span>`;
    activeRole.textContent = user.rol ? ` ${user.rol}` : '';
    activeBar.style.display = 'flex';
  }

  // Escape simple para evitar inyección en el innerHTML
  function escapeHtml(str) {
    return String(str).replace(/[&<>"'`=\/]/g, function (s) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;', '/': '&#x2F;', '`': '&#x60;', '=': '&#x3D;' })[s];
    });
  }

  // Logout: limpiar sesión y recargar para restaurar panel de inicio
  btnLogout.addEventListener('click', () => {
    setToken(null); setUser(null);
    window.location.reload();
  });

  // Editar usuario: abrir modal con datos
  if (btnEditUser) {
    btnEditUser.addEventListener('click', () => {
      const u = getUser(); if (!u) return;
      editNombre.value = u.nombre || ''; editEmail.value = u.email || ''; editPassword.value = '';
      editModal.style.display = 'block';
    });
  }

  // Cancelar edición
  if (btnCancelarEd) btnCancelarEd.addEventListener('click', () => { editModal.style.display = 'none'; });

  // Guardar edición
  if (btnGuardarEd) {
    btnGuardarEd.addEventListener('click', async () => {
      editarMensaje.textContent = '';
      const u = getUser(); if (!u) return;
      const nombre = (editNombre.value || '').trim();
      const email = (editEmail.value || '').trim() || null;
      const password = (editPassword.value || '').trim() || null;
      try {
        const token = getToken();
        const res = await fetch('/api/usuario/' + u.id, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
          body: JSON.stringify({ nombre, email, password })
        });
        const txt = await res.text();
        let data = null; try { data = JSON.parse(txt); } catch (e) { data = null; }
        if (!res.ok) {
          editarMensaje.textContent = (data && data.error) ? data.error : 'Error al actualizar';
          return;
        }
        const updated = data.user || { id: u.id, nombre: nombre || u.nombre, email: email || u.email, rol: u.rol };
        setUser(updated);
        showActiveUser(updated);
        editModal.style.display = 'none';
      } catch (e) {
        editarMensaje.textContent = 'Error de red';
        console.error('Guardar edición error', e);
      }
    });
  }

  // Eliminar usuario (propio)
  if (btnDeleteUser) {
    btnDeleteUser.addEventListener('click', async () => {
      const u = getUser(); if (!u) return;
      if (!confirm('¿Eliminar tu cuenta? Esta acción no se puede deshacer.')) return;
      try {
        const token = getToken();
        const res = await fetch('/api/usuario/' + u.id, {
          method: 'DELETE',
          headers: { 'Authorization': 'Bearer ' + token }
        });
        const txt = await res.text();
        let data = null; try { data = JSON.parse(txt); } catch (e) { data = null; }
        if (!res.ok) {
          alert((data && data.error) ? data.error : 'Error al eliminar');
          return;
        }
        alert('Cuenta eliminada.');
        setToken(null); setUser(null);
        window.location.reload();
      } catch (e) {
        alert('Error de red');
        console.error('Eliminar usuario error', e);
      }
    });
  }

  // Restaurar sesión si hay token y usuario en localStorage
  const existingUser = getUser();
  const existingToken = getToken();
  if (existingUser && existingToken) {
    showActiveUser(existingUser);
    appMain.style.display = 'block';
    // Eliminar panel de inicio si existe
    if (adminPanel && adminPanel.parentNode) adminPanel.parentNode.removeChild(adminPanel);
    // Notificar a la app para que cargue datos
    window.dispatchEvent(new CustomEvent('user-logged-in', { detail: existingUser }));
  }
});