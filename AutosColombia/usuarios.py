# MODULO GESTION USUARIOS - usuarios.py
from flask import request, jsonify
import base_Datos

# Funciones son asignadas por app.py
require_token = None
set_token = None

def usuarios_exists_route():
    """Endpoint opcional para saber si ya existen usuarios (útil para primer registro)."""
    try:
        conn = base_Datos.get_connection()
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
    Devuelve { ok: True, user_id } o { ok: False, error }.
    """
    try:
        data = request.json or {}
        nombre = (data.get('nombre') or '').strip()
        email = (data.get('email') or '').strip() or None
        password = (data.get('password') or '').strip()
        rol = (data.get('rol') or 'operador').strip() or 'operador'

        if not nombre or not password:
            return jsonify({'ok': False, 'error': 'nombre y password obligatorios'}), 400

        ok, res = base_Datos.crear_usuario(nombre, email, password, rol)
        if not ok:
            return jsonify({'ok': False, 'error': res}), 500

        return jsonify({'ok': True, 'user_id': res})
    except Exception as e:
        print("crear_usuario_route error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500

def login_route():
    """
    Login: espera JSON { nombre (o email), password }.
    Devuelve { ok: True, token, user } o { ok: False, error }.
    """
    try:
        data = request.json or {}
        identifier = (data.get('nombre') or data.get('email') or '').strip()
        password = (data.get('password') or '').strip()
        if not identifier or not password:
            return jsonify({'ok': False, 'error': 'nombre (o email) y password requeridos'}), 400

        user = base_Datos.autenticar_usuario(identifier, password)
        if not user:
            return jsonify({'ok': False, 'error': 'Credenciales inválidas'}), 401

        # Generar token si la app lo ha asignado
        if set_token:
            token = set_token(user)
            return jsonify({'ok': True, 'token': token, 'user': user})
        return jsonify({'ok': True, 'user': user})
    except Exception as e:
        print("login_route error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500

def actualizar_usuario_route(user_id):
    """
    Actualiza datos del usuario. Solo el propio usuario puede editar su cuenta.
    Espera JSON con campos opcionales: nombre, email, password, activo, rol.
    """
    try:
        if not require_token:
            return jsonify({'ok': False, 'error': 'No autorizado'}), 403
        current = require_token(request)
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

        ok, err = base_Datos.actualizar_usuario(user_id,
                                                nombre=nombre,
                                                email=email,
                                                password=password,
                                                activo=activo,
                                                rol=rol)
        if not ok:
            return jsonify({'ok': False, 'error': err}), 500

        user = base_Datos.obtener_usuario_por_id(user_id)
        return jsonify({'ok': True, 'user': user})
    except Exception as e:
        print("actualizar_usuario_route error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500

def eliminar_usuario_route(user_id):
    """
    Elimina la cuenta del usuario. Solo el propio usuario puede eliminar su cuenta.
    """
    try:
        if not require_token:
            return jsonify({'ok': False, 'error': 'No autorizado'}), 403
        current = require_token(request)
        if not current:
            return jsonify({'ok': False, 'error': 'No autorizado'}), 403
        if current.get('id') != user_id:
            return jsonify({'ok': False, 'error': 'No autorizado'}), 403

        ok, err = base_Datos.eliminar_usuario(user_id)
        if not ok:
            return jsonify({'ok': False, 'error': err}), 500
        return jsonify({'ok': True})
    except Exception as e:
        print("eliminar_usuario_route error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500
