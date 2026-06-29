import os
import re
from flask import Flask, render_template, request, redirect, url_for, session, flash

from backend.models.usuarios  import login_usuario, crear_usuario, modificar_usuario, eliminar_usuario
from backend.models.complejos import login_complejo, crear_complejo, modificar_complejo
from backend.models.reservas  import (listar_reservas_usuario, crear_reserva,
                                       listar_reservas_complejo, cancelar_reserva,
                                       anotarse_en_espera)
from backend.models.canchas   import (buscar_canchas_disponibles, listar_canchas_complejo,
                                       crear_cancha, modificar_cancha, eliminar_cancha,
                                       listar_tipos_cancha)
from backend.conexion import conectar

Web = Flask(__name__, template_folder="frontend")
from datetime import datetime

@Web.context_processor
def inject_now():
    return {"now": datetime.now}

Web.secret_key = os.environ.get("SECRET_KEY", "clave-secreta-desarrollo-2024")

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────
def validar_email(email):
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email))

def validar_dni(dni_str):
    return str(dni_str).isdigit() and len(str(dni_str)) == 8

def login_requerido(tipo=None):
    """Verifica sesión activa. Si tipo='jugador' o 'complejo', verifica el rol."""
    if "cuenta" not in session:
        flash("Tenés que iniciar sesión para acceder.", "warning")
        return redirect(url_for("login"))
    if tipo and session.get("tipo") != tipo:
        flash("No tenés permiso para acceder a esa sección.", "danger")
        return redirect(url_for("home"))
    return None

def obtener_barrios():
    """Lee los barrios desde la BD para los formularios."""
    try:
        conn = conectar()
        cur  = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT b.id_barrio, b.nombre AS barrio, ci.nombre AS ciudad
            FROM barrio b
            JOIN ciudad ci ON b.id_ciudad = ci.id_ciudad
            WHERE b.fecha_baja IS NULL
            ORDER BY ci.nombre, b.nombre
        """)
        barrios = cur.fetchall()
        cur.close(); conn.close()
        return barrios
    except Exception:
        return []

# ─────────────────────────────────────────
#  RUTAS GENERALES
# ─────────────────────────────────────────
@Web.route("/")
def home():
    return render_template("index.html")

@Web.route("/logout")
def logout():
    nombre = session.get("cuenta", {}).get("nombre", "")
    session.clear()
    flash(f"¡Hasta luego, {nombre}! Sesión cerrada correctamente.", "info")
    return redirect(url_for("home"))

# ─────────────────────────────────────────
#  AUTENTICACIÓN
# ─────────────────────────────────────────
@Web.route("/login", methods=["GET", "POST"])
def login():
    if "cuenta" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        tipo     = request.form.get("tipo")
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email y contraseña son obligatorios.", "danger")
            return render_template("login.html")

        if tipo == "complejo":
            cuenta = login_complejo(email, password)
        else:
            cuenta = login_usuario(email, password)

        if cuenta:
            session["tipo"]   = tipo
            session["cuenta"] = cuenta
            flash(f"¡Bienvenido/a, {cuenta['nombre']}! 🎉", "success")
            if tipo == "complejo":
                return redirect(url_for("panel_complejo"))
            return redirect(url_for("home"))
        else:
            flash("Email o contraseña incorrectos.", "danger")

    return render_template("login.html")


@Web.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        errores = []
        dni_str  = request.form.get("dni", "").strip()
        nombre   = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        email    = request.form.get("email", "").strip()
        telefono = request.form.get("telefono", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        # Validaciones
        if not validar_dni(dni_str):
            errores.append("El DNI debe tener exactamente 8 dígitos numéricos.")
        if not nombre:
            errores.append("El nombre es obligatorio.")
        if not apellido:
            errores.append("El apellido es obligatorio.")
        if not validar_email(email):
            errores.append("El formato del email no es válido.")
        if len(password) < 6:
            errores.append("La contraseña debe tener al menos 6 caracteres.")
        if password != confirm:
            errores.append("Las contraseñas no coinciden.")

        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template("registro.html",
                                   dni=dni_str, nombre=nombre, apellido=apellido,
                                   email=email, telefono=telefono)

        try:
            crear_usuario(int(dni_str), nombre, apellido, email, telefono, password)
            flash("¡Cuenta creada con éxito! Ya podés iniciar sesión. ⚽", "success")
            return redirect(url_for("login"))
        except Exception as e:
            msg = str(e)
            if "Duplicate entry" in msg and "dni" in msg:
                flash("Ese DNI ya está registrado.", "danger")
            elif "Duplicate entry" in msg and "email" in msg:
                flash("Ese email ya está registrado.", "danger")
            else:
                flash(f"Error al registrar: {msg}", "danger")

    return render_template("registro.html")


@Web.route("/registro-complejo", methods=["GET", "POST"])
def registro_complejo():
    barrios = obtener_barrios()

    if request.method == "POST":
        errores = []
        nombre      = request.form.get("nombre", "").strip()
        direccion   = request.form.get("direccion", "").strip()
        telefono    = request.form.get("telefono", "").strip()
        email       = request.form.get("email", "").strip()
        password    = request.form.get("password", "")
        confirm     = request.form.get("confirm_password", "")
        id_barrio   = request.form.get("id_barrio")
        descripcion = request.form.get("descripcion", "").strip()

        if not nombre:      errores.append("El nombre del complejo es obligatorio.")
        if not direccion:   errores.append("La dirección es obligatoria.")
        if not id_barrio:   errores.append("Debés seleccionar un barrio.")
        if not validar_email(email): errores.append("El formato del email no es válido.")
        if len(password) < 6:        errores.append("La contraseña debe tener al menos 6 caracteres.")
        if password != confirm:       errores.append("Las contraseñas no coinciden.")

        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template("registro_complejo.html", barrios=barrios)

        try:
            crear_complejo(int(id_barrio), nombre, direccion, telefono, email, password, descripcion)
            flash("¡Complejo registrado con éxito! Ya podés iniciar sesión. 🏟️", "success")
            return redirect(url_for("login"))
        except Exception as e:
            msg = str(e)
            if "Duplicate entry" in msg and "email" in msg:
                flash("Ese email ya está registrado.", "danger")
            else:
                flash(f"Error al registrar complejo: {msg}", "danger")

    return render_template("registro_complejo.html", barrios=barrios)

# ─────────────────────────────────────────
#  BÚSQUEDA Y RESERVA (Jugador)
# ─────────────────────────────────────────
@Web.route("/buscar")
def buscar():
    barrios     = obtener_barrios()
    fecha       = request.args.get("fecha", "")
    hora_inicio = request.args.get("hora_inicio", "")
    hora_fin    = request.args.get("hora_fin", "")
    id_barrio   = request.args.get("id_barrio", "")
    canchas     = []

    if fecha and hora_inicio and hora_fin:
        if hora_fin <= hora_inicio:
            flash("La hora de fin debe ser posterior a la hora de inicio.", "warning")
        else:
            canchas = buscar_canchas_disponibles(fecha, hora_inicio, hora_fin,
                                                  id_barrio if id_barrio else None) or []

    return render_template("buscar.html", canchas=canchas, barrios=barrios)


@Web.route("/reservar", methods=["GET", "POST"])
def reservar():
    redir = login_requerido("jugador")
    if redir:
        return redir

    if request.method == "POST":
        try:
            dni           = session["cuenta"]["dni"]
            id_cancha     = int(request.form.get("id_cancha"))
            fecha         = request.form.get("fecha")
            hora_inicio   = request.form.get("hora_inicio")
            hora_fin      = request.form.get("hora_fin")
            id_medio_pago = int(request.form.get("id_medio_pago", 1))

            id_reserva = crear_reserva(dni, id_cancha, fecha, hora_inicio, hora_fin, id_medio_pago)
            if id_reserva:
                flash(f"¡Reserva confirmada! Número de reserva: #{id_reserva} ✅", "success")
                return redirect(url_for("mis_reservas"))
            else:
                flash("No se pudo crear la reserva. La cancha puede no estar disponible.", "danger")
        except Exception as e:
            flash(f"Error al reservar: {e}", "danger")

    # GET — formulario de confirmación
    return render_template("reservar.html",
        id_cancha   = request.args.get("id_cancha"),
        fecha       = request.args.get("fecha"),
        hora_inicio = request.args.get("hora_inicio"),
        hora_fin    = request.args.get("hora_fin"),
        complejo    = request.args.get("complejo"),
        cancha      = request.args.get("cancha"),
        precio      = request.args.get("precio"),
    )


@Web.route("/mis-reservas")
def mis_reservas():
    redir = login_requerido("jugador")
    if redir:
        return redir

    dni     = session["cuenta"]["dni"]
    reservas = listar_reservas_usuario(dni)
    return render_template("mis_reservas.html", reservas=reservas)


@Web.route("/cancelar-reserva/<int:id_reserva>", methods=["POST"])
def cancelar_reserva_route(id_reserva):
    redir = login_requerido("jugador")
    if redir:
        return redir

    try:
        cancelar_reserva(id_reserva)
        flash(f"Reserva #{id_reserva} cancelada correctamente.", "success")
    except Exception as e:
        flash(f"No se pudo cancelar la reserva: {e}", "danger")

    return redirect(url_for("mis_reservas"))


@Web.route("/lista-espera/<int:id_reserva>", methods=["POST"])
def lista_espera_route(id_reserva):
    redir = login_requerido("jugador")
    if redir:
        return redir

    dni = session["cuenta"]["dni"]
    try:
        resultado = anotarse_en_espera(id_reserva, dni)
        if resultado:
            flash("Te anotaste en la lista de espera. Te avisaremos si el turno queda libre. 🕐", "success")
        else:
            flash("No fue posible anotarte en la lista de espera.", "warning")
    except Exception as e:
        flash(f"Error: {e}", "danger")

    return redirect(url_for("mis_reservas"))

# ─────────────────────────────────────────
#  PERFIL JUGADOR
# ─────────────────────────────────────────
@Web.route("/mi-perfil", methods=["GET", "POST"])
def mi_perfil():
    redir = login_requerido("jugador")
    if redir:
        return redir

    if request.method == "POST":
        nombre   = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        email    = request.form.get("email", "").strip()
        telefono = request.form.get("telefono", "").strip()

        if not nombre or not apellido:
            flash("Nombre y apellido son obligatorios.", "danger")
        elif not validar_email(email):
            flash("El formato del email no es válido.", "danger")
        else:
            try:
                dni = session["cuenta"]["dni"]
                modificar_usuario(dni, nombre=nombre, apellido=apellido,
                                  email=email, telefono=telefono)
                # Actualizar sesión
                session["cuenta"].update({"nombre": nombre, "apellido": apellido,
                                          "email": email, "telefono": telefono})
                flash("¡Datos actualizados correctamente! ✓", "success")
            except Exception as e:
                flash(f"Error al actualizar: {e}", "danger")

    return render_template("mi_perfil.html")

# ─────────────────────────────────────────
#  PANEL COMPLEJO
# ─────────────────────────────────────────
@Web.route("/panel-complejo")
def panel_complejo():
    redir = login_requerido("complejo")
    if redir:
        return redir

    id_complejo = session["cuenta"]["id_complejo"]
    reservas    = listar_reservas_complejo(id_complejo)
    canchas     = listar_canchas_complejo(id_complejo)
    return render_template("panel_complejo.html", reservas=reservas, canchas=canchas)


@Web.route("/agregar-cancha", methods=["GET", "POST"])
def agregar_cancha():
    redir = login_requerido("complejo")
    if redir:
        return redir

    tipos = listar_tipos_cancha()

    if request.method == "POST":
        try:
            id_complejo     = session["cuenta"]["id_complejo"]
            id_tipo_cancha  = int(request.form.get("id_tipo_cancha"))
            nombre          = request.form.get("nombre", "").strip()
            techada         = request.form.get("techada") == "1"
            precio_por_hora = float(request.form.get("precio_por_hora", 0))

            if not nombre:
                flash("El nombre de la cancha es obligatorio.", "danger")
            elif precio_por_hora <= 0:
                flash("El precio por hora debe ser mayor a cero.", "danger")
            else:
                crear_cancha(id_complejo, id_tipo_cancha, nombre, techada, precio_por_hora)
                flash(f"Cancha '{nombre}' agregada con éxito. ✅", "success")
                return redirect(url_for("panel_complejo"))
        except Exception as e:
            flash(f"Error al agregar cancha: {e}", "danger")

    return render_template("agregar_cancha.html", tipos=tipos)


@Web.route("/editar-cancha/<int:id_cancha>", methods=["GET", "POST"])
def editar_cancha(id_cancha):
    redir = login_requerido("complejo")
    if redir:
        return redir

    id_complejo = session["cuenta"]["id_complejo"]
    canchas     = listar_canchas_complejo(id_complejo)
    cancha      = next((c for c in canchas if c["id_cancha"] == id_cancha), None)

    if not cancha:
        flash("Cancha no encontrada o no pertenece a tu complejo.", "danger")
        return redirect(url_for("panel_complejo"))

    if request.method == "POST":
        try:
            nombre          = request.form.get("nombre", "").strip() or None
            techada         = request.form.get("techada") == "1"
            precio_por_hora = float(request.form.get("precio_por_hora", 0)) or None
            disponible      = request.form.get("disponible") == "1"

            modificar_cancha(id_cancha, nombre=nombre, techada=techada,
                             precio_por_hora=precio_por_hora, disponible=disponible)
            flash("Cancha actualizada correctamente. ✓", "success")
            return redirect(url_for("panel_complejo"))
        except Exception as e:
            flash(f"Error al editar cancha: {e}", "danger")

    return render_template("editar_cancha.html", cancha=cancha)


@Web.route("/dar-baja-cancha/<int:id_cancha>", methods=["POST"])
def dar_baja_cancha(id_cancha):
    redir = login_requerido("complejo")
    if redir:
        return redir

    try:
        eliminar_cancha(id_cancha)
        flash("Cancha dada de baja correctamente.", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")

    return redirect(url_for("panel_complejo"))


@Web.route("/perfil-complejo", methods=["GET", "POST"])
def perfil_complejo():
    redir = login_requerido("complejo")
    if redir:
        return redir

    if request.method == "POST":
        nombre      = request.form.get("nombre", "").strip()
        direccion   = request.form.get("direccion", "").strip()
        telefono    = request.form.get("telefono", "").strip()
        descripcion = request.form.get("descripcion", "").strip()

        if not nombre:
            flash("El nombre es obligatorio.", "danger")
        else:
            try:
                id_complejo = session["cuenta"]["id_complejo"]
                modificar_complejo(id_complejo, nombre=nombre, direccion=direccion,
                                   telefono=telefono, descripcion=descripcion)
                session["cuenta"].update({"nombre": nombre})
                flash("Datos del complejo actualizados. ✓", "success")
            except Exception as e:
                flash(f"Error al actualizar: {e}", "danger")

    return render_template("perfil_complejo.html")


# ─────────────────────────────────────────
#  ERROR HANDLERS
# ─────────────────────────────────────────
@Web.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template("404.html"), 404

@Web.errorhandler(500)
def error_interno(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    Web.run(port=8080, debug=True)
