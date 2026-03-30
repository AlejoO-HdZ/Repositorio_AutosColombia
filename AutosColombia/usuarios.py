# CAPA LOGICA DEL SISTEMA
# MODULO GESTION USUARIOS - usuarios.py
from flask import request, jsonify, make_response
import base_Datos as db_module

# Estas funciones son asignadas por app.py (opcional)
require_token = None
set_token = None

ALLOWED_ROLES = ('operador', 'empleado', 'admin')


def usuarios_exists_route():
    """Endpoint opcional para saber si ya existen usuarios (útil para primer registro)."""
    try:
        conn = db_module.get_connection()
        if not conn:
            return jsonify({'exists': False, 'count': 0})
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM Usuario")
        c = cur.fetchone()[0]
        cur.close(); conn.close()
        return jsonify({'exists': c > 0, 'count': c})
    except Exception as e:
        print("usuarios_exists error:", e)
        return jsonify({'exists': False, 'count': 0})


def crear_usuario_route():
    """
    Crea un usuario. Espera JSON: { nombre, email (opcional), password, rol (opcional) }.
    Roles permitidos: operador, empleado, admin.
    Devuelve { ok: True, user_id } o { ok: False, error }.
    """
    try:
        data = request.json or {}
        nombre = (data.get('nombre') or '').strip()
        email = (data.get('email') or '').strip() or None
        password = (data.get('password') or '').strip()
        rol = (data.get('rol') or 'operador').strip().lower() or 'operador'

        if not nombre or not password:
            return jsonify({'ok': False, 'error': 'nombre y password obligatorios'}), 400

        if rol not in ALLOWED_ROLES:
            return jsonify({'ok': False, 'error': f'rol inválido, opciones: {", ".join(ALLOWED_ROLES)}'}), 400

        ok, res = db_module.crear_usuario(nombre, email, password, rol)
        if not ok:
            return jsonify({'ok': False, 'error': res}), 409 if 'existe' in str(res).lower() else 500

        return jsonify({'ok': True, 'user_id': res})
    except Exception as e:
        print("crear_usuario_route error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500


def _get_current_user_from_request():
    """
    Intenta obtener el usuario actual de la request.
    - Si existe require_token (asignado por la app), usarlo.
    - Si no, fallback a cookie 'user_id' y obtener usuario desde BD.
    Devuelve dict usuario o None.
    """
    try:
        if require_token:
            try:
                current = require_token(request)
                return current
            except Exception:
                # si require_token falla, seguir con fallback
                pass

        # Fallback: cookie 'user_id'
        uid = request.cookies.get('user_id')
        if not uid:
            return None
        try:
            uid_int = int(uid)
        except Exception:
            return None
        user = db_module.obtener_usuario_por_id(uid_int)
        return user
    except Exception:
        return None


def login_route():
    """
    Login: espera JSON { nombre (o email), password }.
    Devuelve { ok: True, token, user } o { ok: False, error }.
    Además setea cookie 'user_id' para permitir operaciones locales de edición/eliminación.
    """
    try:
        data = request.json or {}
        identifier = (data.get('nombre') or data.get('email') or '').strip()
        password = (data.get('password') or '').strip()
        if not identifier or not password:
            return jsonify({'ok': False, 'error': 'nombre (o email) y password requeridos'}), 400

        user = db_module.autenticar_usuario(identifier, password)
        if not user:
            return jsonify({'ok': False, 'error': 'Credenciales inválidas'}), 401

        # Si la app externa asigna token, usarlo y además setear cookie user_id
        if set_token:
            try:
                token = set_token(user)
            except Exception:
                token = None
            resp = make_response(jsonify({'ok': True, 'token': token, 'user': user}) if token else jsonify({'ok': True, 'user': user}))
            # Setear cookie con user_id para fallback local (httponly para mayor seguridad)
            resp.set_cookie('user_id', str(user.get('id')), httponly=True, samesite='Lax')
            return resp

        # Fallback local: setear cookie con user_id para que el servidor pueda identificar al usuario
        resp = make_response(jsonify({'ok': True, 'user': user}))
        resp.set_cookie('user_id', str(user.get('id')), httponly=True, samesite='Lax')
        return resp
    except Exception as e:
        print("login_route error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500


def actualizar_usuario_route(user_id):
    """
    Actualiza datos del usuario. Solo el propio usuario puede editar su cuenta.
    Espera JSON con campos opcionales: nombre, email, password, activo, rol.
    """
    try:
        current = _get_current_user_from_request()
        if not current:
            return jsonify({'ok': False, 'error': 'No autorizado'}), 403
        # Solo permitir editar propia cuenta
        if current.get('id') != user_id:
            return jsonify({'ok': False, 'error': 'No autorizado'}), 403

        data = request.json or {}
        nombre = data.get('nombre')
        email = data.get('email')
        password = data.get('password')
        activo = data.get('activo')
        rol = data.get('rol')

        if rol is not None:
            rol = rol.strip().lower()
            if rol not in ALLOWED_ROLES:
                return jsonify({'ok': False, 'error': f'rol inválido, opciones: {", ".join(ALLOWED_ROLES)}'}), 400

        ok, err = db_module.actualizar_usuario(user_id,
                                               nombre=nombre,
                                               email=email,
                                               password=password,
                                               activo=activo,
                                               rol=rol)
        if not ok:
            return jsonify({'ok': False, 'error': err}), 500

        user = db_module.obtener_usuario_por_id(user_id)
        return jsonify({'ok': True, 'user': user})
    except Exception as e:
        print("actualizar_usuario_route error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500


def eliminar_usuario_route(user_id):
    """
    Elimina la cuenta del usuario. Solo el propio usuario puede eliminar su cuenta.
    """
    try:
        current = _get_current_user_from_request()
        if not current:
            return jsonify({'ok': False, 'error': 'No autorizado'}), 403
        if current.get('id') != user_id:
            return jsonify({'ok': False, 'error': 'No autorizado'}), 403

        ok, err = db_module.eliminar_usuario(user_id)
        if not ok:
            return jsonify({'ok': False, 'error': err}), 500
        # Al eliminar la cuenta, limpiar cookie en la respuesta (si es posible)
        resp = make_response(jsonify({'ok': True}))
        resp.set_cookie('user_id', '', expires=0)
        return resp
    except Exception as e:
        print("eliminar_usuario_route error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500