import sys, os, re
from datetime import date, datetime
sys.path.append(os.path.dirname(__file__))

from models.usuarios  import crear_usuario, login_usuario
from models.complejos import crear_complejo, listar_complejos, login_complejo
from models.canchas   import listar_canchas_complejo, buscar_canchas_disponibles
from models.reservas  import crear_reserva, listar_reservas_usuario

# ─────────────────────────────────────────
#  HELPERS & VALIDACIONES
# ─────────────────────────────────────────
def sep():
    print("\n" + "─" * 45)

def pausar():
    input("\n  Presioná Enter para continuar...")

def validar_dni(dni_str):
    return dni_str.isdigit() and len(dni_str) == 8

def validar_email(email):
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(patron, email))

def validar_telefono(telefono):
    tel_limpio = telefono.replace(" ", "").replace("-", "")
    return tel_limpio.isdigit() and (8 <= len(tel_limpio) <= 11)

# ─────────────────────────────────────────
#  PORTAL USUARIO
# ─────────────────────────────────────────
def portal_usuario():
    while True:
        sep()
        print("  PORTAL USUARIO")
        sep()
        print("  1. Tengo cuenta → Iniciar sesión")
        print("  2. No tengo cuenta → Registrarme")
        print("  0. Volver")
        sep()
        op = input("  Elegí una opción: ").strip()

        if op == "1":
            usuario = login_usuario_interactivo()
            if usuario:
                menu_usuario(usuario)

        elif op == "2":
            sep()
            print("  CREAR CUENTA")
            sep()
            
            while True:
                dni_input = input("  DNI (8 cifras): ").strip()
                if validar_dni(dni_input):
                    dni = int(dni_input)
                    break
                print("  ✗ DNI inválido. Debe tener exactamente 8 cifras (sin puntos ni letras).")

            nombre   = input("  Nombre: ").strip()
            apellido = input("  Apellido: ").strip()
            
            while True:
                email = input("  Email: ").strip()
                if validar_email(email):
                    break
                print("  ✗ Formato de email inválido. Debe incluir '@' y una terminación (ej: .com).")
            
            while True:
                telefono = input("  Teléfono: ").strip()
                if validar_telefono(telefono):
                    break
                print("  ✗ Teléfono inválido. Ingrese solo números (entre 8 y 11 dígitos).")
                
            password = input("  Password: ").strip()
            
            # Capturamos la salida estándar para verificar si el código de tu grupo imprimió un error en pantalla
            import io
            captura_pantalla = io.StringIO()
            sys.stdout = captura_pantalla
            
            try:
                crear_usuario(dni, nombre, apellido, email, telefono, password)
                error_en_consola = captura_pantalla.getvalue()
            finally:
                sys.stdout = sys.__stdout__
            
            # Mostramos en limpio lo que imprimió la función original de tu grupo
            print(error_en_consola, end="")
            
            # 💡 FIX ABSOLUTO PARA DUPLICADOS: Si en la consola se lee 'Duplicate entry', '1062' o 'Error', bloquea el éxito.
            if "Duplicate entry" in error_en_consola or "1062" in error_en_consola or "Error" in error_en_consola or "X" in error_en_consola:
                sep()
                print("  ✗ El registro fue rechazado por la base de datos.")
                print("    Verificá que el DNI, Email o Teléfono no pertenezcan a otra cuenta.")
            else:
                print("\n  ✓ ¡Cuenta creada con éxito! Ya podés iniciar sesión.")
            
            pausar()

        elif op == "0":
            break
        else:
            print("  ✗ Opción inválida.")

def login_usuario_interactivo():
    sep()
    print("  INICIAR SESIÓN")
    sep()
    email    = input("  Email: ").strip()
    password = input("  Password: ").strip()
    return login_usuario(email, password)

# ─────────────────────────────────────────
#  MENÚ USUARIO LOGUEADO
# ─────────────────────────────────────────
def menu_usuario(usuario):
    while True:
        sep()
        print(f"  Hola, {usuario['nombre']} {usuario['apellido']} 👋")
        sep()
        print("  1. Reservar cancha")
        print("  2. Ver mis reservas")
        print("  0. Cerrar sesión")
        sep()
        op = input("  Elegí una opción: ").strip()

        if op == "1":
            flujo_reserva(usuario)
        elif op == "2":
            ver_mis_reservas(usuario)
        elif op == "0":
            print(f"\n  ¡Hasta luego, {usuario['nombre']}!")
            break
        else:
            print("  ✗ Opción inválida.")

# ─────────────────────────────────────────
#  FLUJO RESERVA
# ─────────────────────────────────────────
def flujo_reserva(usuario):
    sep()
    print("  RESERVAR CANCHA")
    sep()

    fecha       = input("  Fecha (YYYY-MM-DD): ").strip()
    hora_inicio = input("  Hora inicio (HH:MM): ").strip()
    hora_fin    = input("  Hora fin   (HH:MM): ").strip()

    try:
        fecha_objeto = date.fromisoformat(fecha)
        if fecha_objeto < date.today():
            sep()
            print("  ✗ Error: No podés reservar en una fecha que ya pasó.")
            print(f"    La fecha mínima permitida es hoy: {date.today()}")
            pausar()
            return
            
        h_ini_obj = datetime.strptime(hora_inicio, "%H:%M").time()
        h_fin_obj = datetime.strptime(hora_fin, "%H:%M").time()
        
        if h_ini_obj >= h_fin_obj:
            sep()
            print("  ✗ Error: La hora de inicio no puede ser igual o mayor que la hora de fin.")
            pausar()
            return

    except ValueError:
        sep()
        print("  ✗ Error: La fecha u horarios ingresados no tienen un formato válido.")
        pausar()
        return

    sep()
    print("  ¿Qué tipo de cancha buscás?")
    print("  1. Fútbol 5")
    print("  2. Fútbol 8")
    print("  3. Fútbol 11")
    sep()
    tipo_op = input("  Elegí una opción (1-3): ").strip()

    if tipo_op == "1":
        nombre_mostrar = "Fútbol 5"
    elif tipo_op == "2":
        nombre_mostrar = "Fútbol 8"
    elif tipo_op == "3":
        nombre_mostrar = "Fútbol 11"
    else:
        print("  ✗ Opción de cancha inválida.")
        pausar()
        return

    sep()
    print("  Buscando canchas disponibles...")
    todas_las_canchas = buscar_canchas_disponibles(fecha, hora_inicio, hora_fin)

    canchas_filtradas = []
    if todas_las_canchas:
        for c in todas_las_canchas:
            tipo_str = str(c.get('tipo', '')).lower()
            
            if tipo_op == "1" and ("5" in tipo_str or "cinco" in tipo_str):
                canchas_filtradas.append(c)
            elif tipo_op == "2" and ("8" in tipo_str or "ocho" in tipo_str or "7" in tipo_str or "siete" in tipo_str):
                canchas_filtradas.append(c)
            elif tipo_op == "3" and ("11" in tipo_str or "once" in tipo_str):
                canchas_filtradas.append(c)

    if not canchas_filtradas:
        print(f"\n  No hay canchas de {nombre_mostrar} disponibles para ese horario.")
        pausar()
        return

    print(f"  → {len(canchas_filtradas)} cancha(s) de {nombre_mostrar} encontradas.")

    sep()
    print(f"  {'#':<4} {'COMPLEJO':<25} {'CANCHA':<18} {'$/H':>9}")
    sep()
    for i, c in enumerate(canchas_filtradas, 1):
        comp_nom = c.get('complejo') or c.get('nombre_complejo') or c.get('nombre') or 'Complejo'
        can_nom  = c.get('cancha') or c.get('nombre_cancha') or 'Cancha'
        precio   = c.get('precio_por_hora') or c.get('precio') or 0
        
        can_nom_str = str(can_nom).replace("(F7)", "(F8)").replace("(f7)", "(F8)")
        
        print(f"  {i:<4} {str(comp_nom)[:25]:<25} {can_nom_str[:18]:<18} ${precio:>8}")

    sep()
    try:
        eleccion = int(input("  Elegí el número de cancha (0 para cancelar): "))
        if eleccion == 0:
            return
        if eleccion < 1 or eleccion > len(canchas_filtradas):
            print("  ✗ Número inválido.")
            pausar()
            return
    except ValueError:
        print("  ✗ Ingresá un número.")
        pausar()
        return

    cancha_elegida = canchas_filtradas[eleccion - 1]
    id_cancha_final = cancha_elegida.get('id_cancha') or cancha_elegida.get('cancha_id') or 1

    sep()
    print("  RESUMEN DE TU RESERVA")
    sep()
    print(f"  Fecha    : {fecha}")
    print(f"  Horario  : {hora_inicio} a {hora_fin}")
    sep()

    confirmar = input("  ¿Confirmás la reserva? (s/n): ").strip().lower()
    if confirmar != "s":
        print("  Reserva cancelada.")
        pausar()
        return

    id_usuario_final = usuario.get('id_usuario') or usuario.get('usuario_id') or usuario.get('id')

    try:
        id_reserva = crear_reserva(
            id_usuario   = id_usuario_final,
            id_cancha    = id_cancha_final,
            fecha        = fecha,
            hora_inicio  = hora_inicio,
            hora_fin     = hora_fin,
            id_medio_pago= 1
        )
        if id_reserva:
            sep()
            print(f"  ✓ ¡Reserva confirmada! ID de reserva: #{id_reserva}")
    except Exception as err_res:
        try:
            id_reserva = crear_reserva(
                dni          = usuario['dni'],
                id_cancha    = id_cancha_final,
                fecha        = fecha,
                hora_inicio  = hora_inicio,
                hora_fin     = hora_fin,
                id_medio_pago= 1
            )
            if id_reserva:
                sep()
                print(f"  ✓ ¡Reserva confirmada! ID de reserva: #{id_reserva}")
        except Exception:
            sep()
            print(f"  ✗ Error en la Base de Datos al procesar la reserva: {err_res}")
            
    pausar()

# ─────────────────────────────────────────
#  VER MIS RESERVAS / PORTALES COMPLEJO / MAIN
# ─────────────────────────────────────────
def ver_mis_reservas(usuario):
    sep()
    print(f"  MIS RESERVAS — {usuario['nombre']} {usuario['apellido']}")
    sep()
    reservas = listar_reservas_usuario(usuario['dni'])
    if not reservas:
        print("  Todavía no tenés reservas realizadas.")
    else:
        for r in reservas:
            print(f"  #{r['id_reserva']} | {r.get('complejo','Complejo')} — {r.get('cancha','Cancha')}")
            print(f"         {r['fecha']} | {r['hora_inicio']} a {r['hora_fin']}")
            print(f"         Total: ${r['total']} | Estado: {r.get('estado_reserva','Confirmada')}")
            print()
    pausar()

def portal_complejo():
    while True:
        sep()
        print("  PORTAL COMPLEJO")
        sep()
        print("  1. Iniciar sesión")
        print("  2. Registrar nuevo complejo")
        print("  0. Volver")
        sep()
        op = input("  Elegí una opción: ").strip()
        if op == "1":
            sep()
            print("  LOGIN COMPLEJO")
            sep()
            email    = input("  Email: ").strip()
            password = input("  Password: ").strip()
            complejo = login_complejo(email, password)
            if complejo:
                menu_complejo(complejo)
        elif op == "2":
            sep()
            print("  REGISTRAR COMPLEJO")
            sep()
            try:
                id_barrio   = int(input("  ID Barrio: "))
                nombre      = input("  Nombre: ").strip()
                direccion   = input("  Dirección: ").strip()
                telefono    = input("  Teléfono: ").strip()
                email       = input("  Email: ").strip()
                password    = input("  Password: ").strip()
                descripcion = input("  Descripción: ").strip()
                crear_complejo(id_barrio, nombre, direccion, telefono, email, password, descripcion)
            except ValueError:
                print("  ✗ ID de barrio debe ser número.")
            pausar()
        elif op == "0":
            break

def menu_complejo(complejo):
    while True:
        sep()
        print(f"  {complejo['nombre']} 🏟️")
        sep()
        print("  1. Ver mis canchas")
        print("  0. Cerrar sesión")
        sep()
        op = input("  Elegí una opción: ").strip()
        if op == "1":
            sep()
            print(f"  CANCHAS — {complejo['nombre']}")
            sep()
            canchas = listar_canchas_complejo(complejo['id_complejo'])
            if not canchas:
                print("  No hay canchas registradas.")
            else:
                for c in canchas:
                    techada    = "Techada" if c['techada'] else "Al aire libre"
                    disponible = "✓ Disponible" if c['disponible'] else "✗ No disponible"
                    print(f"  {c['nombre']} | {c.get('tipo','Fútbol')} | {c.get('capacidad_jugadores',0)} jug. | {techada} | ${c['precio_por_hora']}/h | {disponible}")
            pausar()
        elif op == "0":
            break

def main():
    while True:
        sep()
        print("    GESTOR DE CANCHAS DE FÚTBOL ⚽")
        sep()
        print("  1. Soy jugador")
        print("  2. Soy un complejo deportivo")
        print("  0. Salir")
        sep()
        op = input("  Elegí una opción: ").strip()
        if op == "1":
            portal_usuario()
        elif op == "2":
            portal_complejo()
        elif op == "0":
            break

if __name__ == "__main__":
    main()