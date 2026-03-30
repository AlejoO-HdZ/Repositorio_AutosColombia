# CAPA DE LOGICA
# CONTROLADOR PRINCIPAL (FLASK - CONEXION)
from flask import Flask, request, jsonify, send_from_directory, render_template
import usuarios as usuarios_mod
import celdas as celdas_mod
import pago as pago_mod
import base_Datos as db

app = Flask(__name__, static_folder='static', template_folder='templates')

# --- Rutas estáticas y root ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# --- Usuarios: endpoints mínimos (usar usuarios.py) ---
# Exponer endpoints que usuarios.py espera registrar manualmente
@app.route('/api/usuarios/exists', methods=['GET'])
def usuarios_exists():
    return usuarios_mod.usuarios_exists_route()

@app.route('/api/usuario', methods=['POST'])
def crear_usuario():
    return usuarios_mod.crear_usuario_route()

@app.route('/api/login', methods=['POST'])
def login():
    return usuarios_mod.login_route()

@app.route('/api/usuario/<int:user_id>', methods=['PUT'])
def actualizar_usuario(user_id):
    return usuarios_mod.actualizar_usuario_route(user_id)

@app.route('/api/usuario/<int:user_id>', methods=['DELETE'])
def eliminar_usuario(user_id):
    return usuarios_mod.eliminar_usuario_route(user_id)

# --- Celdas: endpoints ---
@app.route('/api/celdas', methods=['GET'])
def listar_celdas():
    return celdas_mod.listar_celdas_route()

@app.route('/api/celda', methods=['POST'])
def crear_celda():
    return celdas_mod.crear_celda_route()

@app.route('/api/celda/<int:celda_id>/estado', methods=['PUT'])
def actualizar_estado_celda(celda_id):
    return celdas_mod.actualizar_estado_celda_route(celda_id)

# --- Tarifas ---
@app.route('/api/tarifas', methods=['GET'])
def listar_tarifas():
    try:
        tarifas = db.listar_tarifas()
        return jsonify({'ok': True, 'tarifas': tarifas})
    except Exception as e:
        print("listar_tarifas error:", e)
        return jsonify({'ok': False, 'tarifas': []}), 500

@app.route('/api/tarifa', methods=['POST'])
def crear_tarifa():
    try:
        data = request.json or {}
        nombre = (data.get('nombre') or '').strip()
        tipo = (data.get('tipo') or 'por_hora').strip()
        valor = data.get('valor') or 0
        unidad = (data.get('unidad') or 'hora').strip()
        activo = 1 if data.get('activo', 1) else 0
        if not nombre:
            return jsonify({'ok': False, 'error': 'nombre requerido'}), 400
        ok, err = db.crear_tarifa(nombre, tipo, float(valor), unidad, activo)
        if not ok:
            return jsonify({'ok': False, 'error': err}), 500
        return jsonify({'ok': True})
    except Exception as e:
        print("crear_tarifa error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500

@app.route('/api/tarifa/<int:tarifa_id>', methods=['PUT'])
def actualizar_tarifa(tarifa_id):
    try:
        data = request.json or {}
        nombre = data.get('nombre')
        tipo = data.get('tipo')
        valor = data.get('valor')
        unidad = data.get('unidad')
        activo = data.get('activo')
        ok, err = db.actualizar_tarifa(tarifa_id, nombre=nombre, tipo=tipo, valor=valor, unidad=unidad, activo=activo)
        if not ok:
            return jsonify({'ok': False, 'error': err}), 500
        return jsonify({'ok': True})
    except Exception as e:
        print("actualizar_tarifa error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500

# --- Vehículos / Registro / Novedades ---
@app.route('/api/vehiculo/<placa>', methods=['GET'])
def api_buscar_vehiculo(placa):
    try:
        veh = db.buscar_vehiculo(placa)
        registro_activo = db.obtener_registro_activo_por_placa(placa)
        return jsonify({'ok': True, 'vehiculo': veh, 'registro_activo': registro_activo})
    except Exception as e:
        print("api_buscar_vehiculo error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500

@app.route('/api/vehiculo', methods=['POST'])
def api_crear_vehiculo():
    try:
        data = request.json or {}
        placa = (data.get('placa') or '').strip().upper()
        tipo = (data.get('tipo') or '').strip()
        color = data.get('color') or None
        marca = data.get('marca') or None
        if not placa or not tipo:
            return jsonify({'ok': False, 'error': 'placa y tipo requeridos'}), 400
        ok, err = db.crear_vehiculo(placa, tipo, color, marca)
        if not ok:
            return jsonify({'ok': False, 'error': err}), 409 if 'duplicado' in str(err).lower() else 500
        return jsonify({'ok': True})
    except Exception as e:
        print("api_crear_vehiculo error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500

@app.route('/api/registro/entrada', methods=['POST'])
def api_registrar_entrada():
    try:
        data = request.json or {}
        placa = (data.get('placa') or '').strip().upper()
        descripcion = data.get('descripcion')
        tipo_id = data.get('tipo_id')
        celda_id = data.get('celda_id')
        tarifa_id = data.get('tarifa_id')
        if not placa:
            return jsonify({'ok': False, 'error': 'placa requerida'}), 400
        ok, err = db.registrar_entrada(placa, descripcion=descripcion, tipo_id=tipo_id, celda_id=celda_id, tarifa_id=tarifa_id)
        if not ok:
            return jsonify({'ok': False, 'error': err}), 500
        return jsonify({'ok': True})
    except Exception as e:
        print("api_registrar_entrada error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500

@app.route('/api/registro/salida', methods=['POST'])
def api_registrar_salida():
    try:
        data = request.json or {}
        registro_id = data.get('registro_id')
        descripcion = data.get('descripcion')
        tipo_id = data.get('tipo_id')
        if not registro_id:
            return jsonify({'ok': False, 'error': 'registro_id requerido'}), 400
        ok, err = db.registrar_salida(int(registro_id), descripcion=descripcion, tipo_id=tipo_id)
        if not ok:
            return jsonify({'ok': False, 'error': err}), 500
        return jsonify({'ok': True})
    except Exception as e:
        print("api_registrar_salida error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500

# --- Activos e Historial (incluye novedades y tarifa aplicada) ---
@app.route('/api/activos', methods=['GET'])
def api_activos():
    try:
        activos = db.obtener_activos()
        return jsonify({'ok': True, 'activos': activos})
    except Exception as e:
        print("api_activos error:", e)
        return jsonify({'ok': False, 'activos': []}), 500

@app.route('/api/historial', methods=['GET'])
def api_historial():
    try:
        limit_q = request.args.get('limit')
        try:
            limit = int(limit_q) if limit_q and int(limit_q) > 0 else 200
        except Exception:
            limit = 200
        historial = db.obtener_historial(limit=limit)
        return jsonify({'ok': True, 'historial': historial})
    except Exception as e:
        print("api_historial error:", e)
        return jsonify({'ok': False, 'historial': []}), 500

# --- Pagos: usar pago.py register_routes helper to add routes ---
pago_mod.register_routes(app)

# --- Pagos directos (fallback) ---
@app.route('/api/pagos', methods=['GET'])
def api_pagos():
    return pago_mod.pagos_list_route()

# --- Inicialización de DB si se ejecuta directamente (opcional) ---
if __name__ == '__main__':
    # No activar debug en producción; aquí se deja para desarrollo local.
    db.init_db()
    app.run(host='127.0.0.1', port=5000, debug=False)