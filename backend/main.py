import sys, os
sys.path.append(os.path.dirname(__file__))

from models.usuarios  import crear_usuario, login_usuario
from models.complejos import crear_complejo, listar_complejos, login_complejo
from models.canchas   import listar_canchas_complejo, buscar_canchas_disponibles
from models.reservas  import crear_reserva, listar_reservas_usuario

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def sep():
    print("\n" + "─" * 45)

def pausar():
    input("\n  Presioná Enter para continuar...")

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
            try:
                dni      = int(input("  DNI: "))
                nombre   = input("  Nombre: ").strip()
                apellido = input("  Apellido: ").strip()
                email    = input("  Email: ").strip()
                telefono = input("  Teléfono: ").strip()
                password = input("  Password: ").strip()
                crear_usuario(dni, nombre, apellido, email, telefono, password)
                print("\n  ¡Cuenta creada! Ya podés iniciar sesión.")
            except ValueError:
                print("  ✗ El DNI debe ser un número.")
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

    # 1. Fecha y horario
    fecha       = input("  Fecha (YYYY-MM-DD): ").strip()
    hora_inicio = input("  Hora inicio (HH:MM): ").strip()
    hora_fin    = input("  Hora fin   (HH:MM): ").strip()

    # 2. Buscar canchas disponibles
    sep()
    print("  Buscando canchas disponibles...")
    canchas = buscar_canchas_disponibles(fecha, hora_inicio, hora_fin)

    if not canchas:
        print("\n  No hay canchas disponibles para ese horario.")
        pausar()
        return

    # 3. Mostrar opciones
    sep()
    print(f"  {'#':<4} {'COMPLEJO':<25} {'CANCHA':<14} {'TIPO':<10} {'JUG':>4} {'TECH':>5} {'$/H':>9}")
    sep()
    for i, c in enumerate(canchas, 1):
        techada = "Sí" if c['techada'] else "No"
        print(f"  {i:<4} {c['complejo']:<25} {c['cancha']:<14} {c['tipo']:<10} {c['capacidad_jugadores']:>4} {techada:>5} ${c['precio_por_hora']:>8}")

    # 4. Usuario elige
    sep()
    try:
        eleccion = int(input("  Elegí el número de cancha (0 para cancelar): "))
        if eleccion == 0:
            return
        if eleccion < 1 or eleccion > len(canchas):
            print("  ✗ Número inválido.")
            pausar()
            return
    except ValueError:
        print("  ✗ Ingresá un número.")
        pausar()
        return

    cancha_elegida = canchas[eleccion - 1]

    # 5. Confirmar
    sep()
    print("  RESUMEN DE TU RESERVA")
    sep()
    print(f"  Complejo : {cancha_elegida['complejo']}")
    print(f"  Cancha   : {cancha_elegida['cancha']} ({cancha_elegida['tipo']})")
    print(f"  Fecha    : {fecha}")
    print(f"  Horario  : {hora_inicio} a {hora_fin}")
    sep()

    confirmar = input("  ¿Confirmás la reserva? (s/n): ").strip().lower()
    if confirmar != "s":
        print("  Reserva cancelada.")
        pausar()
        return

    # 6. Crear reserva (medio de pago 1 = efectivo por defecto, se expande en Sprint 2)
    id_reserva = crear_reserva(
        dni          = usuario['dni'],
        id_cancha    = cancha_elegida['id_cancha'],
        fecha        = fecha,
        hora_inicio  = hora_inicio,
        hora_fin     = hora_fin,
        id_medio_pago= 1
    )

    if id_reserva:
        sep()
        print(f"  ✓ ¡Reserva confirmada! ID de reserva: #{id_reserva}")
        print(f"  Guardala por si necesitás consultarla.")
    pausar()

# ─────────────────────────────────────────
#  VER MIS RESERVAS
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
            print(f"  #{r['id_reserva']} | {r['complejo']} — {r['cancha']}")
            print(f"       {r['fecha']} | {r['hora_inicio']} a {r['hora_fin']}")
            print(f"       Total: ${r['total']} | Estado: {r['estado_reserva']}")
            print()
    pausar()

# ─────────────────────────────────────────
#  PORTAL COMPLEJO
# ─────────────────────────────────────────
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
            print("  Barrios: 1=Palermo | 2=Belgrano | 3=Almagro")
            print("           4=Villa Urquiza | 5=Caballito | 6=Flores")
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
        else:
            print("  ✗ Opción inválida.")

# ─────────────────────────────────────────
#  MENÚ COMPLEJO LOGUEADO
# ─────────────────────────────────────────
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
                    print(f"  {c['nombre']} | {c['tipo']} | {c['capacidad_jugadores']} jug. | {techada} | ${c['precio_por_hora']}/h | {disponible}")
            pausar()

        elif op == "0":
            print(f"\n  ¡Hasta luego, {complejo['nombre']}!")
            break
        else:
            print("  ✗ Opción inválida.")

# ─────────────────────────────────────────
#  MENÚ PRINCIPAL
# ─────────────────────────────────────────
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
            sep()
            print("  ¡Hasta luego!")
            sep()
            break
        else:
            print("  ✗ Opción inválida.")

if __name__ == "__main__":
    main()