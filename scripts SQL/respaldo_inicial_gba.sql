-- =========================================================
-- RESPALDO BASE INICIAL - GBA CREDOMATIC
-- Base de datos: Proyecto_Banco_Distribuido
-- Tablas incluidas:
-- auditoria, clientes, cuentas, pagos, roles, servicios,
-- solicitudes_contacto, tipos_cuenta, transacciones, usuarios
-- =========================================================

CREATE SCHEMA IF NOT EXISTS backup_gba;


-- =========================================================
-- 1. TABLA MAESTRA DE RESPALDOS BASE
-- Guarda el historial de respaldos completos realizados.
-- =========================================================

CREATE TABLE IF NOT EXISTS backup_gba.respaldos_base (
    id_respaldo_base SERIAL PRIMARY KEY,
    descripcion TEXT NOT NULL,
    fecha_respaldo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- 2. TABLAS DE RESPALDO BASE
-- Cada tabla copia la estructura de su tabla original,
-- agregando id_respaldo_base para identificar a qué respaldo pertenece.
-- =========================================================

CREATE TABLE IF NOT EXISTS backup_gba.auditoria_base AS
SELECT NULL::INTEGER AS id_respaldo_base, a.*
FROM public.auditoria a
WITH NO DATA;

CREATE TABLE IF NOT EXISTS backup_gba.clientes_base AS
SELECT NULL::INTEGER AS id_respaldo_base, c.*
FROM public.clientes c
WITH NO DATA;

CREATE TABLE IF NOT EXISTS backup_gba.cuentas_base AS
SELECT NULL::INTEGER AS id_respaldo_base, c.*
FROM public.cuentas c
WITH NO DATA;

CREATE TABLE IF NOT EXISTS backup_gba.pagos_base AS
SELECT NULL::INTEGER AS id_respaldo_base, p.*
FROM public.pagos p
WITH NO DATA;

CREATE TABLE IF NOT EXISTS backup_gba.roles_base AS
SELECT NULL::INTEGER AS id_respaldo_base, r.*
FROM public.roles r
WITH NO DATA;

CREATE TABLE IF NOT EXISTS backup_gba.servicios_base AS
SELECT NULL::INTEGER AS id_respaldo_base, s.*
FROM public.servicios s
WITH NO DATA;

CREATE TABLE IF NOT EXISTS backup_gba.solicitudes_contacto_base AS
SELECT NULL::INTEGER AS id_respaldo_base, sc.*
FROM public.solicitudes_contacto sc
WITH NO DATA;

CREATE TABLE IF NOT EXISTS backup_gba.tipos_cuenta_base AS
SELECT NULL::INTEGER AS id_respaldo_base, tc.*
FROM public.tipos_cuenta tc
WITH NO DATA;

CREATE TABLE IF NOT EXISTS backup_gba.transacciones_base AS
SELECT NULL::INTEGER AS id_respaldo_base, t.*
FROM public.transacciones t
WITH NO DATA;

CREATE TABLE IF NOT EXISTS backup_gba.usuarios_base AS
SELECT NULL::INTEGER AS id_respaldo_base, u.*
FROM public.usuarios u
WITH NO DATA;


-- =========================================================
-- 3. FUNCIÓN PARA CREAR RESPALDO BASE ACTUAL
-- Copia todos los datos actuales de las 10 tablas principales.
-- =========================================================

CREATE OR REPLACE FUNCTION backup_gba.crear_respaldo_base_actual(
    p_descripcion TEXT DEFAULT 'Respaldo base inicial del sistema'
)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_respaldo_base INTEGER;
BEGIN
    INSERT INTO backup_gba.respaldos_base (descripcion)
    VALUES (p_descripcion)
    RETURNING id_respaldo_base INTO v_id_respaldo_base;

    INSERT INTO backup_gba.auditoria_base
    SELECT v_id_respaldo_base, a.*
    FROM public.auditoria a;

    INSERT INTO backup_gba.clientes_base
    SELECT v_id_respaldo_base, c.*
    FROM public.clientes c;

    INSERT INTO backup_gba.cuentas_base
    SELECT v_id_respaldo_base, c.*
    FROM public.cuentas c;

    INSERT INTO backup_gba.pagos_base
    SELECT v_id_respaldo_base, p.*
    FROM public.pagos p;

    INSERT INTO backup_gba.roles_base
    SELECT v_id_respaldo_base, r.*
    FROM public.roles r;

    INSERT INTO backup_gba.servicios_base
    SELECT v_id_respaldo_base, s.*
    FROM public.servicios s;

    INSERT INTO backup_gba.solicitudes_contacto_base
    SELECT v_id_respaldo_base, sc.*
    FROM public.solicitudes_contacto sc;

    INSERT INTO backup_gba.tipos_cuenta_base
    SELECT v_id_respaldo_base, tc.*
    FROM public.tipos_cuenta tc;

    INSERT INTO backup_gba.transacciones_base
    SELECT v_id_respaldo_base, t.*
    FROM public.transacciones t;

    INSERT INTO backup_gba.usuarios_base
    SELECT v_id_respaldo_base, u.*
    FROM public.usuarios u;

    RETURN v_id_respaldo_base;
END;
$$;


-- =========================================================
-- 4. CREAR RESPALDO BASE INICIAL
-- Ejecuta el respaldo completo del estado actual.
-- =========================================================

SELECT backup_gba.crear_respaldo_base_actual(
    'Respaldo base del sistema bancario'
) AS id_respaldo_base_creado;



SELECT *
FROM backup_gba.respaldos_base
ORDER BY id_respaldo_base DESC;



-- =========================================================
-- CONSULTAR DATOS RESPALDADOS DEL RESPALDO BASE
-- =========================================================

-- Auditoría respaldada
SELECT *
FROM backup_gba.auditoria_base
WHERE id_respaldo_base = 1
ORDER BY id_auditoria ASC;


-- Clientes respaldados
SELECT *
FROM backup_gba.clientes_base
WHERE id_respaldo_base = 1
ORDER BY id_cliente ASC;


-- Cuentas respaldadas
SELECT *
FROM backup_gba.cuentas_base
WHERE id_respaldo_base = 1
ORDER BY id_cuenta ASC;


-- Pagos respaldados
SELECT *
FROM backup_gba.pagos_base
WHERE id_respaldo_base = 1
ORDER BY id_pago ASC;


-- Roles respaldados
SELECT *
FROM backup_gba.roles_base
WHERE id_respaldo_base = 1
ORDER BY id_rol ASC;


-- Servicios respaldados
SELECT *
FROM backup_gba.servicios_base
WHERE id_respaldo_base = 1
ORDER BY id_servicio ASC;


-- Solicitudes de contacto respaldadas
SELECT *
FROM backup_gba.solicitudes_contacto_base
WHERE id_respaldo_base = 1
ORDER BY id_solicitud ASC;


-- Tipos de cuenta respaldados
SELECT *
FROM backup_gba.tipos_cuenta_base
WHERE id_respaldo_base = 1
ORDER BY id_tipo_cuenta ASC;


-- Transacciones respaldadas
SELECT *
FROM backup_gba.transacciones_base
WHERE id_respaldo_base = 1
ORDER BY id_transaccion ASC;


-- Usuarios respaldados
SELECT *
FROM backup_gba.usuarios_base
WHERE id_respaldo_base = 1
ORDER BY id_usuario ASC;



