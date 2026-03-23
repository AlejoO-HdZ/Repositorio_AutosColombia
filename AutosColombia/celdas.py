# MODULO GESTION CELDAS - celdas.py
from flask import request, jsonify
import base_Datos

require_token = None

def listar_celdas_route():
    """
    GET /api/celdas
    Devuelve lista de celdas con sus atributos: id, estado, descripcion.
    """
    try:
        rows = base_Datos.listar_celdas()
        return jsonify({'ok': True, 'celdas': rows})
    except Exception as e:
        print("listar_celdas_route error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500

def crear_celda_route():
    """
    POST /api/celda
    Body JSON: { descripcion, estado (opcional) }
    Nota: la tabla Celda ahora usa 'descripcion' en lugar de 'codigo' y 'tipo'.
    """
    try:
        # Restringir creación a usuarios autenticados, usar require_token aquí.
        data = request.json or {}
        descripcion = (data.get('descripcion') or '').strip()
        estado = (data.get('estado') or 'disponible').strip().lower()
        if not descripcion:
            return jsonify({'ok': False, 'error': 'descripcion requerida'}), 400
        if estado not in ('disponible','ocupada','reservada','bloqueada'):
            return jsonify({'ok': False, 'error': 'estado inválido'}), 400
        ok, err = base_Datos.crear_celda(descripcion, estado=estado)
        if not ok:
            if err == "duplicado":
                return jsonify({'ok': False, 'error': 'celda_duplicada'}), 409
            return jsonify({'ok': False, 'error': err}), 500
        return jsonify({'ok': True})
    except Exception as e:
        print("crear_celda_route error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500

def actualizar_estado_celda_route(celda_id):
    """
    PUT /api/celda/<celda_id>/estado
    Body JSON: { estado }
    Actualiza el estado de la celda (disponible, ocupada, reservada, bloqueada).
    """
    try:
        # Opcional: validar token/roles si se requiere
        data = request.json or {}
        estado = (data.get('estado') or '').strip().lower()
        if estado not in ('disponible','ocupada','reservada','bloqueada'):
            return jsonify({'ok': False, 'error': 'estado inválido'}), 400
        ok, err = base_Datos.actualizar_estado_celda(celda_id, estado)
        if not ok:
            return jsonify({'ok': False, 'error': err}), 500
        return jsonify({'ok': True})
    except Exception as e:
        print("actualizar_estado_celda_route error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500