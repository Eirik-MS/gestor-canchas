import bcrypt
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from conexion import conectar

# ─────────────────────────────────────────
#  ALTA
# ─────────────────────────────────────────
def crear_complejo(id_barrio, nombre, direccion, telefono, email, password, descripcion=""):
    """Registra un nuevo complejo deportivo con su login propio."""
    conexion = conectar()
    cursor   = conexion.cursor()
    try:
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        sql = """
            INSERT INTO complejo
                (id_barrio, nombre, direccion, telefono, email, password, descripcion)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (id_barrio, nombre, direccion, telefono, email, password_hash, descripcion))
        conexion.commit()
        print(f"✓ Complejo '{nombre}' creado correctamente.")
    except Exception as e:
        conexion.rollback()
        print(f"✗ Error al crear complejo: {e}")
        raise
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  CONSULTA — todos los activos
# ─────────────────────────────────────────
def listar_complejos():
    """Lista todos los complejos activos con su ciudad y barrio."""
    conexion = conectar()
    cursor   = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT co.id_complejo, co.nombre, co.direccion, co.telefono, co.email,
                   co.descripcion, b.nombre AS barrio, ci.nombre AS ciudad,
                   pr.nombre AS provincia
            FROM complejo co
            JOIN barrio   b  ON co.id_barrio    = b.id_barrio
            JOIN ciudad   ci ON b.id_ciudad     = ci.id_ciudad
            JOIN provincia pr ON ci.id_provincia = pr.id_provincia
            WHERE co.activo = TRUE AND co.fecha_baja IS NULL
            ORDER BY co.nombre
        """)
        complejos = cursor.fetchall()
        for c in complejos:
            print(c)
        return complejos
    except Exception as e:
        print(f"✗ Error al listar complejos: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  CONSULTA — filtrar por ciudad o barrio
# ─────────────────────────────────────────
def buscar_complejos(id_ciudad=None, id_barrio=None):
    """Filtra complejos por ciudad o barrio. Usado en la búsqueda del usuario."""
    conexion = conectar()
    cursor   = conexion.cursor(dictionary=True)
    try:
        condiciones = ["co.activo = TRUE", "co.fecha_baja IS NULL"]
        valores = []
        if id_barrio:
            condiciones.append("co.id_barrio = %s")
            valores.append(id_barrio)
        elif id_ciudad:
            condiciones.append("b.id_ciudad = %s")
            valores.append(id_ciudad)

        sql = f"""
            SELECT co.id_complejo, co.nombre, co.direccion, co.telefono,
                   b.nombre AS barrio, ci.nombre AS ciudad
            FROM complejo co
            JOIN barrio   b  ON co.id_barrio  = b.id_barrio
            JOIN ciudad   ci ON b.id_ciudad   = ci.id_ciudad
            WHERE {' AND '.join(condiciones)}
            ORDER BY co.nombre
        """
        cursor.execute(sql, tuple(valores))
        return cursor.fetchall()
    except Exception as e:
        print(f"✗ Error al buscar complejos: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  MODIFICACIÓN
# ─────────────────────────────────────────
def modificar_complejo(id_complejo, nombre=None, direccion=None, telefono=None, descripcion=None):
    conexion = conectar()
    cursor   = conexion.cursor()
    try:
        campos, valores = [], []
        if nombre      is not None: campos.append("nombre = %s");      valores.append(nombre)
        if direccion   is not None: campos.append("direccion = %s");   valores.append(direccion)
        if telefono    is not None: campos.append("telefono = %s");    valores.append(telefono)
        if descripcion is not None: campos.append("descripcion = %s"); valores.append(descripcion)

        if not campos:
            print("✗ No se proporcionó ningún campo para modificar.")
            return

        valores.append(id_complejo)
        sql = f"UPDATE complejo SET {', '.join(campos)} WHERE id_complejo = %s AND fecha_baja IS NULL"
        cursor.execute(sql, tuple(valores))
        conexion.commit()

        if cursor.rowcount == 0:
            print(f"✗ No se encontró complejo con ID {id_complejo}.")
        else:
            print(f"✓ Complejo ID {id_complejo} actualizado.")
    except Exception as e:
        conexion.rollback()
        print(f"✗ Error al modificar complejo: {e}")
        raise
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  BAJA LÓGICA
# ─────────────────────────────────────────
def eliminar_complejo(id_complejo):
    conexion = conectar()
    cursor   = conexion.cursor()
    try:
        cursor.execute("""
            UPDATE complejo SET fecha_baja = NOW(), activo = FALSE
            WHERE id_complejo = %s AND fecha_baja IS NULL
        """, (id_complejo,))
        conexion.commit()
        if cursor.rowcount == 0:
            print(f"✗ No se encontró complejo activo con ID {id_complejo}.")
        else:
            print(f"✓ Complejo ID {id_complejo} dado de baja.")
    except Exception as e:
        conexion.rollback()
        print(f"✗ Error al dar de baja complejo: {e}")
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  LOGIN del complejo
# ─────────────────────────────────────────
def login_complejo(email, password):
    conexion = conectar()
    cursor   = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id_complejo, nombre, email, password
            FROM complejo
            WHERE email = %s AND activo = TRUE AND fecha_baja IS NULL
        """, (email,))
        complejo = cursor.fetchone()

        if not complejo:
            print("✗ Email o password incorrectos.")
            return None

        if bcrypt.checkpw(password.encode("utf-8"), complejo["password"].encode("utf-8")):
            print(f"✓ Login exitoso. Bienvenido, {complejo['nombre']}.")
            complejo.pop("password")
            return complejo
        else:
            print("✗ Email o password incorrectos.")
            return None
    except Exception as e:
        print(f"✗ Error en login complejo: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()
