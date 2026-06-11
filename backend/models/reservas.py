from datetime import datetime, timedelta
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from conexion import conectar

# ─────────────────────────────────────────
#  ALTA — crear reserva
# ─────────────────────────────────────────
def crear_reserva(dni, id_cancha, fecha, hora_inicio, hora_fin, id_medio_pago, nro_operacion=None):
    """
    Crea una reserva y su pago asociado.
    - Calcula el total automáticamente.
    - Si el medio es efectivo o transferencia → pago pendiente con fecha_limite_pago.
    - Si el medio es tarjeta (id=3) → pago pagado, sin fecha_limite.
    """
    conexion = conectar()
    cursor   = conexion.cursor(dictionary=True)
    try:
        # 1. Obtener precio de la cancha
        cursor.execute("SELECT precio_por_hora FROM cancha WHERE id_cancha = %s", (id_cancha,))
        cancha = cursor.fetchone()
        if not cancha:
            print("✗ Cancha no encontrada.")
            return None

        # 2. Calcular total
        fmt = "%H:%M"
        dt_inicio = datetime.strptime(hora_inicio, fmt)
        dt_fin    = datetime.strptime(hora_fin, fmt)
        horas     = (dt_fin - dt_inicio).seconds / 3600
        total     = round(horas * float(cancha["precio_por_hora"]), 2)

        # 3. Insertar reserva
        cursor2 = conexion.cursor()
        cursor2.execute("""
            INSERT INTO reserva (dni, id_cancha, fecha, hora_inicio, hora_fin, total)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (dni, id_cancha, fecha, hora_inicio, hora_fin, total))
        id_reserva = cursor2.lastrowid

        # 4. Calcular fecha_limite_pago (solo para efectivo/transferencia)
        es_tarjeta    = (id_medio_pago == 3)
        estado_pago   = "pagado" if es_tarjeta else "pendiente"
        fecha_limite  = None
        if not es_tarjeta:
            dt_reserva   = datetime.strptime(f"{fecha} {hora_inicio}", "%Y-%m-%d %H:%M")
            fecha_limite = dt_reserva - timedelta(minutes=40)

        # 5. Insertar pago
        cursor2.execute("""
            INSERT INTO pago (id_reserva, id_medio_pago, nro_operacion, monto, estado_pago, fecha_limite_pago)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (id_reserva, id_medio_pago, nro_operacion, total, estado_pago, fecha_limite))

        conexion.commit()
        print(f"✓ Reserva creada. ID: {id_reserva} | Total: ${total} | Pago: {estado_pago}")
        return id_reserva

    except Exception as e:
        conexion.rollback()
        print(f"✗ Error al crear reserva: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  CONSULTA — reservas de un usuario
# ─────────────────────────────────────────
def listar_reservas_usuario(dni):
    conexion = conectar()
    cursor   = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT r.id_reserva, co.nombre AS complejo, c.nombre AS cancha,
                   tc.nombre AS tipo, r.fecha, r.hora_inicio, r.hora_fin,
                   r.total, r.estado AS estado_reserva,
                   mp.nombre AS medio_pago, p.estado_pago, p.fecha_limite_pago
            FROM reserva     r
            JOIN cancha      c  ON r.id_cancha      = c.id_cancha
            JOIN tipo_cancha tc ON c.id_tipo_cancha  = tc.id_tipo_cancha
            JOIN complejo    co ON c.id_complejo     = co.id_complejo
            LEFT JOIN pago   p  ON r.id_reserva      = p.id_reserva
            LEFT JOIN medio_pago mp ON p.id_medio_pago = mp.id_medio_pago
            WHERE r.dni = %s AND r.fecha_baja IS NULL
            ORDER BY r.fecha DESC, r.hora_inicio
        """, (dni,))
        reservas = cursor.fetchall()
        for r in reservas:
            print(r)
        return reservas
    except Exception as e:
        print(f"✗ Error al listar reservas: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  CONSULTA — panel del complejo
# ─────────────────────────────────────────
def listar_reservas_complejo(id_complejo):
    """
    Devuelve todas las reservas del complejo con estado de pago.
    Marca alerta_vencido=True cuando el plazo de pago ya venció.
    """
    conexion = conectar()
    cursor   = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT r.id_reserva, c.nombre AS cancha, tc.nombre AS tipo,
                   CONCAT(u.nombre,' ',u.apellido) AS usuario, u.telefono,
                   r.fecha, r.hora_inicio, r.hora_fin, r.total,
                   r.estado AS estado_reserva,
                   mp.nombre AS medio_pago, p.nro_operacion,
                   p.estado_pago, p.fecha_limite_pago,
                   CASE
                       WHEN p.estado_pago = 'pendiente'
                        AND p.fecha_limite_pago IS NOT NULL
                        AND NOW() >= p.fecha_limite_pago
                       THEN TRUE ELSE FALSE
                   END AS alerta_vencido,
                   CASE WHEN le.id_espera IS NOT NULL THEN TRUE ELSE FALSE
                   END AS tiene_espera,
                   le.dni AS dni_en_espera
            FROM reserva r
            JOIN cancha       c  ON r.id_cancha       = c.id_cancha
            JOIN tipo_cancha  tc ON c.id_tipo_cancha  = tc.id_tipo_cancha
            JOIN complejo     co ON c.id_complejo     = co.id_complejo
            JOIN usuario      u  ON r.dni             = u.dni
            LEFT JOIN pago    p  ON r.id_reserva      = p.id_reserva
            LEFT JOIN medio_pago mp ON p.id_medio_pago = mp.id_medio_pago
            LEFT JOIN lista_espera le ON r.id_reserva = le.id_reserva
                                     AND le.estado    = 'esperando'
            WHERE co.id_complejo = %s AND r.fecha_baja IS NULL
            ORDER BY r.fecha DESC, r.hora_inicio
        """, (id_complejo,))
        return cursor.fetchall()
    except Exception as e:
        print(f"✗ Error al listar reservas del complejo: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  CANCELAR reserva (baja lógica)
# ─────────────────────────────────────────
def cancelar_reserva(id_reserva):
    conexion = conectar()
    cursor   = conexion.cursor()
    try:
        cursor.execute("""
            UPDATE reserva SET estado = 'cancelada', fecha_baja = NOW()
            WHERE id_reserva = %s AND estado = 'confirmada'
        """, (id_reserva,))
        conexion.commit()
        if cursor.rowcount == 0:
            print(f"✗ No se encontró reserva confirmada con ID {id_reserva}.")
        else:
            print(f"✓ Reserva ID {id_reserva} cancelada.")
            # Si había alguien en espera, también se marca como expirado
            cursor.execute("""
                UPDATE lista_espera SET estado = 'expirado'
                WHERE id_reserva = %s AND estado = 'esperando'
            """, (id_reserva,))
            conexion.commit()
    except Exception as e:
        conexion.rollback()
        print(f"✗ Error al cancelar reserva: {e}")
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  LISTA DE ESPERA — anotarse
# ─────────────────────────────────────────
def anotarse_en_espera(id_reserva, dni):
    """El usuario se anota en lista de espera para una reserva con pago pendiente."""
    conexion = conectar()
    cursor   = conexion.cursor(dictionary=True)
    try:
        # Verificar que la reserva existe, es efectivo y está pendiente
        cursor.execute("""
            SELECT r.id_reserva, p.estado_pago, p.id_medio_pago
            FROM reserva r
            JOIN pago p ON r.id_reserva = p.id_reserva
            WHERE r.id_reserva = %s AND r.estado = 'confirmada'
        """, (id_reserva,))
        reserva = cursor.fetchone()

        if not reserva:
            print("✗ La reserva no existe o ya no está confirmada.")
            return False
        if reserva["estado_pago"] == "pagado":
            print("✗ Esta reserva ya está paga, no se puede anotar en espera.")
            return False
        if reserva["id_medio_pago"] == 3:  # tarjeta
            print("✗ Las reservas con tarjeta no generan lista de espera.")
            return False

        cursor2 = conexion.cursor()
        cursor2.execute("""
            INSERT INTO lista_espera (id_reserva, dni) VALUES (%s, %s)
        """, (id_reserva, dni))
        conexion.commit()
        print(f"✓ Usuario DNI {dni} anotado en lista de espera para reserva ID {id_reserva}.")
        return True
    except Exception as e:
        conexion.rollback()
        print(f"✗ Error al anotarse en espera: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  LISTA DE ESPERA — transferir turno (lo hace el complejo)
# ─────────────────────────────────────────
def transferir_turno(id_reserva_original, id_medio_pago_nuevo=1):
    """
    El complejo transfiere el turno al usuario en lista de espera.
    Pasos: cancela la reserva original → crea una nueva → marca espera como asignada.
    """
    conexion = conectar()
    cursor   = conexion.cursor(dictionary=True)
    try:
        # 1. Obtener datos de la reserva original y del usuario en espera
        cursor.execute("""
            SELECT r.id_cancha, r.fecha, r.hora_inicio, r.hora_fin, r.total,
                   le.dni AS dni_espera, le.id_espera
            FROM reserva r
            JOIN lista_espera le ON r.id_reserva = le.id_reserva
            WHERE r.id_reserva = %s AND le.estado = 'esperando'
        """, (id_reserva_original,))
        datos = cursor.fetchone()

        if not datos:
            print("✗ No hay usuario en espera para esta reserva.")
            return False

        cursor2 = conexion.cursor()

        # 2. Cancelar reserva original
        cursor2.execute("""
            UPDATE reserva SET estado = 'cancelada', fecha_baja = NOW()
            WHERE id_reserva = %s
        """, (id_reserva_original,))

        # 3. Crear nueva reserva para el usuario en espera
        cursor2.execute("""
            INSERT INTO reserva (dni, id_cancha, fecha, hora_inicio, hora_fin, total)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (datos["dni_espera"], datos["id_cancha"], datos["fecha"],
              datos["hora_inicio"], datos["hora_fin"], datos["total"]))
        nueva_id = cursor2.lastrowid

        # 4. Crear pago pendiente para la nueva reserva
        dt_reserva   = datetime.combine(datos["fecha"], datos["hora_inicio"])
        fecha_limite = dt_reserva - timedelta(minutes=40)
        cursor2.execute("""
            INSERT INTO pago (id_reserva, id_medio_pago, monto, estado_pago, fecha_limite_pago)
            VALUES (%s, %s, %s, 'pendiente', %s)
        """, (nueva_id, id_medio_pago_nuevo, datos["total"], fecha_limite))

        # 5. Marcar lista de espera como asignada
        cursor2.execute("""
            UPDATE lista_espera SET estado = 'asignado'
            WHERE id_espera = %s
        """, (datos["id_espera"],))

        conexion.commit()
        print(f"✓ Turno transferido. Nueva reserva ID: {nueva_id} para DNI {datos['dni_espera']}.")
        return nueva_id

    except Exception as e:
        conexion.rollback()
        print(f"✗ Error al transferir turno: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()
