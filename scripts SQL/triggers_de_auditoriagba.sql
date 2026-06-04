-- =========================================================
-- TRIGGERS DE AUDITORÍA - GBA CREDOMATIC
-- Base de datos: Proyecto_Banco_Distribuido
-- Tabla utilizada: public.auditoria
-- =========================================================


-- =========================================================
-- 1. FUNCIONES AUXILIARES PARA OBTENER USUARIO DESDE FLASK
-- =========================================================

CREATE OR REPLACE FUNCTION public.fn_obtener_id_usuario_app()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_usuario TEXT;
BEGIN
    v_id_usuario := current_setting('app.id_usuario', true);

    IF v_id_usuario IS NULL OR v_id_usuario = '' THEN
        RETURN NULL;
    END IF;

    RETURN v_id_usuario::INTEGER;

EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$;


CREATE OR REPLACE FUNCTION public.fn_obtener_usuario_app()
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    v_usuario TEXT;
BEGIN
    v_usuario := current_setting('app.usuario', true);

    IF v_usuario IS NULL OR v_usuario = '' THEN
        RETURN 'Sistema BD';
    END IF;

    RETURN v_usuario;

EXCEPTION
    WHEN OTHERS THEN
        RETURN 'Sistema BD';
END;
$$;


-- =========================================================
-- 2. TRIGGER: REGISTRO DE USUARIOS INTERNOS
-- Registra cuando el administrador crea un usuario.
-- =========================================================

CREATE OR REPLACE FUNCTION public.fn_auditar_insert_usuario()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO public.auditoria (
        id_usuario,
        modulo,
        operacion,
        descripcion
    )
    VALUES (
        public.fn_obtener_id_usuario_app(),
        'Usuarios',
        'REGISTRO_USUARIO',
        'El administrador ' || public.fn_obtener_usuario_app() ||
        ' registró al usuario interno ' || NEW.usuario || '.'
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_auditar_insert_usuario
AFTER INSERT ON public.usuarios
FOR EACH ROW
EXECUTE FUNCTION public.fn_auditar_insert_usuario();


-- =========================================================
-- 3. TRIGGER: ACTIVACIÓN / INACTIVACIÓN DE USUARIOS
-- Registra cuando un usuario cambia de ACTIVO a INACTIVO o viceversa.
-- =========================================================

CREATE OR REPLACE FUNCTION public.fn_auditar_estado_usuario()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.estado IS DISTINCT FROM NEW.estado THEN

        IF NEW.estado = 'INACTIVO' THEN
            INSERT INTO public.auditoria (
                id_usuario,
                modulo,
                operacion,
                descripcion
            )
            VALUES (
                public.fn_obtener_id_usuario_app(),
                'Usuarios',
                'INACTIVACION_USUARIO',
                'El administrador ' || public.fn_obtener_usuario_app() ||
                ' inactivó al usuario interno ' || NEW.usuario || '.'
            );

        ELSIF NEW.estado = 'ACTIVO' THEN
            INSERT INTO public.auditoria (
                id_usuario,
                modulo,
                operacion,
                descripcion
            )
            VALUES (
                public.fn_obtener_id_usuario_app(),
                'Usuarios',
                'ACTIVACION_USUARIO',
                'El administrador ' || public.fn_obtener_usuario_app() ||
                ' activó al usuario ' || NEW.usuario || '.'
            );
        END IF;

    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_auditar_estado_usuario
AFTER UPDATE OF estado ON public.usuarios
FOR EACH ROW
EXECUTE FUNCTION public.fn_auditar_estado_usuario();


-- =========================================================
-- 4. TRIGGER: REGISTRO DE CLIENTES
-- Registra cuando el cajero crea un cliente.
-- =========================================================

CREATE OR REPLACE FUNCTION public.fn_auditar_insert_cliente()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO public.auditoria (
        id_usuario,
        modulo,
        operacion,
        descripcion
    )
    VALUES (
        public.fn_obtener_id_usuario_app(),
        'Clientes',
        'INSERT',
        'El cajero ' || public.fn_obtener_usuario_app() ||
        ' registró al cliente ' || NEW.nombres || ' ' || NEW.apellidos ||
        ' con DPI ' || NEW.dpi || '.'
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_auditar_insert_cliente
AFTER INSERT ON public.clientes
FOR EACH ROW
EXECUTE FUNCTION public.fn_auditar_insert_cliente();


-- =========================================================
-- 5. TRIGGER: ACTIVACIÓN / INACTIVACIÓN DE CLIENTES
-- Registra cuando un cliente cambia de estado.
-- =========================================================

CREATE OR REPLACE FUNCTION public.fn_auditar_estado_cliente()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.estado IS DISTINCT FROM NEW.estado THEN

        IF NEW.estado = 'INACTIVO' THEN
            INSERT INTO public.auditoria (
                id_usuario,
                modulo,
                operacion,
                descripcion
            )
            VALUES (
                public.fn_obtener_id_usuario_app(),
                'Clientes',
                'INACTIVACION_CLIENTE',
                'El administrador ' || public.fn_obtener_usuario_app() ||
                ' inactivó al cliente ' || NEW.nombres || ' ' || NEW.apellidos || '.'
            );

        ELSIF NEW.estado = 'ACTIVO' THEN
            INSERT INTO public.auditoria (
                id_usuario,
                modulo,
                operacion,
                descripcion
            )
            VALUES (
                public.fn_obtener_id_usuario_app(),
                'Clientes',
                'ACTIVACION_CLIENTE',
                'El administrador ' || public.fn_obtener_usuario_app() ||
                ' activó al cliente ' || NEW.nombres || ' ' || NEW.apellidos || '.'
            );
        END IF;

    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_auditar_estado_cliente
AFTER UPDATE OF estado ON public.clientes
FOR EACH ROW
EXECUTE FUNCTION public.fn_auditar_estado_cliente();


-- =========================================================
-- 6. TRIGGER: CREACIÓN DE CUENTAS
-- Registra cuando el cajero crea una cuenta bancaria.
-- =========================================================

CREATE OR REPLACE FUNCTION public.fn_auditar_insert_cuenta()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO public.auditoria (
        id_usuario,
        modulo,
        operacion,
        descripcion
    )
    VALUES (
        public.fn_obtener_id_usuario_app(),
        'Cuentas',
        'INSERT',
        'El cajero ' || public.fn_obtener_usuario_app() ||
        ' creó la cuenta ' || NEW.numero_cuenta || '.'
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_auditar_insert_cuenta
AFTER INSERT ON public.cuentas
FOR EACH ROW
EXECUTE FUNCTION public.fn_auditar_insert_cuenta();


-- =========================================================
-- 7. TRIGGER: ACTIVACIÓN / INACTIVACIÓN DE CUENTAS
-- Registra cuando una cuenta cambia de estado.
-- =========================================================

CREATE OR REPLACE FUNCTION public.fn_auditar_estado_cuenta()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.estado IS DISTINCT FROM NEW.estado THEN

        IF NEW.estado IN ('INACTIVA', 'INACTIVO') THEN
            INSERT INTO public.auditoria (
                id_usuario,
                modulo,
                operacion,
                descripcion
            )
            VALUES (
                public.fn_obtener_id_usuario_app(),
                'Cuentas',
                'INACTIVACION_CUENTA',
                'El administrador ' || public.fn_obtener_usuario_app() ||
                ' inactivó la cuenta ' || NEW.numero_cuenta || '.'
            );

        ELSIF NEW.estado IN ('ACTIVA', 'ACTIVO') THEN
            INSERT INTO public.auditoria (
                id_usuario,
                modulo,
                operacion,
                descripcion
            )
            VALUES (
                public.fn_obtener_id_usuario_app(),
                'Cuentas',
                'ACTIVACION_CUENTA',
                'El administrador ' || public.fn_obtener_usuario_app() ||
                ' activó la cuenta ' || NEW.numero_cuenta || '.'
            );
        END IF;

    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_auditar_estado_cuenta
AFTER UPDATE OF estado ON public.cuentas
FOR EACH ROW
EXECUTE FUNCTION public.fn_auditar_estado_cuenta();


-- =========================================================
-- 8. TRIGGER: REGISTRO DE TRANSACCIONES
-- Registra la operación real: DEPOSITO, RETIRO,
-- TRANSFERENCIA o PAGO_SERVICIO.
-- =========================================================

CREATE OR REPLACE FUNCTION public.fn_auditar_insert_transaccion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_usuario TEXT;
    v_operacion TEXT;
    v_descripcion TEXT;
BEGIN
    v_usuario := public.fn_obtener_usuario_app();
    v_operacion := NEW.tipo_transaccion;

    IF NEW.tipo_transaccion = 'DEPOSITO' THEN

        v_descripcion :=
            'El cajero ' || v_usuario ||
            ' realizó un depósito por Q' || NEW.monto ||
            ' en la cuenta destino ID ' || COALESCE(NEW.id_cuenta_destino::TEXT, 'N/A') || '.';

    ELSIF NEW.tipo_transaccion = 'RETIRO' THEN

        v_descripcion :=
            'El cajero ' || v_usuario ||
            ' realizó un retiro por Q' || NEW.monto ||
            ' desde la cuenta origen ID ' || COALESCE(NEW.id_cuenta_origen::TEXT, 'N/A') || '.';

    ELSIF NEW.tipo_transaccion = 'TRANSFERENCIA' THEN

        v_descripcion :=
            'El cajero ' || v_usuario ||
            ' realizó una transferencia por Q' || NEW.monto ||
            ' desde la cuenta origen ID ' || COALESCE(NEW.id_cuenta_origen::TEXT, 'N/A') ||
            ' hacia la cuenta destino ID ' || COALESCE(NEW.id_cuenta_destino::TEXT, 'N/A') || '.';

    ELSIF NEW.tipo_transaccion = 'PAGO_SERVICIO' THEN

        v_descripcion :=
            'El cajero ' || v_usuario ||
            ' registró una transacción de pago de servicio por Q' || NEW.monto ||
            ' desde la cuenta origen ID ' || COALESCE(NEW.id_cuenta_origen::TEXT, 'N/A') || '.';

    ELSE

        v_operacion := 'OPERACION_BANCARIA';

        v_descripcion :=
            'El usuario ' || v_usuario ||
            ' procesó una operación bancaria por Q' || NEW.monto || '.';

    END IF;

    INSERT INTO public.auditoria (
        id_usuario,
        modulo,
        operacion,
        descripcion
    )
    VALUES (
        public.fn_obtener_id_usuario_app(),
        'Transacciones',
        v_operacion,
        v_descripcion
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_auditar_insert_transaccion
AFTER INSERT ON public.transacciones
FOR EACH ROW
EXECUTE FUNCTION public.fn_auditar_insert_transaccion();


-- =========================================================
-- 9. TRIGGER: ANULACIÓN DE TRANSACCIONES
-- Registra cuando una transacción cambia a estado ANULADA.
-- =========================================================

CREATE OR REPLACE FUNCTION public.fn_auditar_estado_transaccion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.estado IS DISTINCT FROM NEW.estado THEN

        IF NEW.estado = 'ANULADA' THEN

            INSERT INTO public.auditoria (
                id_usuario,
                modulo,
                operacion,
                descripcion
            )
            VALUES (
                public.fn_obtener_id_usuario_app(),
                'Transacciones',
                'ANULACION',
                'El cajero ' || public.fn_obtener_usuario_app() ||
                ' anuló la transacción ' || NEW.codigo_transaccion ||
                ' de tipo ' || NEW.tipo_transaccion ||
                ' por Q' || NEW.monto || '.'
            );

        END IF;

    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_auditar_estado_transaccion
AFTER UPDATE OF estado ON public.transacciones
FOR EACH ROW
EXECUTE FUNCTION public.fn_auditar_estado_transaccion();


-- =========================================================
-- 10. TRIGGER: REGISTRO DE PAGOS
-- Registra pagos con operación PAGO_SERVICIO.
-- =========================================================

CREATE OR REPLACE FUNCTION public.fn_auditar_insert_pago()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO public.auditoria (
        id_usuario,
        modulo,
        operacion,
        descripcion
    )
    VALUES (
        public.fn_obtener_id_usuario_app(),
        'Pagos',
        'PAGO_SERVICIO',
        'El cajero ' || public.fn_obtener_usuario_app() ||
        ' registró un pago de servicio por Q' || NEW.monto ||
        ' con referencia ' || NEW.referencia || '.'
    );

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_auditar_insert_pago
AFTER INSERT ON public.pagos
FOR EACH ROW
EXECUTE FUNCTION public.fn_auditar_insert_pago();


-- =========================================================
-- 11. CONSULTA DE VERIFICACIÓN
-- =========================================================

SELECT
    id_auditoria,
    id_usuario,
    modulo,
    operacion,
    descripcion,
    fecha
FROM public.auditoria
ORDER BY id_auditoria DESC;