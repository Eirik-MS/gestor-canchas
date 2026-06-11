import bcrypt
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from conexion import conectar

# ─────────────────────────────────────────
#  ALTA
# ─────────────────────────────────────────
def crear_usuario(dni, nombre, apellido, email, telefono, password):
    """Registra un nuevo usuario. Encripta la password antes de guardarla."""
    conexion = conectar()
    cursor   = conexion.cursor()
    try:
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        sql = """
            INSERT INTO usuario (dni, nombre, apellido, email, telefono, password)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (dni, nombre, apellido, email, telefono, password_hash))
        conexion.commit()
        print(f"✓ Usuario {nombre} {apellido} creado correctamente.")
    except Exception as e:
        conexion.rollback()
        print(f"✗ Error al crear usuario: {e}")
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  CONSULTA — todos
# ─────────────────────────────────────────
def listar_usuarios():
    """Devuelve todos los usuarios activos (sin mostrar la password)."""
    conexion = conectar()
    cursor   = conexion.cursor(dictionary=True)   # devuelve dicts en lugar de tuplas
    try:
        cursor.execute("""
            SELECT dni, nombre, apellido, email, telefono, activo, fecha_alta
            FROM usuario
            WHERE fecha_baja IS NULL
            ORDER BY apellido, nombre
        """)
        usuarios = cursor.fetchall()
        for u in usuarios:
            print(u)
        return usuarios
    except Exception as e:
        print(f"✗ Error al listar usuarios: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  CONSULTA — uno por DNI
# ─────────────────────────────────────────
def obtener_usuario(dni):
    """Busca un usuario por DNI. Retorna el dict o None si no existe."""
    conexion = conectar()
    cursor   = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT dni, nombre, apellido, email, telefono, activo
            FROM usuario
            WHERE dni = %s AND fecha_baja IS NULL
        """, (dni,))
        usuario = cursor.fetchone()
        if not usuario:
            print(f"✗ No se encontró un usuario con DNI {dni}.")
        return usuario
    except Exception as e:
        print(f"✗ Error al buscar usuario: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  MODIFICACIÓN
# ─────────────────────────────────────────
def modificar_usuario(dni, nombre=None, apellido=None, email=None, telefono=None):
    """Actualiza los campos que se pasen. Los que queden en None no se tocan."""
    conexion = conectar()
    cursor   = conexion.cursor()
    try:
        # Construimos el SET dinámicamente solo con los campos que llegaron
        campos = []
        valores = []
        if nombre   is not None: campos.append("nombre = %s");   valores.append(nombre)
        if apellido is not None: campos.append("apellido = %s"); valores.append(apellido)
        if email    is not None: campos.append("email = %s");    valores.append(email)
        if telefono is not None: campos.append("telefono = %s"); valores.append(telefono)

        if not campos:
            print("✗ No se proporcionó ningún campo para modificar.")
            return

        valores.append(dni)
        sql = f"UPDATE usuario SET {', '.join(campos)} WHERE dni = %s AND fecha_baja IS NULL"
        cursor.execute(sql, tuple(valores))
        conexion.commit()

        if cursor.rowcount == 0:
            print(f"✗ No se encontró usuario con DNI {dni}.")
        else:
            print(f"✓ Usuario DNI {dni} actualizado correctamente.")
    except Exception as e:
        conexion.rollback()
        print(f"✗ Error al modificar usuario: {e}")
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  BAJA LÓGICA
# ─────────────────────────────────────────
def eliminar_usuario(dni):
    """Baja lógica: setea fecha_baja, no borra el registro."""
    conexion = conectar()
    cursor   = conexion.cursor()
    try:
        cursor.execute("""
            UPDATE usuario
            SET fecha_baja = NOW(), activo = FALSE
            WHERE dni = %s AND fecha_baja IS NULL
        """, (dni,))
        conexion.commit()

        if cursor.rowcount == 0:
            print(f"✗ No se encontró usuario activo con DNI {dni}.")
        else:
            print(f"✓ Usuario DNI {dni} dado de baja correctamente.")
    except Exception as e:
        conexion.rollback()
        print(f"✗ Error al dar de baja usuario: {e}")
    finally:
        cursor.close()
        conexion.close()

# ─────────────────────────────────────────
#  LOGIN — verifica password encriptada
# ─────────────────────────────────────────
def login_usuario(email, password):
    """
    Verifica email y password contra la BD.
    Retorna el usuario si es correcto, None si no.
    """
    conexion = conectar()
    cursor   = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT dni, nombre, apellido, email, telefono, password
            FROM usuario
            WHERE email = %s AND activo = TRUE AND fecha_baja IS NULL
        """, (email,))
        usuario = cursor.fetchone()

        if not usuario:
            print("✗ Email o password incorrectos.")
            return None

        # Verificamos la password contra el hash guardado
        if bcrypt.checkpw(password.encode("utf-8"), usuario["password"].encode("utf-8")):
            print(f"✓ Login exitoso. Bienvenido, {usuario['nombre']}.")
            usuario.pop("password")   # nunca devolvemos el hash al llamador
            return usuario
        else:
            print("✗ Email o password incorrectos.")
            return None
    except Exception as e:
        print(f"✗ Error en login: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()