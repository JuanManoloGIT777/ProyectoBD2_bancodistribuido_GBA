-- =========================================================
-- RESPALDO CONTINUO LÓGICO - GBA CREDOMATIC
-- Base de datos: Proyecto_Banco_Distribuido
-- Uso: PostgreSQL / pgAdmin / Query Tool
-- =========================================================

-- =========================================================
-- 1. CREAR ESQUEMA DE RESPALDO
-- Descripción:
-- Crea un espacio separado llamado backup_gba para guardar
-- información de respaldo sin mezclarla con las tablas principales.
-- =========================================================

CREATE SCHEMA IF NOT EXISTS backup_gba;


-- =========================================================
-- 2. TABLA DE CAMBIOS CONTINUOS
-- Descripción:
-- Guarda cada cambio realizado en tablas críticas.
-- Cada registro almacena:
-- - tabla afectada
-- - tipo de operación
-- - datos anteriores
-- - datos nuevos
-- - fecha del cambio
-- =========================================================

CREATE TABLE IF NOT EXISTS backup_gba.cambios_continuos (
    id_cambio SERIAL PRIMARY KEY,
    tabla_afectada VARCHAR(80) NOT NULL,
    operacion VARCHAR(20) NOT NULL,
    id_registro INTEGER,
    datos_anteriores JSONB,
    datos_nuevos JSONB,
    fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================================================
-- 3. FUNCIÓN GENERAL DE RESPALDO CONTINUO
-- Descripción:
-- Esta función se ejecuta automáticamente con triggers.
-- Guarda una copia lógica del registro insertado, actualizado o eliminado.
-- =========================================================

CREATE OR REPLACE FUNCTION backup_gba.fn_respaldo_continuo()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_registro INTEGER;
BEGIN
    -- INSERT: cuando se agrega un nuevo registro
    IF TG_OP = 'INSERT' THEN

        IF TG_TABLE_NAME = 'usuarios' THEN
            v_id_registro := NEW.id_usuario;
        ELSIF TG_TABLE_NAME = 'clientes' THEN
            v_id_registro := NEW.id_cliente;
        ELSIF TG_TABLE_NAME = 'cuentas' THEN
            v_id_registro := NEW.id_cuenta;
        ELSIF TG_TABLE_NAME = 'transacciones' THEN
            v_id_registro := NEW.id_transaccion;
        ELSIF TG_TABLE_NAME = 'pagos' THEN
            v_id_registro := NEW.id_pago;
        ELSIF TG_TABLE_NAME = 'auditoria' THEN
            v_id_registro := NEW.id_auditoria;
        ELSE
            v_id_registro := NULL;
        END IF;

        INSERT INTO backup_gba.cambios_continuos (
            tabla_afectada,
            operacion,
            id_registro,
            datos_anteriores,
            datos_nuevos
        )
        VALUES (
            TG_TABLE_NAME,
            TG_OP,
            v_id_registro,
            NULL,
            to_jsonb(NEW)
        );

        RETURN NEW;
    END IF;


    -- UPDATE: cuando se modifica un registro
    IF TG_OP = 'UPDATE' THEN

        IF TG_TABLE_NAME = 'usuarios' THEN
            v_id_registro := NEW.id_usuario;
        ELSIF TG_TABLE_NAME = 'clientes' THEN
            v_id_registro := NEW.id_cliente;
        ELSIF TG_TABLE_NAME = 'cuentas' THEN
            v_id_registro := NEW.id_cuenta;
        ELSIF TG_TABLE_NAME = 'transacciones' THEN
            v_id_registro := NEW.id_transaccion;
        ELSIF TG_TABLE_NAME = 'pagos' THEN
            v_id_registro := NEW.id_pago;
        ELSIF TG_TABLE_NAME = 'auditoria' THEN
            v_id_registro := NEW.id_auditoria;
        ELSE
            v_id_registro := NULL;
        END IF;

        INSERT INTO backup_gba.cambios_continuos (
            tabla_afectada,
            operacion,
            id_registro,
            datos_anteriores,
            datos_nuevos
        )
        VALUES (
            TG_TABLE_NAME,
            TG_OP,
            v_id_registro,
            to_jsonb(OLD),
            to_jsonb(NEW)
        );

        RETURN NEW;
    END IF;


    -- DELETE: cuando se elimina un registro
    IF TG_OP = 'DELETE' THEN

        IF TG_TABLE_NAME = 'usuarios' THEN
            v_id_registro := OLD.id_usuario;
        ELSIF TG_TABLE_NAME = 'clientes' THEN
            v_id_registro := OLD.id_cliente;
        ELSIF TG_TABLE_NAME = 'cuentas' THEN
            v_id_registro := OLD.id_cuenta;
        ELSIF TG_TABLE_NAME = 'transacciones' THEN
            v_id_registro := OLD.id_transaccion;
        ELSIF TG_TABLE_NAME = 'pagos' THEN
            v_id_registro := OLD.id_pago;
        ELSIF TG_TABLE_NAME = 'auditoria' THEN
            v_id_registro := OLD.id_auditoria;
        ELSE
            v_id_registro := NULL;
        END IF;

        INSERT INTO backup_gba.cambios_continuos (
            tabla_afectada,
            operacion,
            id_registro,
            datos_anteriores,
            datos_nuevos
        )
        VALUES (
            TG_TABLE_NAME,
            TG_OP,
            v_id_registro,
            to_jsonb(OLD),
            NULL
        );

        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$;


-- =========================================================
-- 4. ELIMINAR TRIGGERS ANTERIORES SI EXISTEN
-- Descripción:
-- Evita errores si ejecutas el script más de una vez.
-- =========================================================

DROP TRIGGER IF EXISTS trg_respaldo_continuo_usuarios ON public.usuarios;
DROP TRIGGER IF EXISTS trg_respaldo_continuo_clientes ON public.clientes;
DROP TRIGGER IF EXISTS trg_respaldo_continuo_cuentas ON public.cuentas;
DROP TRIGGER IF EXISTS trg_respaldo_continuo_transacciones ON public.transacciones;
DROP TRIGGER IF EXISTS trg_respaldo_continuo_pagos ON public.pagos;
DROP TRIGGER IF EXISTS trg_respaldo_continuo_auditoria ON public.auditoria;


-- =========================================================
-- 5. CREAR TRIGGERS DE RESPALDO CONTINUO
-- Descripción:
-- Cada trigger se activa automáticamente cuando ocurre un
-- INSERT, UPDATE o DELETE en una tabla crítica.
-- =========================================================

CREATE TRIGGER trg_respaldo_continuo_usuarios
AFTER INSERT OR UPDATE OR DELETE ON public.usuarios
FOR EACH ROW
EXECUTE FUNCTION backup_gba.fn_respaldo_continuo();


CREATE TRIGGER trg_respaldo_continuo_clientes
AFTER INSERT OR UPDATE OR DELETE ON public.clientes
FOR EACH ROW
EXECUTE FUNCTION backup_gba.fn_respaldo_continuo();


CREATE TRIGGER trg_respaldo_continuo_cuentas
AFTER INSERT OR UPDATE OR DELETE ON public.cuentas
FOR EACH ROW
EXECUTE FUNCTION backup_gba.fn_respaldo_continuo();


CREATE TRIGGER trg_respaldo_continuo_transacciones
AFTER INSERT OR UPDATE OR DELETE ON public.transacciones
FOR EACH ROW
EXECUTE FUNCTION backup_gba.fn_respaldo_continuo();


CREATE TRIGGER trg_respaldo_continuo_pagos
AFTER INSERT OR UPDATE OR DELETE ON public.pagos
FOR EACH ROW
EXECUTE FUNCTION backup_gba.fn_respaldo_continuo();


CREATE TRIGGER trg_respaldo_continuo_auditoria
AFTER INSERT OR UPDATE OR DELETE ON public.auditoria
FOR EACH ROW
EXECUTE FUNCTION backup_gba.fn_respaldo_continuo();


-- =========================================================
-- 6. CONSULTA DE VERIFICACIÓN
-- Descripción:
-- Permite ver los últimos cambios respaldados.
-- =========================================================

SELECT *
FROM backup_gba.cambios_continuos
ORDER BY id_cambio DESC;





-- Para ver los cambios respaldados

SELECT
    id_cambio,
    tabla_afectada,
    operacion,
    id_registro,
    fecha_cambio
FROM backup_gba.cambios_continuos
ORDER BY id_cambio DESC;


-- Para ver el det