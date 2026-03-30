# CAPA LOGICA DEL SISTEMA
# MODULO DE PAGO Y TARIFAS PARA GESTION DE PAGOS, pago.py
from flask import request, jsonify
import base_Datos as db
from typing import Optional

def calcular_monto_route(registro_id):
    """
    GET /api/registro/<registro_id>/calcular_monto
    Devuelve el monto calculado para el registro según la tarifa activa o tarifa_id opcional.
    Query params: tarifa_id (opcional)
    """
    try:
        tarifa_id = request.args.get('tarifa_id')
        tarifa_id_val = int(tarifa_id) if tarifa_id and tarifa_id.isdigit() else None
        monto = db.calcular_monto_por_registro(int(registro_id), tarifa_id=tarifa_id_val)
        if monto is None:
            return jsonify({'ok': False, 'error': 'Registro no encontrado o error calculando monto'}), 404
        return jsonify({'ok': True, 'monto_calculado': monto})
    except Exception as e:
        print("calcular_monto_route error:", e)
        return jsonify({'ok': False, 'error': 'Error interno calculando monto'}), 500

def crear_pago_route():
    """
    POST /api/pago
    Body JSON: { registro_id, monto, metodo (opcional), detalle (opcional) }
    Crea un pago y marca el registro como pagado (flag pagado=1).
    """
    try:
        data = request.json or {}
        registro_id = data.get('registro_id')
        monto = data.get('monto')
        metodo = data.get('metodo') or 'efectivo'
        detalle = data.get('detalle') or None

        if registro_id is None or monto is None:
            return jsonify({'ok': False, 'error': 'registro_id y monto requeridos'}), 400

        try:
            registro_id_int = int(registro_id)
        except Exception:
            return jsonify({'ok': False, 'error': 'registro_id inválido'}), 400

        # Verificar que el registro existe y está activo o cerrado (permitir cobro en cierre)
        registro = None
        try:
            hist = db.obtener_historial(limit=2000)
            for r in hist:
                if int(r.get('id')) == registro_id_int:
                    registro = r
                    break
        except Exception:
            registro = None

        if not registro:
            return jsonify({'ok': False, 'error': 'registro_no_encontrado'}), 404

        # Validar monto numérico
        try:
            monto_val = float(monto)
            if monto_val < 0:
                return jsonify({'ok': False, 'error': 'monto inválido'}), 400
        except Exception:
            return jsonify({'ok': False, 'error': 'monto inválido'}), 400

        ok, res = db.crear_pago(registro_id_int, monto_val, metodo=metodo, usuario_id=None, detalle=detalle)
        if not ok:
            return jsonify({'ok': False, 'error': res}), 500

        return jsonify({'ok': True, 'pago_id': res})
    except Exception as e:
        print("crear_pago_route error:", e)
        return jsonify({'ok': False, 'error': 'Error interno creando pago'}), 500

def pagos_por_registro_route(registro_id):
    """
    GET /api/pago/registro/<registro_id>
    Devuelve la lista de pagos asociados a un registro.
    """
    try:
        pagos = db.obtener_pagos_por_registro(int(registro_id))
        return jsonify({'ok': True, 'pagos': pagos})
    except Exception as e:
        print("pagos_por_registro_route error:", e)
        return jsonify({'ok': False, 'pagos': []}), 200

def pagos_list_route():
    """
    GET /api/pagos
    Devuelve lista de pagos y total recaudado (limit opcional via query ?limit=).
    """
    try:
        limit_q = request.args.get('limit')
        try:
            limit = int(limit_q) if limit_q and int(limit_q) > 0 else 500
        except Exception:
            limit = 500
        pagos = db.obtener_pagos(limit=limit)
        total = sum([float(p.get('monto') or 0) for p in pagos])
        return jsonify({'ok': True, 'pagos': pagos, 'total_recaudado': total})
    except Exception as e:
        print("pagos_list_route error:", e)
        return jsonify({'ok': True, 'pagos': [], 'total_recaudado': 0}), 200

# Helper para registrar rutas desde app.py
def register_routes(app):
    """
    Llamar desde app.py: pago.register_routes(app)
    """
    app.add_url_rule('/api/registro/<int:registro_id>/calcular_monto', 'calcular_monto', calcular_monto_route, methods=['GET'])
    app.add_url_rule('/api/pago', 'crear_pago', crear_pago_route, methods=['POST'])
    app.add_url_rule('/api/pago/registro/<int:registro_id>', 'pagos_por_registro', pagos_por_registro_route, methods=['GET'])
    app.add_url_rule('/api/pagos', 'pagos_list', pagos_list_route, methods=['GET'])