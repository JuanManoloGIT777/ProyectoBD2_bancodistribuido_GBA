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

