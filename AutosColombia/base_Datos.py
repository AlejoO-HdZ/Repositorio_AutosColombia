# MODULO DE CONEXION CON MYSQL-base_datos.py
import mysql.connector
from mysql.connector import Error
from datetime import datetime

def get_connection():
    try:
        return mysql.connector.connect(
        host="local", # Entorno Local.
        user="Us000", # Usuario base datos por seguridad se pone una generico.
        password="Password Gene998989879", # Contraseña del usuario base datos por seguridad se pone una generica.
        database="parqueadero12232" # Nombre de database random
    )
    except Error as e:
        print("Error de conexión:", e)
        return None

def buscar_vehiculo(placa):
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Vehiculo WHERE placa = %s", (placa,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def crear_vehiculo(placa, tipo, color, marca):
    conn = get_connection()
    if not conn:
        return False, "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Vehiculo (placa, tipo, color, marca) VALUES (%s,%s,%s,%s)",
            (placa, tipo, color, marca)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True, None
    except Error as e:
        return False, str(e)

# Registrar entrada con novedad opcional
def registrar_entrada(placa, descripcion_novedad=None, tipo_id=None):
    conn = get_connection()
    if not conn:
        return False, "Error de conexión"
    try:
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO Registro (placa, hora_entrada, estado) VALUES (%s, %s, 'activo')",
            (placa, now)
        )
        registro_id = cursor.lastrowid
        # Si hay novedad, insertarla
        if descripcion_novedad and tipo_id:
            cursor.execute(
                "INSERT INTO Novedad (registro_id, descripcion, fecha, tipo_id) VALUES (%s, %s, %s, %s)",
                (registro_id, descripcion_novedad, now, tipo_id)
            )
        conn.commit()
        cursor.close()
        conn.close()
        return True, None
    except Error as e:
        return False, str(e)

def registrar_salida(registro_id, descripcion_novedad=None, tipo_id=None):
    conn = get_connection()
    if not conn:
        return False, "Error de conexión"
    try:
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "UPDATE Registro SET hora_salida = %s, estado = 'cerrado' WHERE id = %s",
            (now, registro_id)
        )
        if descripcion_novedad and tipo_id:
            cursor.execute(
                "INSERT INTO Novedad (registro_id, descripcion, fecha, tipo_id) VALUES (%s, %s, %s, %s)",
                (registro_id, descripcion_novedad, now, tipo_id)
            )
        conn.commit()
        cursor.close()
        conn.close()
        return True, None
    except Error as e:
        return False, str(e)

def obtener_registro_activo_por_placa(placa):
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT r.* FROM Registro r WHERE r.placa = %s AND r.estado = 'activo' ORDER BY r.hora_entrada DESC LIMIT 1",
        (placa,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def obtener_historial(limit=200):
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT r.id, r.placa, v.tipo, v.marca, r.hora_entrada, r.hora_salida, r.estado "
        "FROM Registro r LEFT JOIN Vehiculo v ON r.placa = v.placa "
        "ORDER BY r.hora_entrada DESC LIMIT %s",
        (limit,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def obtener_novedades_por_registro(registro_id):
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT n.id, n.descripcion, n.fecha, t.nombre as tipo_nombre "
        "FROM Novedad n LEFT JOIN TipoNovedad t ON n.tipo_id = t.id "
        "WHERE n.registro_id = %s ORDER BY n.fecha DESC",
        (registro_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def obtener_tipos_novedad():
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre FROM TipoNovedad ORDER BY nombre")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# Nuevo: obtener lista de registros activos (placa, tipo, hora_entrada)
def obtener_activos():
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT r.id, r.placa, v.tipo, r.hora_entrada "
        "FROM Registro r LEFT JOIN Vehiculo v ON r.placa = v.placa "
        "WHERE r.estado = 'activo' ORDER BY r.hora_entrada ASC"
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows