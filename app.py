from functools import wraps
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from conexion import obtener_conexion


app = Flask(__name__)
app.secret_key = "gba_credomatic_clave_secreta_segura"


# =========================
# AUDITORÍA DESDE FLASK
# =========================

def registrar_auditoria(id_usuario, modulo, operacion, descripcion):
    conexion = obtener_conexion()

    if conexion is None:
        return

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO auditoria (id_usuario, modulo, operacion, descripcion)
                VALUES (%s, %s, %s, %s)
                """,
                (id_usuario, modulo, operacion, descripcion)
            )

        conexion.commit()

    except Exception as error:
        print("Error al registrar auditoría:", error)

    finally:
        conexion.close()


# =========================
# CONTEXTO DE AUDITORÍA PARA TRIGGERS
# Envía a PostgreSQL el usuario que está logueado.
# Los triggers usan este contexto para guardar id_usuario y usuario real.
# =========================

def establecer_contexto_auditoria(conexion):
    if "id_usuario" not in session:
        return

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('app.id_usuario', %s, true)",
                (str(session["id_usuario"]),)
            )

            cursor.execute(
                "SELECT set_config('app.usuario', %s, true)",
                (session["usuario"],)
            )

    except Exception as error:
        print("Error al establecer contexto de auditoría:", error)



# =========================
# USUARIOS BASE
# =========================

def crear_usuarios_base():
    conexion = obtener_conexion()

    if conexion is None:
        print("No hay conexión para crear usuarios base.")
        return

    usuarios_base = [
        {
            "rol": "ADMINISTRADOR",
            "nombre": "Administrador General",
            "usuario": "admin_banco",
            "correo": "admin@gbacredomatic.com.gt",
            "clave": "AdminBanco123"
        },
        {
            "rol": "CAJERO",
            "nombre": "Cajero Bancario",
            "usuario": "cajero_banco",
            "correo": "cajero@gbacredomatic.com.gt",
            "clave": "CajeroBanco123"
        },
        {
            "rol": "AUDITOR",
            "nombre": "Auditor Interno",
            "usuario": "auditor_banco",
            "correo": "auditor@gbacredomatic.com.gt",
            "clave": "AuditorBanco123"
        }
    ]

    try:
        with conexion.cursor() as cursor:
            for usuario_base in usuarios_base:
                cursor.execute(
                    """
                    SELECT id_rol
                    FROM roles
                    WHERE nombre_rol = %s
                    LIMIT 1
                    """,
                    (usuario_base["rol"],)
                )

                rol = cursor.fetchone()

                if not rol:
                    print(f"No existe el rol {usuario_base['rol']}.")
                    continue

                cursor.execute(
                    """
                    SELECT id_usuario
                    FROM usuarios
                    WHERE usuario = %s
                    LIMIT 1
                    """,
                    (usuario_base["usuario"],)
                )

                usuario_existente = cursor.fetchone()
                clave_hash = generate_password_hash(usuario_base["clave"])

                if usuario_existente:
                    cursor.execute(
                        """
                        UPDATE usuarios
                        SET id_rol = %s,
                            nombre_completo = %s,
                            correo = %s,
                            clave = %s,
                            estado = 'ACTIVO'
                        WHERE usuario = %s
                        """,
                        (
                            rol["id_rol"],
                            usuario_base["nombre"],
                            usuario_base["correo"],
                            clave_hash,
                            usuario_base["usuario"]
                        )
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO usuarios
                        (id_rol, nombre_completo, usuario, correo, clave, estado)
                        VALUES (%s, %s, %s, %s, %s, 'ACTIVO')
                        """,
                        (
                            rol["id_rol"],
                            usuario_base["nombre"],
                            usuario_base["usuario"],
                            usuario_base["correo"],
                            clave_hash
                        )
                    )

        conexion.commit()
        print("Usuarios base verificados correctamente.")

    except Exception as error:
        print("Error al crear usuarios base:", error)

    finally:
        conexion.close()


# =========================
# SEGURIDAD
# =========================

def login_requerido(funcion):
    @wraps(funcion)
    def decorador(*args, **kwargs):
        if "id_usuario" not in session:
            flash("Debe iniciar sesión para acceder al sistema.", "warning")
            return redirect(url_for("login"))

        return funcion(*args, **kwargs)

    return decorador


def rol_requerido(rol):
    def decorador_rol(funcion):
        @wraps(funcion)
        def decorador(*args, **kwargs):
            if "id_usuario" not in session:
                flash("Debe iniciar sesión para acceder al sistema.", "warning")
                return redirect(url_for("login"))

            if session.get("rol") != rol:
                flash("No tiene permisos para acceder a este módulo.", "danger")
                return redirect(url_for("login"))

            return funcion(*args, **kwargs)

        return decorador

    return decorador_rol


def redirigir_por_rol(rol):
    if rol == "ADMINISTRADOR":
        return redirect(url_for("panel_admin"))

    if rol == "CAJERO":
        return redirect(url_for("panel_cajero"))

    if rol == "AUDITOR":
        return redirect(url_for("panel_auditor"))

    return redirect(url_for("login"))


def validar_clave_admin(clave_confirmacion):
    conexion = obtener_conexion()

    if conexion is None:
        return False

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT clave
                FROM usuarios
                WHERE id_usuario = %s
                LIMIT 1
                """,
                (session["id_usuario"],)
            )

            administrador = cursor.fetchone()

            if not administrador:
                return False

            return check_password_hash(administrador["clave"], clave_confirmacion)

    except Exception as error:
        print("Error al validar contraseña de administrador:", error)
        return False

    finally:
        conexion.close()


# =========================
# RUTAS PÚBLICAS
# =========================

@app.route("/")
def inicio():
    return render_template("pgba.html")


@app.route("/pgba")
def pgba():
    return render_template("pgba.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET" and request.args.get("nueva_sesion") == "1":
        session.clear()

    elif request.method == "GET" and "id_usuario" in session:
        return redirigir_por_rol(session.get("rol"))

    if request.method == "POST":
        usuario_o_correo = request.form.get("usuario", "").strip()
        clave = request.form.get("clave", "").strip()

        if not usuario_o_correo or not clave:
            flash("Debe completar todos los campos.", "warning")
            return redirect(url_for("login"))

        conexion = obtener_conexion()

        if conexion is None:
            flash("No se pudo conectar con la base de datos.", "danger")
            return redirect(url_for("login"))

        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        u.id_usuario,
                        u.nombre_completo,
                        u.usuario,
                        u.correo,
                        u.clave,
                        u.estado,
                        r.nombre_rol
                    FROM usuarios u
                    INNER JOIN roles r ON u.id_rol = r.id_rol
                    WHERE u.usuario = %s OR u.correo = %s
                    LIMIT 1
                    """,
                    (usuario_o_correo, usuario_o_correo)
                )

                usuario = cursor.fetchone()

                if not usuario:
                    flash("Usuario, correo o contraseña incorrectos.", "danger")
                    return redirect(url_for("login"))

                if not check_password_hash(usuario["clave"], clave):
                    flash("Usuario, correo o contraseña incorrectos.", "danger")
                    return redirect(url_for("login"))

                if usuario["estado"] != "ACTIVO":
                    flash("El usuario se encuentra inactivo.", "danger")
                    return redirect(url_for("login"))

                session["id_usuario"] = usuario["id_usuario"]
                session["nombre_completo"] = usuario["nombre_completo"]
                session["usuario"] = usuario["usuario"]
                session["correo"] = usuario["correo"]
                session["rol"] = usuario["nombre_rol"]

                registrar_auditoria(
                    usuario["id_usuario"],
                    "Seguridad",
                    "LOGIN",
                    f"El usuario {usuario['usuario']} inició sesión con rol {usuario['nombre_rol']}."
                )

                return redirigir_por_rol(usuario["nombre_rol"])

        except Exception as error:
            print("Error en login:", error)
            flash("Ocurrió un error al iniciar sesión.", "danger")
            return redirect(url_for("login"))

        finally:
            conexion.close()

    return render_template("login.html")


@app.route("/recuperacion", methods=["GET", "POST"])
def recuperacion():
    if request.method == "POST":
        usuario_o_correo = request.form.get("usuario", "").strip()
        nueva_clave = request.form.get("nueva_clave", "").strip()
        confirmar_clave = request.form.get("confirmar_clave", "").strip()

        if not usuario_o_correo or not nueva_clave or not confirmar_clave:
            flash("Debe completar todos los campos.", "warning")
            return redirect(url_for("recuperacion"))

        if nueva_clave != confirmar_clave:
            flash("Las contraseñas no coinciden.", "warning")
            return redirect(url_for("recuperacion"))

        if len(nueva_clave) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "warning")
            return redirect(url_for("recuperacion"))

        conexion = obtener_conexion()

        if conexion is None:
            flash("No se pudo conectar con la base de datos.", "danger")
            return redirect(url_for("recuperacion"))

        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id_usuario, usuario
                    FROM usuarios
                    WHERE usuario = %s OR correo = %s
                    LIMIT 1
                    """,
                    (usuario_o_correo, usuario_o_correo)
                )

                usuario = cursor.fetchone()

                if not usuario:
                    flash("No se encontró un usuario con esos datos.", "danger")
                    return redirect(url_for("recuperacion"))

                clave_hash = generate_password_hash(nueva_clave)

                cursor.execute(
                    """
                    UPDATE usuarios
                    SET clave = %s
                    WHERE id_usuario = %s
                    """,
                    (clave_hash, usuario["id_usuario"])
                )

                conexion.commit()

                registrar_auditoria(
                    usuario["id_usuario"],
                    "Seguridad",
                    "RECUPERACION_CLAVE",
                    f"Se restableció la contraseña del usuario {usuario['usuario']}."
                )

                flash("Contraseña actualizada correctamente. Ya puede iniciar sesión.", "success")
                return redirect(url_for("login"))

        except Exception as error:
            print("Error en recuperación:", error)
            flash("Ocurrió un error al recuperar la contraseña.", "danger")
            return redirect(url_for("recuperacion"))

        finally:
            conexion.close()

    return render_template("recuperacion.html")
    


# =========================
# PANEL ADMINISTRADOR
# =========================

@app.route("/panel_admin")
@rol_requerido("ADMINISTRADOR")
def panel_admin():
    conexion = obtener_conexion()

    usuarios = []
    clientes = []
    cuentas_admin = []
    eventos = []
    transacciones_reporte = []
    resumen_tipos = []
    roles = []

    grafica_pastel_labels = []
    grafica_pastel_valores = []
    grafica_linea_fechas = []
    grafica_linea_cantidades = []

    total_usuarios = 0
    total_eventos = 0
    total_clientes = 0
    total_cuentas = 0
    total_transacciones = 0
    saldo_total = 0
    monto_total_transacciones = 0

    if conexion:
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        u.id_usuario,
                        u.usuario,
                        u.nombre_completo,
                        u.correo,
                        r.nombre_rol,
                        u.estado,
                        u.fecha_registro
                    FROM usuarios u
                    INNER JOIN roles r ON u.id_rol = r.id_rol
                    ORDER BY u.id_usuario DESC
                    """
                )
                usuarios = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT id_rol, nombre_rol
                    FROM roles
                    WHERE estado = 'ACTIVO'
                    ORDER BY nombre_rol
                    """
                )
                roles = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT
                        id_cliente,
                        dpi,
                        nombres,
                        apellidos,
                        telefono,
                        correo,
                        direccion,
                        estado
                    FROM clientes
                    ORDER BY id_cliente DESC
                    """
                )
                clientes = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT
                        c.id_cuenta,
                        c.numero_cuenta,
                        c.saldo,
                        c.estado,
                        c.fecha_apertura,
                        tc.nombre_tipo,
                        cl.dpi,
                        cl.nombres,
                        cl.apellidos,
                        cl.correo
                    FROM cuentas c
                    INNER JOIN clientes cl ON c.id_cliente = cl.id_cliente
                    INNER JOIN tipos_cuenta tc ON c.id_tipo_cuenta = tc.id_tipo_cuenta
                    ORDER BY c.id_cuenta DESC
                    """
                )
                cuentas_admin = cursor.fetchall()

                cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
                total_usuarios = cursor.fetchone()["total"]

                cursor.execute("SELECT COUNT(*) AS total FROM auditoria")
                total_eventos = cursor.fetchone()["total"]

                cursor.execute("SELECT COUNT(*) AS total FROM clientes")
                total_clientes = cursor.fetchone()["total"]

                cursor.execute("SELECT COUNT(*) AS total FROM cuentas")
                total_cuentas = cursor.fetchone()["total"]

                cursor.execute("SELECT COUNT(*) AS total FROM transacciones")
                total_transacciones = cursor.fetchone()["total"]

                cursor.execute("SELECT COALESCE(SUM(saldo), 0) AS total FROM cuentas")
                saldo_total = cursor.fetchone()["total"]

                cursor.execute("SELECT COALESCE(SUM(monto), 0) AS total FROM transacciones")
                monto_total_transacciones = cursor.fetchone()["total"]

                cursor.execute(
                    """
                    SELECT
                        a.fecha,
                        COALESCE(u.usuario, 'Sistema BD') AS usuario,
                        a.modulo,
                        a.operacion,
                        a.descripcion
                    FROM auditoria a
                    LEFT JOIN usuarios u ON a.id_usuario = u.id_usuario
                    ORDER BY a.fecha DESC
                    LIMIT 15
                    """
                )
                eventos = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT
                        codigo_transaccion,
                        tipo_transaccion,
                        id_cuenta_origen,
                        id_cuenta_destino,
                        monto,
                        estado,
                        descripcion,
                        fecha_transaccion
                    FROM transacciones
                    ORDER BY fecha_transaccion DESC
                    LIMIT 20
                    """
                )
                transacciones_reporte = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT
                        tipo_transaccion,
                        COUNT(*) AS cantidad,
                        COALESCE(SUM(monto), 0) AS monto_total
                    FROM transacciones
                    GROUP BY tipo_transaccion
                    ORDER BY cantidad DESC
                    """
                )
                resumen_tipos_raw = cursor.fetchall()

                total_resumen = sum(item["cantidad"] for item in resumen_tipos_raw)

                for item in resumen_tipos_raw:
                    porcentaje = 0

                    if total_resumen > 0:
                        porcentaje = round((item["cantidad"] / total_resumen) * 100, 2)

                    resumen_tipos.append({
                        "tipo_transaccion": item["tipo_transaccion"],
                        "cantidad": item["cantidad"],
                        "monto_total": item["monto_total"],
                        "porcentaje": porcentaje
                    })

                    grafica_pastel_labels.append(item["tipo_transaccion"])
                    grafica_pastel_valores.append(item["cantidad"])

                cursor.execute(
                    """
                    SELECT
                        fecha,
                        cantidad
                    FROM (
                        SELECT
                            DATE(fecha_transaccion) AS fecha,
                            COUNT(*) AS cantidad
                        FROM transacciones
                        GROUP BY DATE(fecha_transaccion)
                        ORDER BY fecha DESC
                        LIMIT 7
                    ) datos
                    ORDER BY fecha ASC
                    """
                )
                datos_linea = cursor.fetchall()

                for item in datos_linea:
                    grafica_linea_fechas.append(str(item["fecha"]))
                    grafica_linea_cantidades.append(item["cantidad"])

        except Exception as error:
            print("Error al cargar panel admin:", error)
            flash("No se pudieron cargar los datos del panel administrador.", "danger")

        finally:
            conexion.close()

    return render_template(
        "panel_admin.html",
        usuarios=usuarios,
        roles=roles,
        clientes=clientes,
        cuentas_admin=cuentas_admin,
        eventos=eventos,
        transacciones_reporte=transacciones_reporte,
        resumen_tipos=resumen_tipos,
        total_usuarios=total_usuarios,
        total_eventos=total_eventos,
        total_clientes=total_clientes,
        total_cuentas=total_cuentas,
        total_transacciones=total_transacciones,
        saldo_total=saldo_total,
        monto_total_transacciones=monto_total_transacciones,
        grafica_pastel_labels=grafica_pastel_labels,
        grafica_pastel_valores=grafica_pastel_valores,
        grafica_linea_fechas=grafica_linea_fechas,
        grafica_linea_cantidades=grafica_linea_cantidades
    )


@app.route("/admin/usuarios/crear", methods=["POST"])
@rol_requerido("ADMINISTRADOR")
def crear_usuario_admin():
    nombre_completo = request.form.get("nombre_completo", "").strip()
    usuario = request.form.get("usuario", "").strip()
    correo = request.form.get("correo", "").strip()
    id_rol = request.form.get("id_rol", "").strip()
    clave = request.form.get("clave", "").strip()
    confirmar_clave = request.form.get("confirmar_clave", "").strip()

    if not nombre_completo or not usuario or not correo or not id_rol or not clave or not confirmar_clave:
        flash("Debe completar todos los campos del usuario.", "warning")
        return redirect(url_for("panel_admin", seccion="usuarios"))

    if clave != confirmar_clave:
        flash("Las contraseñas no coinciden.", "warning")
        return redirect(url_for("panel_admin", seccion="usuarios"))

    if len(clave) < 6:
        flash("La contraseña debe tener al menos 6 caracteres.", "warning")
        return redirect(url_for("panel_admin", seccion="usuarios"))

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("panel_admin", seccion="usuarios"))

    establecer_contexto_auditoria(conexion)

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id_usuario
                FROM usuarios
                WHERE usuario = %s OR correo = %s
                LIMIT 1
                """,
                (usuario, correo)
            )

            usuario_existente = cursor.fetchone()

            if usuario_existente:
                flash("Ya existe un usuario con ese nombre de usuario o correo.", "warning")
                return redirect(url_for("panel_admin", seccion="usuarios"))

            clave_hash = generate_password_hash(clave)

            cursor.execute(
                """
                INSERT INTO usuarios
                (id_rol, nombre_completo, usuario, correo, clave, estado)
                VALUES (%s, %s, %s, %s, %s, 'ACTIVO')
                """,
                (id_rol, nombre_completo, usuario, correo, clave_hash)
            )

        conexion.commit()
        flash("Usuario interno registrado correctamente.", "success")

    except Exception as error:
        conexion.rollback()
        print("Error al crear usuario desde panel admin:", error)
        flash("No se pudo registrar el usuario interno.", "danger")

    finally:
        conexion.close()

    return redirect(url_for("panel_admin", seccion="usuarios"))

# =========================
# ACTIVAR / INACTIVAR USUARIOS, CLIENTES Y CUENTAS
# =========================

@app.route("/admin/usuarios/inactivar/<int:id_usuario>", methods=["POST"])
@rol_requerido("ADMINISTRADOR")
def inactivar_usuario_admin(id_usuario):
    clave_confirmacion = request.form.get("clave_confirmacion", "").strip()

    if not clave_confirmacion:
        flash("Debe ingresar su contraseña para confirmar la inactivación.", "warning")
        return redirect(url_for("panel_admin", seccion="usuarios"))

    if not validar_clave_admin(clave_confirmacion):
        flash("La contraseña de confirmación es incorrecta.", "danger")
        return redirect(url_for("panel_admin", seccion="usuarios"))

    if id_usuario == session.get("id_usuario"):
        flash("No puede inactivar su propio usuario.", "warning")
        return redirect(url_for("panel_admin", seccion="usuarios"))

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("panel_admin", seccion="usuarios"))

    establecer_contexto_auditoria(conexion)

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT usuario, estado
                FROM usuarios
                WHERE id_usuario = %s
                FOR UPDATE
                """,
                (id_usuario,)
            )

            usuario = cursor.fetchone()

            if not usuario:
                flash("El usuario seleccionado no existe.", "danger")
                return redirect(url_for("panel_admin", seccion="usuarios"))

            if usuario["estado"] == "INACTIVO":
                flash("El usuario ya se encuentra inactivo.", "warning")
                return redirect(url_for("panel_admin", seccion="usuarios"))

            cursor.execute(
                """
                UPDATE usuarios
                SET estado = 'INACTIVO'
                WHERE id_usuario = %s
                """,
                (id_usuario,)
            )

        conexion.commit()
        flash("Usuario inactivado correctamente.", "success")

    except Exception as error:
        conexion.rollback()
        print("Error al inactivar usuario:", error)
        flash("No se pudo inactivar el usuario.", "danger")

    finally:
        conexion.close()

    return redirect(url_for("panel_admin", seccion="usuarios"))


@app.route("/admin/usuarios/activar/<int:id_usuario>", methods=["POST"])
@rol_requerido("ADMINISTRADOR")
def activar_usuario_admin(id_usuario):
    clave_confirmacion = request.form.get("clave_confirmacion", "").strip()

    if not clave_confirmacion:
        flash("Debe ingresar su contraseña para confirmar la activación.", "warning")
        return redirect(url_for("panel_admin", seccion="usuarios"))

    if not validar_clave_admin(clave_confirmacion):
        flash("La contraseña de confirmación es incorrecta.", "danger")
        return redirect(url_for("panel_admin", seccion="usuarios"))

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("panel_admin", seccion="usuarios"))

    establecer_contexto_auditoria(conexion)

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT usuario, estado
                FROM usuarios
                WHERE id_usuario = %s
                FOR UPDATE
                """,
                (id_usuario,)
            )

            usuario = cursor.fetchone()

            if not usuario:
                flash("El usuario seleccionado no existe.", "danger")
                return redirect(url_for("panel_admin", seccion="usuarios"))

            if usuario["estado"] == "ACTIVO":
                flash("El usuario ya se encuentra activo.", "warning")
                return redirect(url_for("panel_admin", seccion="usuarios"))

            cursor.execute(
                """
                UPDATE usuarios
                SET estado = 'ACTIVO'
                WHERE id_usuario = %s
                """,
                (id_usuario,)
            )

        conexion.commit()
        flash("Usuario activado correctamente.", "success")

    except Exception as error:
        conexion.rollback()
        print("Error al activar usuario:", error)
        flash("No se pudo activar el usuario.", "danger")

    finally:
        conexion.close()

    return redirect(url_for("panel_admin", seccion="usuarios"))


@app.route("/admin/clientes/inactivar/<int:id_cliente>", methods=["POST"])
@rol_requerido("ADMINISTRADOR")
def inactivar_cliente_admin(id_cliente):
    clave_confirmacion = request.form.get("clave_confirmacion", "").strip()

    if not clave_confirmacion:
        flash("Debe ingresar su contraseña para confirmar la inactivación.", "warning")
        return redirect(url_for("panel_admin", seccion="clientes"))

    if not validar_clave_admin(clave_confirmacion):
        flash("La contraseña de confirmación es incorrecta.", "danger")
        return redirect(url_for("panel_admin", seccion="clientes"))

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("panel_admin", seccion="clientes"))

    establecer_contexto_auditoria(conexion)

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id_cliente, dpi, nombres, apellidos, estado
                FROM clientes
                WHERE id_cliente = %s
                FOR UPDATE
                """,
                (id_cliente,)
            )

            cliente = cursor.fetchone()

            if not cliente:
                flash("El cliente seleccionado no existe.", "danger")
                return redirect(url_for("panel_admin", seccion="clientes"))

            if cliente["estado"] == "INACTIVO":
                flash("El cliente ya se encuentra inactivo.", "warning")
                return redirect(url_for("panel_admin", seccion="clientes"))

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM cuentas
                WHERE id_cliente = %s
                  AND estado IN ('ACTIVA', 'ACTIVO')
                """,
                (id_cliente,)
            )

            cuentas_activas = cursor.fetchone()["total"]

            if cuentas_activas > 0:
                flash("No se puede inactivar el cliente porque tiene cuentas activas.", "warning")
                return redirect(url_for("panel_admin", seccion="clientes"))

            cursor.execute(
                """
                UPDATE clientes
                SET estado = 'INACTIVO'
                WHERE id_cliente = %s
                """,
                (id_cliente,)
            )

        conexion.commit()
        flash("Cliente inactivado correctamente.", "success")

    except Exception as error:
        conexion.rollback()
        print("Error al inactivar cliente:", error)
        flash("No se pudo inactivar el cliente.", "danger")

    finally:
        conexion.close()

    return redirect(url_for("panel_admin", seccion="clientes"))


@app.route("/admin/clientes/activar/<int:id_cliente>", methods=["POST"])
@rol_requerido("ADMINISTRADOR")
def activar_cliente_admin(id_cliente):
    clave_confirmacion = request.form.get("clave_confirmacion", "").strip()

    if not clave_confirmacion:
        flash("Debe ingresar su contraseña para confirmar la activación.", "warning")
        return redirect(url_for("panel_admin", seccion="clientes"))

    if not validar_clave_admin(clave_confirmacion):
        flash("La contraseña de confirmación es incorrecta.", "danger")
        return redirect(url_for("panel_admin", seccion="clientes"))

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("panel_admin", seccion="clientes"))

    establecer_contexto_auditoria(conexion)

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id_cliente, dpi, nombres, apellidos, estado
                FROM clientes
                WHERE id_cliente = %s
                FOR UPDATE
                """,
                (id_cliente,)
            )

            cliente = cursor.fetchone()

            if not cliente:
                flash("El cliente seleccionado no existe.", "danger")
                return redirect(url_for("panel_admin", seccion="clientes"))

            if cliente["estado"] == "ACTIVO":
                flash("El cliente ya se encuentra activo.", "warning")
                return redirect(url_for("panel_admin", seccion="clientes"))

            cursor.execute(
                """
                UPDATE clientes
                SET estado = 'ACTIVO'
                WHERE id_cliente = %s
                """,
                (id_cliente,)
            )

        conexion.commit()
        flash("Cliente activado correctamente.", "success")

    except Exception as error:
        conexion.rollback()
        print("Error al activar cliente:", error)
        flash("No se pudo activar el cliente.", "danger")

    finally:
        conexion.close()

    return redirect(url_for("panel_admin", seccion="clientes"))


@app.route("/admin/cuentas/inactivar/<int:id_cuenta>", methods=["POST"])
@rol_requerido("ADMINISTRADOR")
def inactivar_cuenta_admin(id_cuenta):
    clave_confirmacion = request.form.get("clave_confirmacion", "").strip()

    if not clave_confirmacion:
        flash("Debe ingresar su contraseña para confirmar la inactivación.", "warning")
        return redirect(url_for("panel_admin", seccion="cuentas"))

    if not validar_clave_admin(clave_confirmacion):
        flash("La contraseña de confirmación es incorrecta.", "danger")
        return redirect(url_for("panel_admin", seccion="cuentas"))

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("panel_admin", seccion="cuentas"))

    establecer_contexto_auditoria(conexion)

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id_cuenta, numero_cuenta, saldo, estado
                FROM cuentas
                WHERE id_cuenta = %s
                FOR UPDATE
                """,
                (id_cuenta,)
            )

            cuenta = cursor.fetchone()

            if not cuenta:
                flash("La cuenta seleccionada no existe.", "danger")
                return redirect(url_for("panel_admin", seccion="cuentas"))

            if cuenta["estado"] in ("INACTIVA", "INACTIVO"):
                flash("La cuenta ya se encuentra inactiva.", "warning")
                return redirect(url_for("panel_admin", seccion="cuentas"))

            if cuenta["saldo"] > 0:
                flash("No se puede inactivar la cuenta porque aún tiene saldo disponible.", "warning")
                return redirect(url_for("panel_admin", seccion="cuentas"))

            cursor.execute(
                """
                UPDATE cuentas
                SET estado = 'INACTIVA'
                WHERE id_cuenta = %s
                """,
                (id_cuenta,)
            )

        conexion.commit()
        flash("Cuenta inactivada correctamente.", "success")

    except Exception as error:
        conexion.rollback()
        print("Error al inactivar cuenta:", error)
        flash("No se pudo inactivar la cuenta.", "danger")

    finally:
        conexion.close()

    return redirect(url_for("panel_admin", seccion="cuentas"))


@app.route("/admin/cuentas/activar/<int:id_cuenta>", methods=["POST"])
@rol_requerido("ADMINISTRADOR")
def activar_cuenta_admin(id_cuenta):
    clave_confirmacion = request.form.get("clave_confirmacion", "").strip()

    if not clave_confirmacion:
        flash("Debe ingresar su contraseña para confirmar la activación.", "warning")
        return redirect(url_for("panel_admin", seccion="cuentas"))

    if not validar_clave_admin(clave_confirmacion):
        flash("La contraseña de confirmación es incorrecta.", "danger")
        return redirect(url_for("panel_admin", seccion="cuentas"))

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("panel_admin", seccion="cuentas"))

    establecer_contexto_auditoria(conexion)

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id_cuenta, numero_cuenta, estado
                FROM cuentas
                WHERE id_cuenta = %s
                FOR UPDATE
                """,
                (id_cuenta,)
            )

            cuenta = cursor.fetchone()

            if not cuenta:
                flash("La cuenta seleccionada no existe.", "danger")
                return redirect(url_for("panel_admin", seccion="cuentas"))

            if cuenta["estado"] in ("ACTIVA", "ACTIVO"):
                flash("La cuenta ya se encuentra activa.", "warning")
                return redirect(url_for("panel_admin", seccion="cuentas"))

            cursor.execute(
                """
                UPDATE cuentas
                SET estado = 'ACTIVA'
                WHERE id_cuenta = %s
                """,
                (id_cuenta,)
            )

        conexion.commit()
        flash("Cuenta activada correctamente.", "success")

    except Exception as error:
        conexion.rollback()
        print("Error al activar cuenta:", error)
        flash("No se pudo activar la cuenta.", "danger")

    finally:
        conexion.close()

    return redirect(url_for("panel_admin", seccion="cuentas"))

 
# =========================
# PANEL CAJERO
# =========================

@app.route("/panel_cajero")
@rol_requerido("CAJERO")
def panel_cajero():
    conexion = obtener_conexion()

    clientes = []
    cuentas = []
    tipos_cuenta = []
    servicios = []
    transacciones = []
    pagos = []

    total_clientes = 0
    total_cuentas = 0
    total_transacciones = 0
    saldo_total = 0

    if conexion:
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM clientes
                    ORDER BY id_cliente DESC
                    """
                )
                clientes = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT
                        c.id_cuenta,
                        c.numero_cuenta,
                        c.saldo,
                        c.estado,
                        tc.nombre_tipo,
                        cl.nombres,
                        cl.apellidos
                    FROM cuentas c
                    INNER JOIN clientes cl ON c.id_cliente = cl.id_cliente
                    INNER JOIN tipos_cuenta tc ON c.id_tipo_cuenta = tc.id_tipo_cuenta
                    ORDER BY c.id_cuenta DESC
                    """
                )
                cuentas = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT id_tipo_cuenta, nombre_tipo
                    FROM tipos_cuenta
                    WHERE estado = 'ACTIVO'
                    ORDER BY nombre_tipo
                    """
                )
                tipos_cuenta = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT id_servicio, nombre_servicio
                    FROM servicios
                    WHERE estado = 'ACTIVO'
                    ORDER BY nombre_servicio
                    """
                )
                servicios = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT *
                    FROM transacciones
                    ORDER BY fecha_transaccion DESC
                    LIMIT 30
                    """
                )
                transacciones = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT
                        p.codigo_pago,
                        c.numero_cuenta,
                        s.nombre_servicio,
                        p.referencia,
                        p.monto,
                        p.estado,
                        p.fecha_pago
                    FROM pagos p
                    INNER JOIN cuentas c ON p.id_cuenta = c.id_cuenta
                    INNER JOIN servicios s ON p.id_servicio = s.id_servicio
                    ORDER BY p.fecha_pago DESC
                    LIMIT 20
                    """
                )
                pagos = cursor.fetchall()

                cursor.execute("SELECT COUNT(*) AS total FROM clientes")
                total_clientes = cursor.fetchone()["total"]

                cursor.execute("SELECT COUNT(*) AS total FROM cuentas")
                total_cuentas = cursor.fetchone()["total"]

                cursor.execute("SELECT COUNT(*) AS total FROM transacciones")
                total_transacciones = cursor.fetchone()["total"]

                cursor.execute("SELECT COALESCE(SUM(saldo), 0) AS total FROM cuentas")
                saldo_total = cursor.fetchone()["total"]

        except Exception as error:
            print("Error al cargar panel cajero:", error)
            flash("No se pudieron cargar los datos del cajero.", "danger")

        finally:
            conexion.close()

    return render_template(
        "panel_cajero.html",
        clientes=clientes,
        cuentas=cuentas,
        tipos_cuenta=tipos_cuenta,
        servicios=servicios,
        transacciones=transacciones,
        pagos=pagos,
        total_clientes=total_clientes,
        total_cuentas=total_cuentas,
        total_transacciones=total_transacciones,
        saldo_total=saldo_total
    )


@app.route("/clientes/guardar", methods=["POST"])
@rol_requerido("CAJERO")
def guardar_cliente():
    dpi = request.form.get("dpi", "").strip()
    nombres = request.form.get("nombres", "").strip()
    apellidos = request.form.get("apellidos", "").strip()
    telefono = request.form.get("telefono", "").strip()
    correo = request.form.get("correo", "").strip()
    direccion = request.form.get("direccion", "").strip()

    if not dpi or not nombres or not apellidos:
        flash("DPI, nombres y apellidos son obligatorios.", "warning")
        return redirect(url_for("panel_cajero", seccion="clientes"))

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("panel_cajero", seccion="clientes"))

    establecer_contexto_auditoria(conexion)

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO clientes
                (dpi, nombres, apellidos, telefono, correo, direccion, estado)
                VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVO')
                """,
                (dpi, nombres, apellidos, telefono, correo, direccion)
            )

        conexion.commit()
        flash("Cliente registrado correctamente.", "success")

    except Exception as error:
        conexion.rollback()
        print("Error al guardar cliente:", error)
        flash("No se pudo registrar el cliente. Verifique que el DPI no esté repetido.", "danger")

    finally:
        conexion.close()

    return redirect(url_for("panel_cajero", seccion="clientes"))


@app.route("/cuentas/guardar", methods=["POST"])
@rol_requerido("CAJERO")
def guardar_cuenta():
    id_cliente = request.form.get("id_cliente", "").strip()
    id_tipo_cuenta = request.form.get("id_tipo_cuenta", "").strip()
    saldo_inicial = request.form.get("saldo_inicial", "0").strip()

    if not id_cliente or not id_tipo_cuenta:
        flash("Debe seleccionar cliente y tipo de cuenta.", "warning")
        return redirect(url_for("panel_cajero", seccion="cuentas"))

    try:
        saldo_inicial = float(saldo_inicial)

        if saldo_inicial < 0:
            flash("El saldo inicial no puede ser negativo.", "warning")
            return redirect(url_for("panel_cajero", seccion="cuentas"))

    except ValueError:
        flash("El saldo inicial no es válido.", "warning")
        return redirect(url_for("panel_cajero", seccion="cuentas"))

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("panel_cajero", seccion="cuentas"))

    establecer_contexto_auditoria(conexion)

    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(id_cuenta), 0) + 1 AS siguiente FROM cuentas")
            siguiente = cursor.fetchone()["siguiente"]
            numero_cuenta = f"100001{str(siguiente).zfill(4)}"

            cursor.execute(
                """
                INSERT INTO cuentas
                (id_cliente, id_tipo_cuenta, numero_cuenta, saldo, estado)
                VALUES (%s, %s, %s, %s, 'ACTIVA')
                """,
                (id_cliente, id_tipo_cuenta, numero_cuenta, saldo_inicial)
            )

        conexion.commit()
        flash("Cuenta creada correctamente.", "success")

    except Exception as error:
        conexion.rollback()
        print("Error al crear cuenta:", error)
        flash("No se pudo crear la cuenta.", "danger")

    finally:
        conexion.close()

    return redirect(url_for("panel_cajero", seccion="cuentas"))


@app.route("/transacciones/procesar", methods=["POST"])
@rol_requerido("CAJERO")
def procesar_transaccion():
    tipo = request.form.get("tipo_transaccion", "").strip()
    id_cuenta_origen = request.form.get("id_cuenta_origen") or None
    id_cuenta_destino = request.form.get("id_cuenta_destino") or None
    monto = request.form.get("monto", "").strip()

    try:
        monto = float(monto)

        if monto <= 0:
            flash("El monto debe ser mayor que cero.", "warning")
            return redirect(url_for("panel_cajero", seccion="transacciones"))

    except ValueError:
        flash("El monto no es válido.", "warning")
        return redirect(url_for("panel_cajero", seccion="transacciones"))

    codigo = "TRX-" + datetime.now().strftime("%Y%m%d%H%M%S%f")
    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("panel_cajero", seccion="transacciones"))

    establecer_contexto_auditoria(conexion)

    try:
        with conexion.cursor() as cursor:
            if tipo == "DEPOSITO":
                if not id_cuenta_destino:
                    flash("Para depósito debe seleccionar cuenta destino.", "warning")
                    return redirect(url_for("panel_cajero", seccion="transacciones"))

                cursor.execute(
                    """
                    UPDATE cuentas
                    SET saldo = saldo + %s
                    WHERE id_cuenta = %s
                    """,
                    (monto, id_cuenta_destino)
                )

                cursor.execute(
                    """
                    INSERT INTO transacciones
                    (codigo_transaccion, tipo_transaccion, id_cuenta_origen, id_cuenta_destino, monto, estado, descripcion)
                    VALUES (%s, %s, NULL, %s, %s, 'COMPLETADA', %s)
                    """,
                    (codigo, tipo, id_cuenta_destino, monto, "Depósito realizado en ventanilla.")
                )

            elif tipo == "RETIRO":
                if not id_cuenta_origen:
                    flash("Para retiro debe seleccionar cuenta origen.", "warning")
                    return redirect(url_for("panel_cajero", seccion="transacciones"))

                cursor.execute(
                    """
                    SELECT saldo
                    FROM cuentas
                    WHERE id_cuenta = %s
                    FOR UPDATE
                    """,
                    (id_cuenta_origen,)
                )

                cuenta = cursor.fetchone()

                if not cuenta or cuenta["saldo"] < monto:
                    flash("Fondos insuficientes.", "danger")
                    return redirect(url_for("panel_cajero", seccion="transacciones"))

                cursor.execute(
                    """
                    UPDATE cuentas
                    SET saldo = saldo - %s
                    WHERE id_cuenta = %s
                    """,
                    (monto, id_cuenta_origen)
                )

                cursor.execute(
                    """
                    INSERT INTO transacciones
                    (codigo_transaccion, tipo_transaccion, id_cuenta_origen, id_cuenta_destino, monto, estado, descripcion)
                    VALUES (%s, %s, %s, NULL, %s, 'COMPLETADA', %s)
                    """,
                    (codigo, tipo, id_cuenta_origen, monto, "Retiro realizado en ventanilla.")
                )

            elif tipo == "TRANSFERENCIA":
                if not id_cuenta_origen or not id_cuenta_destino:
                    flash("Debe seleccionar cuenta origen y destino.", "warning")
                    return redirect(url_for("panel_cajero", seccion="transacciones"))

                if id_cuenta_origen == id_cuenta_destino:
                    flash("La cuenta origen y destino no pueden ser la misma.", "warning")
                    return redirect(url_for("panel_cajero", seccion="transacciones"))

                cursor.execute(
                    """
                    SELECT saldo
                    FROM cuentas
                    WHERE id_cuenta = %s
                    FOR UPDATE
                    """,
                    (id_cuenta_origen,)
                )

                cuenta_origen = cursor.fetchone()

                if not cuenta_origen or cuenta_origen["saldo"] < monto:
                    flash("Fondos insuficientes.", "danger")
                    return redirect(url_for("panel_cajero", seccion="transacciones"))

                cursor.execute(
                    """
                    UPDATE cuentas
                    SET saldo = saldo - %s
                    WHERE id_cuenta = %s
                    """,
                    (monto, id_cuenta_origen)
                )

                cursor.execute(
                    """
                    UPDATE cuentas
                    SET saldo = saldo + %s
                    WHERE id_cuenta = %s
                    """,
                    (monto, id_cuenta_destino)
                )

                cursor.execute(
                    """
                    INSERT INTO transacciones
                    (codigo_transaccion, tipo_transaccion, id_cuenta_origen, id_cuenta_destino, monto, estado, descripcion)
                    VALUES (%s, %s, %s, %s, %s, 'COMPLETADA', %s)
                    """,
                    (codigo, tipo, id_cuenta_origen, id_cuenta_destino, monto, "Transferencia realizada en ventanilla.")
                )

            else:
                flash("Tipo de transacción no válido.", "danger")
                return redirect(url_for("panel_cajero", seccion="transacciones"))

        conexion.commit()
        flash("Transacción procesada correctamente.", "success")

    except Exception as error:
        conexion.rollback()
        print("Error al procesar transacción:", error)
        flash("No se pudo procesar la transacción.", "danger")

    finally:
        conexion.close()

    return redirect(url_for("panel_cajero", seccion="transacciones"))


@app.route("/transacciones/anular", methods=["POST"])
@rol_requerido("CAJERO")
def anular_transaccion():
    id_transaccion = request.form.get("id_transaccion", "").strip()

    if not id_transaccion:
        flash("Debe seleccionar una transacción para anular.", "warning")
        return redirect(url_for("panel_cajero", seccion="transacciones"))

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("panel_cajero", seccion="transacciones"))

    establecer_contexto_auditoria(conexion)

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id_transaccion,
                    codigo_transaccion,
                    tipo_transaccion,
                    id_cuenta_origen,
                    id_cuenta_destino,
                    monto,
                    estado
                FROM transacciones
                WHERE id_transaccion = %s
                FOR UPDATE
                """,
                (id_transaccion,)
            )

            transaccion = cursor.fetchone()

            if not transaccion:
                flash("La transacción seleccionada no existe.", "danger")
                return redirect(url_for("panel_cajero", seccion="transacciones"))

            if transaccion["estado"] != "COMPLETADA":
                flash("Solo se pueden anular transacciones completadas.", "warning")
                return redirect(url_for("panel_cajero", seccion="transacciones"))

            tipo = transaccion["tipo_transaccion"]
            monto = transaccion["monto"]
            id_cuenta_origen = transaccion["id_cuenta_origen"]
            id_cuenta_destino = transaccion["id_cuenta_destino"]

            if tipo == "DEPOSITO":
                cursor.execute(
                    """
                    SELECT saldo
                    FROM cuentas
                    WHERE id_cuenta = %s
                    FOR UPDATE
                    """,
                    (id_cuenta_destino,)
                )

                cuenta_destino = cursor.fetchone()

                if not cuenta_destino or cuenta_destino["saldo"] < monto:
                    flash("No se puede anular el depósito porque la cuenta no tiene saldo suficiente para revertirlo.", "danger")
                    return redirect(url_for("panel_cajero", seccion="transacciones"))

                cursor.execute(
                    """
                    UPDATE cuentas
                    SET saldo = saldo - %s
                    WHERE id_cuenta = %s
                    """,
                    (monto, id_cuenta_destino)
                )

            elif tipo == "RETIRO":
                cursor.execute(
                    """
                    UPDATE cuentas
                    SET saldo = saldo + %s
                    WHERE id_cuenta = %s
                    """,
                    (monto, id_cuenta_origen)
                )

            elif tipo == "TRANSFERENCIA":
                cursor.execute(
                    """
                    SELECT saldo
                    FROM cuentas
                    WHERE id_cuenta = %s
                    FOR UPDATE
                    """,
                    (id_cuenta_destino,)
                )

                cuenta_destino = cursor.fetchone()

                if not cuenta_destino or cuenta_destino["saldo"] < monto:
                    flash("No se puede anular la transferencia porque la cuenta destino no tiene saldo suficiente.", "danger")
                    return redirect(url_for("panel_cajero", seccion="transacciones"))

                cursor.execute(
                    """
                    UPDATE cuentas
                    SET saldo = saldo - %s
                    WHERE id_cuenta = %s
                    """,
                    (monto, id_cuenta_destino)
                )

                cursor.execute(
                    """
                    UPDATE cuentas
                    SET saldo = saldo + %s
                    WHERE id_cuenta = %s
                    """,
                    (monto, id_cuenta_origen)
                )

            elif tipo == "PAGO_SERVICIO":
                cursor.execute(
                    """
                    UPDATE cuentas
                    SET saldo = saldo + %s
                    WHERE id_cuenta = %s
                    """,
                    (monto, id_cuenta_origen)
                )

            else:
                flash("Este tipo de transacción no se puede anular desde este módulo.", "warning")
                return redirect(url_for("panel_cajero", seccion="transacciones"))

            cursor.execute(
                """
                UPDATE transacciones
                SET estado = 'ANULADA',
                    descripcion = CONCAT(descripcion, ' | Transacción anulada y revertida.')
                WHERE id_transaccion = %s
                """,
                (id_transaccion,)
            )

        conexion.commit()
        flash("Transacción anulada y revertida correctamente.", "success")

    except Exception as error:
        conexion.rollback()
        print("Error al anular transacción:", error)
        flash("No se pudo anular la transacción.", "danger")

    finally:
        conexion.close()

    return redirect(url_for("panel_cajero", seccion="transacciones"))


@app.route("/pagos/procesar", methods=["POST"])
@rol_requerido("CAJERO")
def procesar_pago():
    id_cuenta = request.form.get("id_cuenta", "").strip()
    id_servicio = request.form.get("id_servicio", "").strip()
    referencia = request.form.get("referencia", "").strip()
    monto = request.form.get("monto", "").strip()

    if not id_cuenta or not id_servicio or not referencia or not monto:
        flash("Debe completar todos los campos del pago.", "warning")
        return redirect(url_for("panel_cajero", seccion="pagos"))

    try:
        monto = float(monto)

        if monto <= 0:
            flash("El monto debe ser mayor que cero.", "warning")
            return redirect(url_for("panel_cajero", seccion="pagos"))

    except ValueError:
        flash("El monto no es válido.", "warning")
        return redirect(url_for("panel_cajero", seccion="pagos"))

    codigo_pago = "PAG-" + datetime.now().strftime("%Y%m%d%H%M%S%f")
    codigo_trx = "TRX-" + datetime.now().strftime("%Y%m%d%H%M%S%f")

    conexion = obtener_conexion()

    if conexion is None:
        flash("No se pudo conectar con la base de datos.", "danger")
        return redirect(url_for("panel_cajero", seccion="pagos"))

    establecer_contexto_auditoria(conexion)

    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT saldo
                FROM cuentas
                WHERE id_cuenta = %s
                FOR UPDATE
                """,
                (id_cuenta,)
            )

            cuenta = cursor.fetchone()

            if not cuenta or cuenta["saldo"] < monto:
                flash("Fondos insuficientes.", "danger")
                return redirect(url_for("panel_cajero", seccion="pagos"))

            cursor.execute(
                """
                UPDATE cuentas
                SET saldo = saldo - %s
                WHERE id_cuenta = %s
                """,
                (monto, id_cuenta)
            )

            cursor.execute(
                """
                INSERT INTO pagos
                (codigo_pago, id_cuenta, id_servicio, referencia, monto, estado)
                VALUES (%s, %s, %s, %s, %s, 'PAGADO')
                """,
                (codigo_pago, id_cuenta, id_servicio, referencia, monto)
            )

            cursor.execute(
                """
                INSERT INTO transacciones
                (codigo_transaccion, tipo_transaccion, id_cuenta_origen, id_cuenta_destino, monto, estado, descripcion)
                VALUES (%s, 'PAGO_SERVICIO', %s, NULL, %s, 'COMPLETADA', %s)
                """,
                (codigo_trx, id_cuenta, monto, f"Pago de servicio con referencia {referencia}.")
            )

        conexion.commit()
        flash("Pago registrado correctamente.", "success")

    except Exception as error:
        conexion.rollback()
        print("Error al procesar pago:", error)
        flash("No se pudo procesar el pago.", "danger")

    finally:
        conexion.close()

    return redirect(url_for("panel_cajero", seccion="pagos"))   

# =========================
# PANEL AUDITOR
# =========================

@app.route("/panel_auditor")
@rol_requerido("AUDITOR")
def panel_auditor():
    conexion = obtener_conexion()

    eventos = []
    transacciones = []
    pagos = []

    if conexion:
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        a.fecha,
                        COALESCE(u.usuario, 'Sistema BD') AS usuario,
                        a.modulo,
                        a.operacion,
                        a.descripcion
                    FROM auditoria a
                    LEFT JOIN usuarios u ON a.id_usuario = u.id_usuario
                    ORDER BY a.fecha DESC
                    """
                )
                eventos = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT *
                    FROM transacciones
                    ORDER BY fecha_transaccion DESC
                    """
                )
                transacciones = cursor.fetchall()

                cursor.execute(
                    """
                    SELECT
                        p.codigo_pago,
                        c.numero_cuenta,
                        s.nombre_servicio,
                        p.referencia,
                        p.monto,
                        p.estado,
                        p.fecha_pago
                    FROM pagos p
                    INNER JOIN cuentas c ON p.id_cuenta = c.id_cuenta
                    INNER JOIN servicios s ON p.id_servicio = s.id_servicio
                    ORDER BY p.fecha_pago DESC
                    """
                )
                pagos = cursor.fetchall()

        except Exception as error:
            print("Error al cargar auditoría:", error)
            flash("No se pudieron cargar los datos de auditoría.", "danger")

        finally:
            conexion.close()

    return render_template(
        "panel_auditor.html",
        eventos=eventos,
        transacciones=transacciones,
        pagos=pagos
    )

# =========================
# FORMATO DE CIFRAS DECIMALES
# =========================

@app.template_filter("moneda")
def formato_moneda(valor):
    try:
        if valor is None:
            valor = 0

        return "Q{:,.2f}".format(float(valor))

    except (ValueError, TypeError):
        return "Q0.00"


# =========================
# LOGOUT
# =========================

@app.route("/logout")
@login_requerido
def logout():
    registrar_auditoria(
        session["id_usuario"],
        "Seguridad",
        "LOGOUT",
        f"El usuario {session['usuario']} cerró sesión."
    )

    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("pgba"))


# =========================
# EJECUCIÓN
# =========================

if __name__ == "__main__":
    crear_usuarios_base()
    app.run(debug=True)
