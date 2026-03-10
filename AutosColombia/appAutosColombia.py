# CAPA DE LOGICA
# CONTROLADOR PRINCIPAL (FLASK-CONEXION)

from flask import Flask, render_template, request, jsonify
from base_Datos import (
    buscar_vehiculo, crear_vehiculo, registrar_entrada,
    obtener_registro_activo_por_placa, registrar_salida,
    obtener_historial, obtener_novedades_por_registro,
    obtener_tipos_novedad, obtener_activos
)

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/vehiculo/<placa>', methods=['GET'])
def api_buscar_vehiculo(placa):
    placa = placa.upper()
    veh = buscar_vehiculo(placa)
    registro_activo = obtener_registro_activo_por_placa(placa)
    novedades = []
    if registro_activo:
        novedades = obtener_novedades_por_registro(registro_activo['id'])
    tipos_novedad = obtener_tipos_novedad()
    return jsonify({
        'vehiculo': veh,
        'registro_activo': registro_activo,
        'novedades': novedades,
        'tipos_novedad': tipos_novedad
    })

@app.route('/api/vehiculo', methods=['POST'])
def api_crear_vehiculo():
    data = request.json
    placa = data.get('placa','').upper()
    tipo = data.get('tipo')
    color = data.get('color')
    marca = data.get('marca')
    if not placa or not tipo:
        return jsonify({'ok': False, 'error': 'Placa y tipo son obligatorios'}), 400
    ok, err = crear_vehiculo(placa, tipo, color, marca)
    if not ok:
        return jsonify({'ok': False, 'error': err}), 500
    return jsonify({'ok': True})

# Registrar entrada con novedad opcional
@app.route('/api/registro/entrada', methods=['POST'])
def api_registrar_entrada():
    data = request.json
    placa = data.get('placa','').upper()
    descripcion = data.get('descripcion')
    tipo_id = data.get('tipo_id')
    if not placa:
        return jsonify({'ok': False, 'error': 'Placa requerida'}), 400
    activo = obtener_registro_activo_por_placa(placa)
    if activo:
        return jsonify({'ok': False, 'error': 'Ya existe un registro activo para esta placa', 'registro': activo}), 400
    ok, err = registrar_entrada(placa, descripcion, tipo_id)
    if not ok:
        return jsonify({'ok': False, 'error': err}), 500
    return jsonify({'ok': True})

@app.route('/api/registro/salida', methods=['POST'])
def api_registrar_salida():
    data = request.json
    registro_id = data.get('registro_id')
    descripcion = data.get('descripcion')
    tipo_id = data.get('tipo_id')
    if not registro_id:
        return jsonify({'ok': False, 'error': 'registro_id requerido'}), 400
    ok, err = registrar_salida(registro_id, descripcion, tipo_id)
    if not ok:
        return jsonify({'ok': False, 'error': err}), 500
    return jsonify({'ok': True})

@app.route('/api/historial', methods=['GET'])
def api_historial():
    rows = obtener_historial(limit=500)
    return jsonify({'historial': rows})

# Nuevo endpoint: lista de activos
@app.route('/api/activos', methods=['GET'])
def api_activos():
    rows = obtener_activos()
    return jsonify({'activos': rows})

if __name__ == '__main__':
    app.run(debug=True)