from flask import Flask, render_template, request, redirect, url_for, session, flash

from backend.models.usuarios  import login_usuario
from backend.models.complejos import login_complejo
from backend.models.canchas   import buscar_canchas_disponibles

Web = Flask(__name__, template_folder="frontend")
## TODO: Fix session security 
## add a hashed secret loded from .env

@Web.route("/")
def home():
    return render_template("index.html")

@Web.route("/buscar")
def buscar():
    fecha       = request.args.get("fecha")
    hora_inicio = request.args.get("hora_inicio")
    hora_fin    = request.args.get("hora_fin")
    barrios     = request.args.get("barrios")
    canchas = []
    if fecha and hora_inicio and hora_fin and barrios:
        canchas = buscar_canchas_disponibles(fecha, hora_inicio, hora_fin, barrios) or []
        # si tu función soporta filtrar por barrio, pasale request.args.get("id_barrio")
    return render_template("buscar.html", canchas=canchas)

@Web.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        tipo     = request.form.get("tipo")
        email    = request.form.get("email")
        password = request.form.get("password")

        if tipo == "complejo":
            cuenta = login_complejo(email, password)
        else:
            cuenta = login_usuario(email, password)

        if cuenta:
            session["tipo"] = tipo
            session["cuenta"] = cuenta
            flash(f"Bienvenido, {cuenta['nombre']}.", "success")
            return redirect(url_for("home"))
        else:
            flash("Email o password incorrectos.", "danger")

    return render_template("login.html")

if __name__ == "__main__":
    Web.run(port=8080, debug=True)