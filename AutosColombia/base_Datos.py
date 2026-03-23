# MODULO DE CONEXION CON MYSQL-base_datos.py
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from typing import Optional, Tuple, List, Dict

# --- CONFIGURACION entorno MySQL ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'Us000', # Usuario base datos por seguridad se pone una generico.
    'password': 'Password Gene998989879', # Contraseña del usuario base datos por seguridad se pone una generica.
    'database': 'parqueadero12232', # Nombre de database random
    'charset': 'utf8mb4'
}
# ------------------------------------------------

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print("DB connection error:", e)
        return None

def init_db():
    """Crea las tablas necesarias si no existen y pobla 20 celdas de ejemplo si están vacías."""
    conn = get_connection()
    if not conn:
        print("No se pudo conectar para inicializar BD")
        return
    cur = conn.cursor()
    try:
        cur.execute("SET SESSION sql_mode=''")
        # Usuarios
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Usuario (
          id INT AUTO_INCREMENT PRIMARY KEY,
          nombre VARCHAR(100) NOT NULL,
          email VARCHAR(150) UNIQUE,
          rol VARCHAR(30) NOT NULL DEFAULT 'operador',
          password VARCHAR(255) NOT NULL,
          activo TINYINT(1) DEFAULT 1
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        # Vehiculo
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Vehiculo (
          placa VARCHAR(20) PRIMARY KEY,
          tipo VARCHAR(50) NOT NULL,
          color VARCHAR(50),
          marca VARCHAR(50)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        # Celda (nueva estructura: id, estado, descripcion)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Celda (
          id INT AUTO_INCREMENT PRIMARY KEY,
          estado ENUM('disponible','ocupada','reservada','bloqueada') NOT NULL DEFAULT 'disponible',
          descripcion VARCHAR(255) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        # Registro
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Registro (
          id INT AUTO_INCREMENT PRIMARY KEY,
          placa VARCHAR(20) NOT NULL,
          hora_entrada DATETIME NOT NULL,
          hora_salida DATETIME NULL,
          estado ENUM('activo','cerrado') DEFAULT 'activo',
          celda_id INT NULL,
          FOREIGN KEY (placa) REFERENCES Vehiculo(placa) ON DELETE RESTRICT ON UPDATE CASCADE,
          FOREIGN KEY (celda_id) REFERENCES Celda(id) ON DELETE SET NULL ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        # TipoNovedad y Novedad
        cur.execute("""
        CREATE TABLE IF NOT EXISTS TipoNovedad (
          id INT AUTO_INCREMENT PRIMARY KEY,
          nombre VARCHAR(80) UNIQUE NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Novedad (
          id INT AUTO_INCREMENT PRIMARY KEY,
          registro_id INT NOT NULL,
          descripcion VARCHAR(255),
          fecha DATETIME NOT NULL,
          tipo_id INT NOT NULL,
          FOREIGN KEY (registro_id) REFERENCES Registro(id) ON DELETE CASCADE ON UPDATE CASCADE,
          FOREIGN KEY (tipo_id) REFERENCES TipoNovedad(id) ON DELETE RESTRICT ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        # Insertar tipos de novedad si no existen
        cur.execute("SELECT COUNT(*) FROM TipoNovedad")
        if cur.fetchone()[0] == 0:
            cur.executemany("INSERT IGNORE INTO TipoNovedad (nombre) VALUES (%s)",
                            [('Daño menor',), ('Daño mayor',), ('Observación',), ('Otro',)])
        # Poblar 20 celdas de ejemplo si la tabla está vacía
        cur.execute("SELECT COUNT(*) FROM Celda")
        if cur.fetchone()[0] == 0:
            cur.executemany("INSERT INTO Celda (estado, descripcion) VALUES (%s,%s)", [
                ('disponible', 'A1 - Automovil - Nivel 1'),
                ('ocupada',    'A2 - Automovil - Nivel 1'),
                ('reservada',  'R1 - Reservada - Movilidad reducida'),
                ('bloqueada',  'Mantenimiento - Bloqueada - Nivel 2'),
                ('disponible', 'M1 - Motocicleta - Zona M'),
                ('ocupada',    'M2 - Motocicleta - Zona M'),
                ('disponible', 'B1 - Bicicleta - Rack Norte'),
                ('ocupada',    'B2 - Bicicleta - Rack Sur'),
                ('reservada',  'R2 - Reservada - Propietario VIP'),
                ('disponible', 'A3 - Automovil - Nivel 2'),
                ('ocupada',    'A4 - Automovil - Nivel 2'),
                ('disponible', 'M3 - Motocicleta - Zona Exterior'),
                ('bloqueada',  'Señalización - Bloqueada - Zona C'),
                ('disponible', 'B3 - Bicicleta - Rack Este'),
                ('ocupada',    'B4 - Bicicleta - Rack Oeste'),
                ('disponible', 'A5 - Automovil - Nivel 3'),
                ('reservada',  'R3 - Reservada - Personal'),
                ('disponible', 'M4 - Motocicleta - Zona Techada'),
                ('disponible', 'Otro1 - Multiuso - Nivel 1'),
                ('ocupada',    'Otro2 - Multiuso - Nivel 2'),
            ])
        conn.commit()
    except Exception as e:
        print("init_db error:", e)
    finally:
        try: cur.close(); conn.close()
        except: pass

# ---------------- Usuarios ----------------
def crear_usuario(nombre: str, email: Optional[str], password: str, rol: str = 'operador') -> Tuple[bool, str]:
    conn = get_connection()
    if not conn:
        return False, "Error de conexión a BD"
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO Usuario (nombre,email,password,rol) VALUES (%s,%s,%s,%s)",
                    (nombre, email, password, rol))
        conn.commit()
        uid = cur.lastrowid
        cur.close(); conn.close()
        return True, uid
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        msg = str(e)
        if "Duplicate" in msg or "Duplicate entry" in msg:
            return False, "Usuario o email ya existe"
        return False, msg

def autenticar_usuario(identifier: str, password: str) -> Optional[Dict]:
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,nombre,email,rol,password,activo FROM Usuario WHERE nombre=%s OR email=%s LIMIT 1",
                    (identifier, identifier))
        row = cur.fetchone()
        cur.close(); conn.close()
        if not row:
            return None
        if row.get('activo', 1) != 1:
            return None
        if row.get('password') == password:
            row.pop('password', None)
            return row
        return None
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        print("auth error:", e)
        return None

def obtener_usuario_por_id(user_id: int) -> Optional[Dict]:
    conn = get_connection()
    if not conn: return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,nombre,email,rol,activo FROM Usuario WHERE id=%s", (user_id,))
        row = cur.fetchone()
        cur.close(); conn.close()
        return dict(row) if row else None
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        print("obtener_usuario_por_id error:", e)
        return None

def actualizar_usuario(user_id: int, nombre: Optional[str]=None, email: Optional[str]=None,
                       password: Optional[str]=None, activo: Optional[bool]=None, rol: Optional[str]=None) -> Tuple[bool, Optional[str]]:
    conn = get_connection()
    if not conn:
        return False, "Error de conexión a BD"
    try:
        cur = conn.cursor()
        updates = []
        params = []
        if nombre is not None:
            updates.append("nombre=%s"); params.append(nombre)
        if email is not None:
            updates.append("email=%s"); params.append(email)
        if password is not None:
            updates.append("password=%s"); params.append(password)
        if activo is not None:
            updates.append("activo=%s"); params.append(1 if activo else 0)
        if rol is not None:
            updates.append("rol=%s"); params.append(rol)
        if not updates:
            cur.close(); conn.close(); return True, None
        params.append(user_id)
        sql = "UPDATE Usuario SET " + ", ".join(updates) + " WHERE id=%s"
        cur.execute(sql, tuple(params))
        conn.commit()
        cur.close(); conn.close()
        return True, None
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        return False, str(e)

def eliminar_usuario(user_id: int) -> Tuple[bool, Optional[str]]:
    conn = get_connection()
    if not conn:
        return False, "Error de conexión a BD"
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM Usuario WHERE id=%s", (user_id,))
        conn.commit()
        cur.close(); conn.close()
        return True, None
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        return False, str(e)

# ---------------- Vehículos / Registro / Novedad ----------------
def buscar_vehiculo(placa: str) -> Optional[Dict]:
    conn = get_connection()
    if not conn: return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Vehiculo WHERE placa=%s", (placa,))
        row = cur.fetchone()
        cur.close(); conn.close()
        return dict(row) if row else None
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        print("buscar_vehiculo error:", e)
        return None

def crear_vehiculo(placa: str, tipo: str, color: Optional[str], marca: Optional[str]) -> Tuple[bool, Optional[str]]:
    conn = get_connection()
    if not conn:
        return False, "Error de conexión a BD"
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO Vehiculo (placa,tipo,color,marca) VALUES (%s,%s,%s,%s)",
                    (placa, tipo, color, marca))
        conn.commit()
        cur.close(); conn.close()
        return True, None
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        msg = str(e)
        if "1062" in msg or "Duplicate entry" in msg:
            return False, "duplicado"
        return False, msg

def obtener_registro_activo_por_placa(placa: str) -> Optional[Dict]:
    conn = get_connection()
    if not conn: return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT r.*, c.descripcion as celda_descripcion FROM Registro r LEFT JOIN Celda c ON r.celda_id=c.id WHERE r.placa=%s AND r.estado='activo' ORDER BY hora_entrada DESC LIMIT 1", (placa,))
        row = cur.fetchone()
        cur.close(); conn.close()
        return dict(row) if row else None
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        print("obtener_registro_activo error:", e)
        return None

def asignar_celda_para_tipo(tipo_vehiculo: Optional[str]=None) -> Optional[int]:
    """
    Prioriza celdas disponibles cuya descripcion contenga la palabra clave del tipo.
    Estrategia:
      1) Buscar celdas disponibles con descripcion LIKE '%<tipo>%' y que no sean 'Reservada'
      2) Si no hay, buscar disponibles con descripcion LIKE '%<tipo>%'
      3) Si no hay, buscar cualquier disponible que no sea 'Reservada'
      4) Si no hay, tomar cualquier disponible (incluyendo reservadas)
    """
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor(dictionary=True)
        key = (tipo_vehiculo or '').strip()
        # Normalizar palabras clave simples
        mapping = {
            'automovil': ['Automovil','Automóvil','A1','A2','A3','A4','A5'],
            'motocicleta': ['Motocicleta','M1','M2','M3','M4'],
            'bicicleta': ['Bicicleta','B1','B2','B3','B4'],
            'otro': ['Otro','Multiuso']
        }
        # Build LIKE patterns
        patterns = []
        if key:
            k = key.lower()
            if 'auto' in k or 'car' in k or 'autom' in k:
                patterns = mapping['automovil']
            elif 'moto' in k or 'motoc' in k:
                patterns = mapping['motocicleta']
            elif 'bici' in k or 'bicic' in k:
                patterns = mapping['bicicleta']
            else:
                patterns = mapping['otro']
        # 1) Prefer matching and not reserved
        if patterns:
            for p in patterns:
                cur.execute("SELECT id, descripcion FROM Celda WHERE estado='disponible' AND descripcion LIKE %s AND descripcion NOT LIKE %s ORDER BY id LIMIT 1", ('%'+p+'%', '%Reservada%'))
                row = cur.fetchone()
                if row:
                    cid = row['id']
                    cur.close(); conn.close()
                    return cid
            # 2) matching including reserved descriptions
            for p in patterns:
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT id, descripcion FROM Celda WHERE estado='disponible' AND descripcion LIKE %s ORDER BY id LIMIT 1", ('%'+p+'%',))
                row = cur.fetchone()
                if row:
                    cid = row['id']
                    cur.close(); conn.close()
                    return cid
        # 3) any available not reserved
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM Celda WHERE estado='disponible' AND descripcion NOT LIKE %s ORDER BY id LIMIT 1", ('%Reservada%',))
        row = cur.fetchone()
        if row:
            cid = row['id']
            cur.close(); conn.close()
            return cid
        # 4) any available including reserved
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM Celda WHERE estado='disponible' ORDER BY id LIMIT 1")
        row = cur.fetchone()
        cur.close(); conn.close()
        return row['id'] if row else None
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        print("asignar_celda error:", e)
        return None

def registrar_entrada(placa: str, descripcion: Optional[str]=None, tipo_id: Optional[int]=None, celda_id: Optional[int]=None) -> Tuple[bool, Optional[str]]:
    conn = get_connection()
    if not conn:
        return False, "Error de conexión a BD"
    try:
        cur = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Si no se pasó celda_id, intentar asignar automáticamente según tipo de vehiculo
        if not celda_id:
            cur.execute("SELECT tipo FROM Vehiculo WHERE placa=%s", (placa,))
            row = cur.fetchone()
            tipo_veh = row[0] if row else None
            cur.close()
            celda_id = asignar_celda_para_tipo(tipo_veh)
            cur = conn.cursor()
        if celda_id:
            cur.execute("INSERT INTO Registro (placa,hora_entrada,estado,celda_id) VALUES (%s,%s,'activo',%s)",
                        (placa, now, celda_id))
            # marcar celda como ocupada
            cur.execute("UPDATE Celda SET estado='ocupada' WHERE id=%s", (celda_id,))
        else:
            cur.execute("INSERT INTO Registro (placa,hora_entrada,estado) VALUES (%s,%s,'activo')", (placa, now))
        reg_id = cur.lastrowid
        if descripcion and tipo_id:
            cur.execute("INSERT INTO Novedad (registro_id,descripcion,fecha,tipo_id) VALUES (%s,%s,%s,%s)",
                        (reg_id, descripcion, now, tipo_id))
        conn.commit()
        cur.close(); conn.close()
        return True, None
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        return False, str(e)

def registrar_salida(registro_id: int, descripcion: Optional[str]=None, tipo_id: Optional[int]=None) -> Tuple[bool, Optional[str]]:
    conn = get_connection()
    if not conn:
        return False, "Error de conexión a BD"
    try:
        cur = conn.cursor(dictionary=True)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("SELECT celda_id FROM Registro WHERE id=%s", (registro_id,))
        row = cur.fetchone()
        celda_id = row['celda_id'] if row and 'celda_id' in row else None
        cur.execute("UPDATE Registro SET hora_salida=%s, estado='cerrado' WHERE id=%s", (now, registro_id))
        if descripcion and tipo_id:
            cur.execute("INSERT INTO Novedad (registro_id,descripcion,fecha,tipo_id) VALUES (%s,%s,%s,%s)",
                        (registro_id, descripcion, now, tipo_id))
        if celda_id:
            cur.execute("UPDATE Celda SET estado='disponible' WHERE id=%s", (celda_id,))
        conn.commit()
        cur.close(); conn.close()
        return True, None
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        return False, str(e)

def obtener_historial(limit: int = 200) -> List[Dict]:
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT r.id, r.placa, r.hora_entrada, r.hora_salida, r.estado, r.celda_id, c.descripcion as celda_descripcion, v.tipo, v.marca "
            "FROM Registro r LEFT JOIN Vehiculo v ON r.placa=v.placa LEFT JOIN Celda c ON r.celda_id=c.id "
            "ORDER BY r.hora_entrada DESC LIMIT %s", (limit,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        print("obtener_historial error:", e)
        return []

def obtener_activos() -> List[Dict]:
    """
    Devuelve registros activos incluyendo la descripcion de la celda y
    la última novedad (descripcion) asociada al registro si existe.
    """
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT
              r.id,
              r.placa,
              r.hora_entrada,
              r.celda_id,
              c.descripcion AS celda_descripcion,
              v.tipo,
              (SELECT n.descripcion
               FROM Novedad n
               WHERE n.registro_id = r.id
               ORDER BY n.fecha DESC, n.id DESC
               LIMIT 1) AS novedad
            FROM Registro r
            LEFT JOIN Vehiculo v ON r.placa = v.placa
            LEFT JOIN Celda c ON r.celda_id = c.id
            WHERE r.estado = 'activo'
            ORDER BY r.hora_entrada ASC
        """)
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        print("obtener_activos error:", e)
        return []

# ---------------- Celdas ----------------
def crear_celda(codigo_or_desc: str, tipo: Optional[str]=None, ubicacion: Optional[str]=None, estado: str='disponible') -> Tuple[bool, Optional[str]]:
    """
    Nota: la tabla Celda ahora solo tiene 'descripcion' en lugar de 'codigo' y 'tipo'.
    Se usa 'codigo_or_desc' como descripcion.
    """
    conn = get_connection()
    if not conn:
        return False, "Error de conexión a BD"
    try:
        cur = conn.cursor()
        descripcion = codigo_or_desc
        cur.execute("INSERT INTO Celda (descripcion,estado) VALUES (%s,%s)",
                    (descripcion, estado))
        conn.commit()
        cur.close(); conn.close()
        return True, None
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        msg = str(e)
        if "1062" in msg or "Duplicate entry" in msg:
            return False, "duplicado"
        return False, msg

def listar_celdas() -> List[Dict]:
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,estado,descripcion FROM Celda ORDER BY id")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        print("listar_celdas error:", e)
        return []

def actualizar_estado_celda(celda_id: int, estado: str) -> Tuple[bool, Optional[str]]:
    if estado not in ('disponible','ocupada','reservada','bloqueada'):
        return False, "estado inválido"
    conn = get_connection()
    if not conn:
        return False, "Error de conexión a BD"
    try:
        cur = conn.cursor()
        cur.execute("UPDATE Celda SET estado=%s WHERE id=%s", (estado, celda_id))
        conn.commit()
        cur.close(); conn.close()
        return True, None
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        return False, str(e)

# Inicializar DB al importar
if __name__ == '__main__':
    init_db()