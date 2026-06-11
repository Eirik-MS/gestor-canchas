import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from conexion import conectar

# ─────────────────────────────────────────
#  ALTA
# ─────────────────────────────────────────
def crear_cancha(id_complejo, id_tipo_cancha, nombre, techada, precio_por_hora):
    conexion = conectar()
    cursor   = conexion.cursor()
    try:
        sql = """
            INSERT INTO cancha (id_complejo, id_tipo_cancha, nombre, techada, precio_por_hora)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (id_complejo, id_tipo_cancha, nombre, techada, precio_por_hora))
        conexion.commit()
        print(f"✓ Cancha '{nombre}' creada en complejo ID {id_complejo}.")
    except Exception as e:
        conexion.rollback()
        print(f"✗ Error al crear cancha: {e}")
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  CONSULTA — canchas de un complejo
# ─────────────────────────────────────────
def listar_canchas_complejo(id_complejo):
    conexion = conectar()
    cursor   = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT c.id_cancha, c.nombre, tc.nombre AS tipo, tc.capacidad_jugadores,
                   c.techada, c.precio_por_hora, c.disponible
            FROM cancha      c
            JOIN tipo_cancha tc ON c.id_tipo_cancha = tc.id_tipo_cancha
            WHERE c.id_complejo = %s AND c.fecha_baja IS NULL
            ORDER BY c.nombre
        """, (id_complejo,))
        canchas = cursor.fetchall()
        for c in canchas:
            print(c)
        return canchas
    except Exception as e:
        print(f"✗ Error al listar canchas: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  CONSULTA — disponibilidad por filtros
# ─────────────────────────────────────────
def buscar_canchas_disponibles(fecha, hora_inicio, hora_fin, id_barrio=None, id_ciudad=None):
    """
    Busca canchas libres en una fecha y rango horario.
    Valida que el complejo esté abierto ese día y horario.
    fecha: 'YYYY-MM-DD', hora_inicio / hora_fin: 'HH:MM'
    """
    from datetime import date
    # Día de la semana ISO: 1=Lunes ... 7=Domingo
    dia_iso = date.fromisoformat(fecha).isoweekday()

    conexion = conectar()
    cursor   = conexion.cursor(dictionary=True)
    try:
        condicion_geo = ""
        valores = [fecha, hora_fin, hora_inicio, id_complejo_placeholder := None]

        # Filtro geográfico
        if id_barrio:
            condicion_geo = "AND co.id_barrio = %s"
            valores_geo   = [id_barrio]
        elif id_ciudad:
            condicion_geo = "AND b.id_ciudad = %s"
            valores_geo   = [id_ciudad]
        else:
            condicion_geo = ""
            valores_geo   = []

        sql = f"""
            SELECT c.id_cancha, c.nombre AS cancha, tc.nombre AS tipo,
                   tc.capacidad_jugadores, c.techada, c.precio_por_hora,
                   co.id_complejo, co.nombre AS complejo, co.direccion, co.telefono,
                   b.nombre AS barrio, ci.nombre AS ciudad
            FROM cancha      c
            JOIN tipo_cancha tc ON c.id_tipo_cancha  = tc.id_tipo_cancha
            JOIN complejo    co ON c.id_complejo      = co.id_complejo
            JOIN barrio      b  ON co.id_barrio       = b.id_barrio
            JOIN ciudad      ci ON b.id_ciudad        = ci.id_ciudad
            WHERE c.disponible  = TRUE
              AND co.activo     = TRUE
              AND c.fecha_baja  IS NULL
              {condicion_geo}
              -- Que el complejo esté abierto en ese horario ese día
              AND EXISTS (
                  SELECT 1 FROM horario_complejo h
                  WHERE h.id_complejo  = co.id_complejo
                    AND h.dia_semana   = {dia_iso}
                    AND h.activo       = TRUE
                    AND %s >= h.hora_apertura
                    AND %s <= h.hora_cierre
              )
              -- Que no haya otra reserva que se solape
              AND c.id_cancha NOT IN (
                  SELECT id_cancha FROM reserva
                  WHERE fecha     = %s
                    AND estado   != 'cancelada'
                    AND hora_inicio < %s
                    AND hora_fin    > %s
              )
            ORDER BY co.nombre, c.nombre
        """
        params = valores_geo + [hora_inicio, hora_fin, fecha, hora_fin, hora_inicio]
        cursor.execute(sql, params)
        canchas = cursor.fetchall()
        print(f"→ {len(canchas)} cancha(s) disponibles encontradas.")
        return canchas
    except Exception as e:
        print(f"✗ Error al buscar canchas: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  MODIFICACIÓN
# ─────────────────────────────────────────
def modificar_cancha(id_cancha, nombre=None, techada=None, precio_por_hora=None, disponible=None):
    conexion = conectar()
    cursor   = conexion.cursor()
    try:
        campos, valores = [], []
        if nombre          is not None: campos.append("nombre = %s");          valores.append(nombre)
        if techada         is not None: campos.append("techada = %s");         valores.append(techada)
        if precio_por_hora is not None: campos.append("precio_por_hora = %s"); valores.append(precio_por_hora)
        if disponible      is not None: campos.append("disponible = %s");      valores.append(disponible)

        if not campos:
            print("✗ No se proporcionó ningún campo para modificar.")
            return

        valores.append(id_cancha)
        sql = f"UPDATE cancha SET {', '.join(campos)} WHERE id_cancha = %s AND fecha_baja IS NULL"
        cursor.execute(sql, tuple(valores))
        conexion.commit()
        if cursor.rowcount == 0:
            print(f"✗ No se encontró cancha con ID {id_cancha}.")
        else:
            print(f"✓ Cancha ID {id_cancha} actualizada.")
    except Exception as e:
        conexion.rollback()
        print(f"✗ Error al modificar cancha: {e}")
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  BAJA LÓGICA
# ─────────────────────────────────────────
def eliminar_cancha(id_cancha):
    conexion = conectar()
    cursor   = conexion.cursor()
    try:
        cursor.execute("""
            UPDATE cancha SET fecha_baja = NOW(), disponible = FALSE
            WHERE id_cancha = %s AND fecha_baja IS NULL
        """, (id_cancha,))
        conexion.commit()
        if cursor.rowcount == 0:
            print(f"✗ No se encontró cancha activa con ID {id_cancha}.")
        else:
            print(f"✓ Cancha ID {id_cancha} dada de baja.")
    except Exception as e:
        conexion.rollback()
        print(f"✗ Error al dar de baja cancha: {e}")
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  TIPOS DE CANCHA (catálogo)
# ─────────────────────────────────────────
def listar_tipos_cancha():
    conexion = conectar()
    cursor   = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM tipo_cancha WHERE fecha_baja IS NULL ORDER BY capacidad_jugadores")
        return cursor.fetchall()
    except Exception as e:
        print(f"✗ Error al listar tipos: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()
