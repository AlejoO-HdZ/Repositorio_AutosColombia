# CAPA LOGICA DEL SISTEMA
# MODULO DE CONEXION CON MYSQL-base_datos.py
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from typing import Optional, Tuple, List, Dict

# --- CONFIGURACION entorno MySQL ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'ABC', # Usuario base datos por seguridad se pone una generica.
    'password': 'ABC', # Contraseña del usuario base datos por seguridad se pone una generica.
    'database': 'parqueadero5', # Nombre de database de MySQL Workbench
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
    """Crea las tablas necesarias si no existen y pobla datos iniciales.
       También añade columnas necesarias si faltan (migración simple)."""
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
        # Celda
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Celda (
          id INT AUTO_INCREMENT PRIMARY KEY,
          estado ENUM('disponible','ocupada','reservada','bloqueada') NOT NULL DEFAULT 'disponible',
          descripcion VARCHAR(255) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        # Registro (incluye columna tarifa_id)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Registro (
          id INT AUTO_INCREMENT PRIMARY KEY,
          placa VARCHAR(20) NOT NULL,
          hora_entrada DATETIME NOT NULL,
          hora_salida DATETIME NULL,
          estado ENUM('activo','cerrado') DEFAULT 'activo',
          celda_id INT NULL,
          pagado TINYINT(1) DEFAULT 0,
          tarifa_id INT NULL,
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
        # Tarifa
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Tarifa (
          id INT AUTO_INCREMENT PRIMARY KEY,
          nombre VARCHAR(80) NOT NULL,
          tipo ENUM('por_hora','fijo') NOT NULL DEFAULT 'por_hora',
          valor DECIMAL(10,2) NOT NULL DEFAULT 0.00,
          unidad VARCHAR(20) DEFAULT 'hora',
          activo TINYINT(1) DEFAULT 1
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        # Pago
        cur.execute("""
        CREATE TABLE IF NOT EXISTS Pago (
          id INT AUTO_INCREMENT PRIMARY KEY,
          registro_id INT NOT NULL,
          monto DECIMAL(10,2) NOT NULL,
          fecha DATETIME NOT NULL,
          metodo VARCHAR(50),
          detalle VARCHAR(255),
          usuario_id INT NULL,
          FOREIGN KEY (registro_id) REFERENCES Registro(id) ON DELETE CASCADE
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
        # Insertar tarifa por defecto si no existe
        cur.execute("SELECT COUNT(*) FROM Tarifa")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO Tarifa (nombre,tipo,valor,unidad,activo) VALUES (%s,%s,%s,%s,%s)",
                        ('Tarifa por hora', 'por_hora', 5000.00, 'hora', 1))
        conn.commit()

        # Migración simple: si la columna tarifa_id no existe en Registro, intentar añadirla (por compatibilidad)
        try:
            cur.execute("SHOW COLUMNS FROM Registro LIKE 'tarifa_id'")
            if not cur.fetchone():
                cur.execute("ALTER TABLE Registro ADD COLUMN tarifa_id INT NULL")
                conn.commit()
        except Exception:
            # Si falla, no interrumpir la inicialización
            pass

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
    """
    conn = get_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor(dictionary=True)
        key = (tipo_vehiculo or '').strip()
        mapping = {
            'automovil': ['Automovil','Automóvil','A1','A2','A3','A4','A5'],
            'motocicleta': ['Motocicleta','M1','M2','M3','M4'],
            'bicicleta': ['Bicicleta','B1','B2','B3','B4'],
            'otro': ['Otro','Multiuso']
        }
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

def registrar_entrada(placa: str, descripcion: Optional[str]=None, tipo_id: Optional[int]=None, celda_id: Optional[int]=None, tarifa_id: Optional[int]=None) -> Tuple[bool, Optional[str]]:
    """
    Registra la entrada de un vehículo.
    - Si celda_id es None, intenta asignar automáticamente según tipo de vehículo.
    - Guarda tarifa_id en el registro si se proporciona (para usarla al calcular monto).
    """
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
            if tarifa_id:
                cur.execute("INSERT INTO Registro (placa,hora_entrada,estado,celda_id,tarifa_id) VALUES (%s,%s,'activo',%s,%s)",
                            (placa, now, celda_id, tarifa_id))
            else:
                cur.execute("INSERT INTO Registro (placa,hora_entrada,estado,celda_id) VALUES (%s,%s,'activo',%s)",
                            (placa, now, celda_id))
            # marcar celda como ocupada
            cur.execute("UPDATE Celda SET estado='ocupada' WHERE id=%s", (celda_id,))
        else:
            if tarifa_id:
                cur.execute("INSERT INTO Registro (placa,hora_entrada,estado,tarifa_id) VALUES (%s,%s,'activo',%s)", (placa, now, tarifa_id))
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
    """
    Cierra el registro (hora_salida, estado='cerrado') y libera la celda asociada.
    No crea pagos: el flujo recomendado es crear pago primero y luego llamar a este endpoint.
    """
    conn = get_connection()
    if not conn:
        return False, "Error de conexión a BD"
    try:
        cur = conn.cursor(dictionary=True)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("SELECT celda_id, estado FROM Registro WHERE id=%s", (registro_id,))
        row = cur.fetchone()
        if not row:
            cur.close(); conn.close()
            return False, "registro_no_encontrado"
        if row.get('estado') != 'activo':
            cur.close(); conn.close()
            return False, "registro_no_activo"
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
    """
    Devuelve historial con total pagado por registro, tarifa aplicada (valor por hora si aplica),
    la última novedad (descripcion) y la lista de pagos asociados (pagos_list).
    Campos devueltos: id, placa, hora_entrada, hora_salida, estado, celda_id, celda_descripcion,
    tipo, tarifa_valor, total_pagado, novedad, pagos_list
    """
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT
              r.id,
              r.placa,
              r.hora_entrada,
              r.hora_salida,
              r.estado,
              r.celda_id,
              c.descripcion as celda_descripcion,
              v.tipo,
              COALESCE(t.valor, (SELECT valor FROM Tarifa WHERE activo=1 ORDER BY id LIMIT 1)) AS tarifa_valor,
              (SELECT IFNULL(SUM(p.monto),0) FROM Pago p WHERE p.registro_id = r.id) AS total_pagado,
              (SELECT n.descripcion
               FROM Novedad n
               WHERE n.registro_id = r.id
               ORDER BY n.fecha DESC, n.id DESC
               LIMIT 1) AS novedad,
              (SELECT GROUP_CONCAT(CONCAT(p.fecha, '::', p.monto, '::', IFNULL(p.metodo,'')) SEPARATOR '||')
               FROM Pago p
               WHERE p.registro_id = r.id
               ORDER BY p.fecha DESC, p.id DESC) AS pagos_concat
            FROM Registro r
            LEFT JOIN Vehiculo v ON r.placa=v.placa
            LEFT JOIN Celda c ON r.celda_id=c.id
            LEFT JOIN Tarifa t ON r.tarifa_id = t.id
            ORDER BY r.hora_entrada DESC
            LIMIT %s
            """, (limit,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        # Formatear datetimes a string y parsear pagos_concat a lista
        result = []
        for r in rows:
            he = r.get('hora_entrada')
            hs = r.get('hora_salida')
            try:
                if he and not isinstance(he, str):
                    he = he.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                he = str(he) if he else None
            try:
                if hs and not isinstance(hs, str):
                    hs = hs.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                hs = str(hs) if hs else None

            # Parse pagos_concat -> lista de dicts [{fecha, monto, metodo}, ...]
            pagos_list = []
            pagos_concat = r.get('pagos_concat')
            if pagos_concat:
                try:
                    parts = str(pagos_concat).split('||')
                    for pstr in parts:
                        if not pstr:
                            continue
                        # formato: fecha::monto::metodo
                        pparts = pstr.split('::')
                        fecha = pparts[0] if len(pparts) > 0 else None
                        monto_p = None
                        try:
                            monto_p = float(pparts[1]) if len(pparts) > 1 and pparts[1] != '' else None
                        except Exception:
                            monto_p = None
                        metodo_p = pparts[2] if len(pparts) > 2 else None
                        pagos_list.append({'fecha': fecha, 'monto': monto_p, 'metodo': metodo_p})
                except Exception:
                    pagos_list = []

            item = {
                'id': r.get('id'),
                'placa': r.get('placa'),
                'hora_entrada': he,
                'hora_salida': hs,
                'estado': r.get('estado'),
                'celda_id': r.get('celda_id'),
                'celda_descripcion': r.get('celda_descripcion'),
                'tipo': r.get('tipo'),
                'tarifa_valor': float(r.get('tarifa_valor')) if r.get('tarifa_valor') is not None else None,
                'total_pagado': float(r.get('total_pagado') or 0),
                'novedad': r.get('novedad'),
                'pagos': pagos_list
            }
            result.append(item)
        return result
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        print("obtener_historial error:", e)
        return []

def obtener_activos() -> List[Dict]:
    """
    Devuelve registros activos incluyendo la descripcion de la celda, tarifa valor por hora y
    la última novedad (descripcion) asociada al registro si existe.
    Campos devueltos: id, placa, hora_entrada (formateada), celda_id, celda_descripcion, tipo, novedad, tarifa_valor
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
              r.tarifa_id,
              c.descripcion AS celda_descripcion,
              v.tipo,
              COALESCE(t.valor, (SELECT valor FROM Tarifa WHERE activo=1 ORDER BY id LIMIT 1)) AS tarifa_valor,
              (SELECT n.descripcion
               FROM Novedad n
               WHERE n.registro_id = r.id
               ORDER BY n.fecha DESC, n.id DESC
               LIMIT 1) AS novedad
            FROM Registro r
            LEFT JOIN Vehiculo v ON r.placa = v.placa
            LEFT JOIN Celda c ON r.celda_id = c.id
            LEFT JOIN Tarifa t ON r.tarifa_id = t.id
            WHERE r.estado = 'activo'
            ORDER BY r.hora_entrada ASC
        """)
        rows = cur.fetchall()
        cur.close(); conn.close()
        # Normalizar y formatear hora_entrada a string para el frontend
        result = []
        for r in rows:
            hora = r.get('hora_entrada')
            if hora is None:
                hora_str = None
            else:
                try:
                    if isinstance(hora, str):
                        hora_str = hora
                    else:
                        hora_str = hora.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    hora_str = str(hora)
            tarifa_val = r.get('tarifa_valor')
            try:
                tarifa_val = float(tarifa_val) if tarifa_val is not None else None
            except Exception:
                tarifa_val = None
            item = {
                'id': r.get('id'),
                'placa': r.get('placa'),
                'hora_entrada': hora_str,
                'celda_id': r.get('celda_id'),
                'celda_descripcion': r.get('celda_descripcion'),
                'tipo': r.get('tipo'),
                'novedad': r.get('novedad'),
                'tarifa_valor': tarifa_val
            }
            result.append(item)
        return result
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        print("obtener_activos error:", e)
        return []

# ---------------- Celdas ----------------
def crear_celda(codigo_or_desc: str, tipo: Optional[str]=None, ubicacion: Optional[str]=None, estado: str='disponible') -> Tuple[bool, Optional[str]]:
    """
    Nota: la tabla Celda usa 'descripcion' como campo principal.
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

# ---------------- Tarifas y Pagos ----------------
def listar_tarifas() -> List[Dict]:
    conn = get_connection()
    if not conn: return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,nombre,tipo,valor,unidad,activo FROM Tarifa ORDER BY id")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        print("listar_tarifas error:", e)
        return []

def crear_tarifa(nombre: str, tipo: str, valor: float, unidad: str='hora', activo: int=1) -> Tuple[bool, Optional[str]]:
    conn = get_connection()
    if not conn:
        return False, "Error de conexión a BD"
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO Tarifa (nombre,tipo,valor,unidad,activo) VALUES (%s,%s,%s,%s,%s)",
                    (nombre, tipo, valor, unidad, activo))
        conn.commit()
        cur.close(); conn.close()
        return True, None
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        return False, str(e)

def actualizar_tarifa(tarifa_id: int, nombre: Optional[str]=None, tipo: Optional[str]=None,
                      valor: Optional[float]=None, unidad: Optional[str]=None, activo: Optional[int]=None) -> Tuple[bool, Optional[str]]:
    conn = get_connection()
    if not conn:
        return False, "Error de conexión a BD"
    try:
        cur = conn.cursor()
        updates = []; params = []
        if nombre is not None:
            updates.append("nombre=%s"); params.append(nombre)
        if tipo is not None:
            updates.append("tipo=%s"); params.append(tipo)
        if valor is not None:
            updates.append("valor=%s"); params.append(valor)
        if unidad is not None:
            updates.append("unidad=%s"); params.append(unidad)
        if activo is not None:
            updates.append("activo=%s"); params.append(1 if activo else 0)
        if not updates:
            cur.close(); conn.close(); return True, None
        params.append(tarifa_id)
        sql = "UPDATE Tarifa SET " + ", ".join(updates) + " WHERE id=%s"
        cur.execute(sql, tuple(params))
        conn.commit()
        cur.close(); conn.close()
        return True, None
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        return False, str(e)

def crear_pago(registro_id: int, monto: float, metodo: Optional[str]=None, usuario_id: Optional[int]=None, detalle: Optional[str]=None) -> Tuple[bool, Optional[str]]:
    conn = get_connection()
    if not conn:
        return False, "Error de conexión a BD"
    try:
        cur = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("INSERT INTO Pago (registro_id,monto,fecha,metodo,detalle,usuario_id) VALUES (%s,%s,%s,%s,%s,%s)",
                    (registro_id, monto, now, metodo, detalle, usuario_id))
        # Marcar registro como pagado (flag)
        try:
            cur.execute("UPDATE Registro SET pagado=1 WHERE id=%s", (registro_id,))
        except Exception:
            pass
        conn.commit()
        pid = cur.lastrowid
        cur.close(); conn.close()
        return True, pid
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        return False, str(e)

def obtener_pagos_por_registro(registro_id: int) -> List[Dict]:
    conn = get_connection()
    if not conn: return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,registro_id,monto,fecha,metodo,detalle,usuario_id FROM Pago WHERE registro_id=%s ORDER BY fecha DESC", (registro_id,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        print("obtener_pagos_por_registro error:", e)
        return []

def obtener_pagos(limit: int = 200) -> List[Dict]:
    conn = get_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT p.id,p.registro_id,p.monto,p.fecha,p.metodo,p.detalle,p.usuario_id, r.placa FROM Pago p LEFT JOIN Registro r ON p.registro_id=r.id ORDER BY p.fecha DESC LIMIT %s", (limit,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        print("obtener_pagos error:", e)
        return []

def calcular_monto_por_registro(registro_id: int, tarifa_id: Optional[int]=None) -> Optional[float]:
    """
    Calcula monto según la tarifa seleccionada o la tarifa asociada al registro.
    Regla: redondeo hacia arriba por hora (mínimo 1 hora).
    """
    conn = get_connection()
    if not conn: return None
    try:
        cur = conn.cursor(dictionary=True)
        # Obtener registro (incluye tarifa_id si fue guardada)
        cur.execute("SELECT hora_entrada, hora_salida, tarifa_id FROM Registro WHERE id=%s", (registro_id,))
        row = cur.fetchone()
        if not row:
            cur.close(); conn.close(); return None
        hora_entrada = row['hora_entrada']
        hora_salida = row['hora_salida'] or datetime.now()
        registro_tarifa_id = row.get('tarifa_id')

        # Priorizar tarifa_id pasado por parámetro, luego tarifa asociada al registro, luego tarifa activa por defecto
        tarifa_to_use = None
        if tarifa_id:
            tarifa_to_use = tarifa_id
        elif registro_tarifa_id:
            tarifa_to_use = registro_tarifa_id

        if tarifa_to_use:
            cur.execute("SELECT tipo,valor FROM Tarifa WHERE id=%s AND activo=1 LIMIT 1", (tarifa_to_use,))
            t = cur.fetchone()
        else:
            cur.execute("SELECT tipo,valor FROM Tarifa WHERE activo=1 ORDER BY id LIMIT 1")
            t = cur.fetchone()

        if not t:
            tipo = 'por_hora'; valor = 5000.0
        else:
            tipo = t['tipo']; valor = float(t['valor'])

        # Normalizar datetimes
        if isinstance(hora_entrada, str):
            hora_entrada = datetime.strptime(hora_entrada, '%Y-%m-%d %H:%M:%S')
        if isinstance(hora_salida, str):
            hora_salida = datetime.strptime(hora_salida, '%Y-%m-%d %H:%M:%S')
        delta = hora_salida - hora_entrada
        minutos = max(0, int(delta.total_seconds() // 60))
        if tipo == 'fijo':
            monto = valor
        else:
            horas = max(1, (minutos + 59) // 60)  # redondeo hacia arriba, mínimo 1
            monto = horas * valor
        cur.close(); conn.close()
        return float(monto)
    except Exception as e:
        try: cur.close(); conn.close()
        except: pass
        print("calcular_monto_por_registro error:", e)
        return None

# Inicializar DB al importar (si se ejecuta directamente)
if __name__ == '__main__':
    init_db()