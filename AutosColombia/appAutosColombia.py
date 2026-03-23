# CAPA DE LOGICA
# CONTROLADOR PRINCIPAL (FLASK-CONEXION)
from flask import Flask, render_template, request, jsonify
import uuid
import base_Datos
import usuarios
import celdas

app = Flask(__name__, static_folder='static', template_folder='templates')

# Inicializar la base de datos
db=base_Datos
db.init_db()

# Tokens simples en memoria: token -> user dict
tokens = {}

def set_token_func(user):
    """Generar y almacenar token en memoria para la sesión."""
    token = str(uuid.uuid4())
    tokens[token] = user
    return token

def require_token_func(req):
    """Extraer token del header Authorization: Bearer <token> y devolver user dict o None."""
    auth = req.headers.get('Authorization', '')
    if not auth or not auth.startswith('Bearer '):
        return None
    token = auth.split(' ', 1)[1].strip()
    return tokens.get(token)

# Asignar helpers a módulos de usuarios y celdas
usuarios.require_token = require_token_func
usuarios.set_token = set_token_func
celdas.require_token = require_token_func

@app.route('/')
def index():
    return render_template('index.html')

# ---------------- Usuarios ----------------
# Registrar usuario
app.add_url_rule('/api/usuario', 'crear_usuario', usuarios.crear_usuario_route, methods=['POST'])
# Login
app.add_url_rule('/api/login', 'login', usuarios.login_route, methods=['POST'])
# Editar usuario (solo propio)
app.add_url_rule('/api/usuario/<int:user_id>', 'actualizar_usuario', usuarios.actualizar_usuario_route, methods=['PUT'])
# Eliminar usuario (solo propio)
app.add_url_rule('/api/usuario/<int:user_id>', 'eliminar_usuario', usuarios.eliminar_usuario_route, methods=['DELETE'])
# Optional: endpoint para saber si existen usuarios (útil para primer registro)
app.add_url_rule('/api/usuarios/existen', 'usuarios_exists', usuarios.usuarios_exists_route, methods=['GET'])

# ---------------- Vehículos / Registros ----------------
@app.route('/api/vehiculo/<placa>', methods=['GET'])
def api_buscar_vehiculo(placa):
    try:
        placa = placa.strip().upper()
        veh = db.buscar_vehiculo(placa)
        registro_activo = db.obtener_registro_activo_por_placa(placa)
        return jsonify({'vehiculo': veh, 'registro_activo': registro_activo, 'tipos_novedad': []})
    except Exception as e:
        print("api_buscar_vehiculo error:", e)
        return jsonify({'ok': False, 'error': 'Error interno al buscar vehículo'}), 500

@app.route('/api/vehiculo', methods=['POST'])
def api_crear_vehiculo():
    try:
        data = request.json or {}
        placa = (data.get('placa') or '').strip().upper()
        tipo = data.get('tipo')
        color = data.get('color')
        marca = data.get('marca')
        if not placa or not tipo:
            return jsonify({'ok': False, 'error': 'placa y tipo obligatorios'}), 400
        ok, err = db.crear_vehiculo(placa, tipo, color, marca)
        if not ok:
            if err == "duplicado":
                return jsonify({'ok': False, 'error': 'vehiculo_existente'}), 409
            return jsonify({'ok': False, 'error': err}), 500
        return jsonify({'ok': True})
    except Exception as e:
        print("api_crear_vehiculo error:", e)
        return jsonify({'ok': False, 'error': 'Error interno al crear vehículo'}), 500

@app.route('/api/registro/entrada', methods=['POST'])
def api_registrar_entrada():
    try:
        data = request.json or {}
        placa = (data.get('placa') or '').strip().upper()
        descripcion = data.get('descripcion')
        tipo_id = data.get('tipo_id')
        celda_id = data.get('celda_id')
        if not placa:
            return jsonify({'ok': False, 'error': 'placa requerida'}), 400
        # Normalizar valores vacíos
        if tipo_id == '':
            tipo_id = None
        if celda_id == '':
            celda_id = None
        ok, err = db.registrar_entrada(placa, descripcion, tipo_id, celda_id)
        if not ok:
            return jsonify({'ok': False, 'error': err}), 500
        return jsonify({'ok': True})
    except Exception as e:
        print("api_registrar_entrada error:", e)
        return jsonify({'ok': False, 'error': 'Error interno al registrar entrada'}), 500

@app.route('/api/registro/salida', methods=['POST'])
def api_registrar_salida():
    try:
        data = request.json or {}
        registro_id = data.get('registro_id')
        descripcion = data.get('descripcion')
        tipo_id = data.get('tipo_id')
        if not registro_id:
            return jsonify({'ok': False, 'error': 'registro_id requerido'}), 400
        ok, err = db.registrar_salida(registro_id, descripcion, tipo_id)
        if not ok:
            return jsonify({'ok': False, 'error': err}), 500
        return jsonify({'ok': True})
    except Exception as e:
        print("api_registrar_salida error:", e)
        return jsonify({'ok': False, 'error': 'Error interno al registrar salida'}), 500

@app.route('/api/historial', methods=['GET'])
def api_historial():
    try:
        rows = db.obtener_historial(limit=500)
        return jsonify({'historial': rows})
    except Exception as e:
        print("api_historial error:", e)
        return jsonify({'historial': []}), 200

@app.route('/api/activos', methods=['GET'])
def api_activos():
    try:
        rows = db.obtener_activos()
        return jsonify({'activos': rows})
    except Exception as e:
        print("api_activos error:", e)
        return jsonify({'activos': []}), 200

# ---------------- Celdas ----------------
app.add_url_rule('/api/celdas', 'listar_celdas', celdas.listar_celdas_route, methods=['GET'])
app.add_url_rule('/api/celda', 'crear_celda', celdas.crear_celda_route, methods=['POST'])
app.add_url_rule('/api/celda/<int:celda_id>/estado', 'actualizar_estado_celda', celdas.actualizar_estado_celda_route, methods=['PUT'])

# ---------------- Debug / util ----------------
@app.route('/api/debug/tokens', methods=['GET'])
def api_debug_tokens():
    try:
        return jsonify({'tokens_count': len(tokens)})
    except Exception as e:
        print("api_debug_tokens error:", e)
        return jsonify({'ok': False, 'error': 'Error interno'}), 500

if __name__ == '__main__':
    app.run(debug=True)