-- =========================================================
-- PRUEBA DE ELIMINACIÓN Y RECUPERACIÓN
-- Respaldo usado: id_respaldo_base = 1
-- =========================================================

-- 1. Ver datos actuales
SELECT COUNT(*) AS total_antes_eliminar
FROM public.auditoria;

SELECT *
FROM public.auditoria
ORDER BY id_auditoria ASC;


-- 2. Eliminar datos de la tabla auditoria
DELETE FROM public.auditoria;


-- 3. Confirmar que se eliminaron
SELECT COUNT(*) AS total_despues_eliminar
FROM public.auditoria;


-- 4. Restaurar datos desde el respaldo base
INSERT INTO public.auditoria (
    id_auditoria,
    id_usuario,
    modulo,
    operacion,
    descripcion,
    fecha
)
SELECT
    id_auditoria,
    id_usuario,
    modulo,
    operacion,
    descripcion,
    fecha
FROM backup_gba.auditoria_base
WHERE id_respaldo_base = 1;


-- 5. Reajustar secuencia SERIAL
SELECT setval(
    'auditoria_id_auditoria_seq',
    COALESCE((SELECT MAX(id_auditoria) FROM public.auditoria), 1),
    true
);


-- 6. Verificar recuperación
SELECT COUNT(*) AS total_despues_recuperar
FROM public.auditoria;

SELECT *
FROM public.auditoria
ORDER BY id_auditoria ASC;





-- =========================================================
-- PRUEBA DE ELIMINACIÓN Y RECUPERACIÓN DE PAGOS
-- Respaldo usado: id_respaldo_base = 1
-- =========================================================

-- 1. Ver datos actuales
SELECT COUNT(*) AS total_antes_eliminar
FROM public.pagos;

SELECT *
FROM public.pagos
ORDER BY id_pago ASC;


-- 2. Eliminar datos de la tabla pagos
DELETE FROM public.pagos;


-- 3. Confirmar que se eliminaron
SELECT COUNT(*) AS total_despues_eliminar
FROM public.pagos;


-- 4. Restaurar datos desde el respaldo base
INSERT INTO public.pagos (
    id_pago,
    codigo_pago,
    id_cuenta,
    id_servicio,
    referencia,
    monto,
    estado,
    fecha_pago
)
SELECT
    id_pago,
    codigo_pago,
    id_cuenta,
    id_servicio,
    referencia,
    monto,
    estado,
    fecha_pago
FROM backup_gba.pagos_base
WHERE id_respaldo_base = 1;


-- 5. Reajustar secuencia SERIAL
SELECT setval(
    'pagos_id_pago_seq',
    COALESCE((SELECT MAX(id_pago) FROM public.pagos), 1),
    true
);


-- 6. Verificar recuperación
SELECT COUNT(*) AS total_despues_recuperar
FROM public.pagos;






-- =========================================================
-- PRUEBA DE ELIMINACIÓN Y RECUPERACIÓN DE TRANSACCIONES
-- Respaldo usado: id_respaldo_base = 1
-- =========================================================

-- 1. Ver datos actuales
SELECT COUNT(*) AS total_antes_eliminar
FROM public.transacciones;

SELECT *
FROM public.transacciones
ORDER BY id_transaccion ASC;


-- 2. Eliminar datos de la tabla transacciones
DELETE FROM public.transacciones;


-- 3. Confirmar que se eliminaron
SELECT COUNT(*) AS total_despues_eliminar
FROM public.transacciones;


-- 4. Restaurar datos desde el respaldo base
INSERT INTO public.transacciones (
    id_transaccion,
    codigo_transaccion,
    tipo_transaccion,
    id_cuenta_origen,
    id_cuenta_destino,
    monto,
    estado,
    descripcion,
    fecha_transaccion
)
SELECT
    id_transaccion,
    codigo_transaccion,
    tipo_transaccion,
    id_cuenta_origen,
    id_cuenta_destino,
    monto,
    estado,
    descripcion,
    fecha_transaccion
FROM backup_gba.transacciones_base
WHERE id_respaldo_base = 1;


-- 5. Reajustar secuencia SERIAL
SELECT setval(
    'transacciones_id_transaccion_seq',
    COALESCE((SELECT MAX(id_transaccion) FROM public.transacciones), 1),
    true
);


-- 6. Verificar recuperación
SELECT COUNT(*) AS total_despues_recuperar
FROM public.transacciones;





-- =========================================================
-- PRUEBA DE ELIMINACIÓN Y RECUPERACIÓN DE SERVICIOS
-- Respaldo usado: id_respaldo_base = 1
-- =========================================================

-- 1. Ver datos actuales
SELECT COUNT(*) AS total_antes_eliminar
FROM public.servicios;

SELECT *
FROM public.servicios
ORDER BY id_servicio ASC;


-- 2. Eliminar datos dependientes de la tabla servicios
DELETE FROM public.pagos;


-- 3. Eliminar datos de la tabla servicios
DELETE FROM public.servicios;


-- 4. Confirmar que se eliminaron
SELECT COUNT(*) AS total_despues_eliminar
FROM public.servicios;


-- 5. Restaurar datos desde el respaldo base
INSERT INTO public.servicios (
    id_servicio,
    nombre_servicio,
    descripcion,
    estado
)
SELECT
    id_servicio,
    nombre_servicio,
    descripcion,
    estado
FROM backup_gba.servicios_base
WHERE id_respaldo_base = 1;


-- 6. Restaurar datos dependientes desde el respaldo base
INSERT INTO public.pagos (
    id_pago,
    codigo_pago,
    id_cuenta,
    id_servicio,
    referencia,
    monto,
    estado,
    fecha_pago
)
SELECT
    id_pago,
    codigo_pago,
    id_cuenta,
    id_servicio,
    referencia,
    monto,
    estado,
    fecha_pago
FROM backup_gba.pagos_base
WHERE id_respaldo_base = 1;


-- 7. Reajustar secuencias SERIAL
SELECT setval(
    'servicios_id_servicio_seq',
    COALESCE((SELECT MAX(id_servicio) FROM public.servicios), 1),
    true
);

SELECT setval(
    'pagos_id_pago_seq',
    COALESCE((SELECT MAX(id_pago) FROM public.pagos), 1),
    true
);


-- 8. Verificar recuperación
SELECT COUNT(*) AS total_despues_recuperar
FROM public.servicios;








-- =========================================================
-- PRUEBA DE ELIMINACIÓN Y RECUPERACIÓN DE CUENTAS
-- Respaldo usado: id_respaldo_base = 1
-- =========================================================

-- 1. Ver datos actuales
SELECT COUNT(*) AS total_antes_eliminar
FROM public.cuentas;

SELECT *
FROM public.cuentas
ORDER BY id_cuenta ASC;


-- 2. Eliminar datos dependientes de la tabla cuentas
DELETE FROM public.pagos;
DELETE FROM public.transacciones;


-- 3. Eliminar datos de la tabla cuentas
DELETE FROM public.cuentas;


-- 4. Confirmar que se eliminaron
SELECT COUNT(*) AS total_despues_eliminar
FROM public.cuentas;


-- 5. Restaurar datos desde el respaldo base
INSERT INTO public.cuentas (
    id_cuenta,
    id_cliente,
    id_tipo_cuenta,
    numero_cuenta,
    saldo,
    estado,
    fecha_apertura
)
SELECT
    id_cuenta,
    id_cliente,
    id_tipo_cuenta,
    numero_cuenta,
    saldo,
    estado,
    fecha_apertura
FROM backup_gba.cuentas_base
WHERE id_respaldo_base = 1;


-- 6. Restaurar datos dependientes desde el respaldo base
INSERT INTO public.transacciones (
    id_transaccion,
    codigo_transaccion,
    tipo_transaccion,
    id_cuenta_origen,
    id_cuenta_destino,
    monto,
    estado,
    descripcion,
    fecha_transaccion
)
SELECT
    id_transaccion,
    codigo_transaccion,
    tipo_transaccion,
    id_cuenta_origen,
    id_cuenta_destino,
    monto,
    estado,
    descripcion,
    fecha_transaccion
FROM backup_gba.transacciones_base
WHERE id_respaldo_base = 1;

INSERT INTO public.pagos (
    id_pago,
    codigo_pago,
    id_cuenta,
    id_servicio,
    referencia,
    monto,
    estado,
    fecha_pago
)
SELECT
    id_pago,
    codigo_pago,
    id_cuenta,
    id_servicio,
    referencia,
    monto,
    estado,
    fecha_pago
FROM backup_gba.pagos_base
WHERE id_respaldo_base = 1;


-- 7. Reajustar secuencias SERIAL
SELECT setval(
    'cuentas_id_cuenta_seq',
    COALESCE((SELECT MAX(id_cuenta) FROM public.cuentas), 1),
    true
);

SELECT setval(
    'transacciones_id_transaccion_seq',
    COALESCE((SELECT MAX(id_transaccion) FROM public.transacciones), 1),
    true
);

SELECT setval(
    'pagos_id_pago_seq',
    COALESCE((SELECT MAX(id_pago) FROM public.pagos), 1),
    true
);


-- 8. Verificar recuperación
SELECT COUNT(*) AS total_despues_recuperar
FROM public.cuentas;







-- =========================================================
-- PRUEBA DE ELIMINACIÓN Y RECUPERACIÓN DE CLIENTES
-- Respaldo usado: id_respaldo_base = 1
-- =========================================================

-- 1. Ver datos actuales
SELECT COUNT(*) AS total_antes_eliminar
FROM public.clientes;

SELECT *
FROM public.clientes
ORDER BY id_cliente ASC;


-- 2. Eliminar datos dependientes de la tabla clientes
DELETE FROM public.pagos;
DELETE FROM public.transacciones;
DELETE FROM public.cuentas;


-- 3. Eliminar datos de la tabla clientes
DELETE FROM public.clientes;


-- 4. Confirmar que se eliminaron
SELECT COUNT(*) AS total_despues_eliminar
FROM public.clientes;


-- 5. Restaurar datos desde el respaldo base
INSERT INTO public.clientes (
    id_cliente,
    dpi,
    nombres,
    apellidos,
    telefono,
    correo,
    direccion,
    estado,
    fecha_registro
)
SELECT
    id_cliente,
    dpi,
    nombres,
    apellidos,
    telefono,
    correo,
    direccion,
    estado,
    fecha_registro
FROM backup_gba.clientes_base
WHERE id_respaldo_base = 1;


-- 6. Restaurar datos dependientes desde el respaldo base
INSERT INTO public.cuentas (
    id_cuenta,
    id_cliente,
    id_tipo_cuenta,
    numero_cuenta,
    saldo,
    estado,
    fecha_apertura
)
SELECT
    id_cuenta,
    id_cliente,
    id_tipo_cuenta,
    numero_cuenta,
    saldo,
    estado,
    fecha_apertura
FROM backup_gba.cuentas_base
WHERE id_respaldo_base = 1;

INSERT INTO public.transacciones (
    id_transaccion,
    codigo_transaccion,
    tipo_transaccion,
    id_cuenta_origen,
    id_cuenta_destino,
    monto,
    estado,
    descripcion,
    fecha_transaccion
)
SELECT
    id_transaccion,
    codigo_transaccion,
    tipo_transaccion,
    id_cuenta_origen,
    id_cuenta_destino,
    monto,
    estado,
    descripcion,
    fecha_transaccion
FROM backup_gba.transacciones_base
WHERE id_respaldo_base = 1;

INSERT INTO public.pagos (
    id_pago,
    codigo_pago,
    id_cuenta,
    id_servicio,
    referencia,
    monto,
    estado,
    fecha_pago
)
SELECT
    id_pago,
    codigo_pago,
    id_cuenta,
    id_servicio,
    referencia,
    monto,
    estado,
    fecha_pago
FROM backup_gba.pagos_base
WHERE id_respaldo_base = 1;


-- 7. Reajustar secuencias SERIAL
SELECT setval(
    'clientes_id_cliente_seq',
    COALESCE((SELECT MAX(id_cliente) FROM public.clientes), 1),
    true
);

SELECT setval(
    'cuentas_id_cuenta_seq',
    COALESCE((SELECT MAX(id_cuenta) FROM public.cuentas), 1),
    true
);

SELECT setval(
    'transacciones_id_transaccion_seq',
    COALESCE((SELECT MAX(id_transaccion) FROM public.transacciones), 1),
    true
);

SELECT setval(
    'pagos_id_pago_seq',
    COALESCE((SELECT MAX(id_pago) FROM public.pagos), 1),
    true
);


-- 8. Verificar recuperación
SELECT COUNT(*) AS total_despues_recuperar
FROM public.clientes;






-- =========================================================
-- PRUEBA DE ELIMINACIÓN Y RECUPERACIÓN DE USUARIOS
-- Respaldo usado: id_respaldo_base = 1
-- =========================================================

-- 1. Ver datos actuales
SELECT COUNT(*) AS total_antes_eliminar
FROM public.usuarios;

SELECT *
FROM public.usuarios
ORDER BY id_usuario ASC;


-- 2. Eliminar datos dependientes de la tabla usuarios
DELETE FROM public.auditoria;


-- 3. Eliminar datos de la tabla usuarios
DELETE FROM public.usuarios;


-- 4. Confirmar que se eliminaron
SELECT COUNT(*) AS total_despues_eliminar
FROM public.usuarios;


-- 5. Restaurar datos desde el respaldo base
INSERT INTO public.usuarios (
    id_usuario,
    id_rol,
    nombre_completo,
    usuario,
    correo,
    clave,
    estado,
    fecha_registro
)
SELECT
    id_usuario,
    id_rol,
    nombre_completo,
    usuario,
    correo,
    clave,
    estado,
    fecha_registro
FROM backup_gba.usuarios_base
WHERE id_respaldo_base = 1;


-- 6. Restaurar datos dependientes desde el respaldo base
INSERT INTO public.auditoria (
    id_auditoria,
    id_usuario,
    modulo,
    operacion,
    descripcion,
    fecha
)
SELECT
    id_auditoria,
    id_usuario,
    modulo,
    operacion,
    descripcion,
    fecha
FROM backup_gba.auditoria_base
WHERE id_respaldo_base = 1;


-- 7. Reajustar secuencias SERIAL
SELECT setval(
    'usuarios_id_usuario_seq',
    COALESCE((SELECT MAX(id_usuario) FROM public.usuarios), 1),
    true
);

SELECT setval(
    'auditoria_id_auditoria_seq',
    COALESCE((SELECT MAX(id_auditoria) FROM public.auditoria), 1),
    true
);


-- 8. Verificar recuperación
SELECT COUNT(*) AS total_despues_recuperar
FROM public.usuarios;






-- =========================================================
-- PRUEBA DE ELIMINACIÓN Y RECUPERACIÓN DE ROLES
-- Respaldo usado: id_respaldo_base = 1
-- =========================================================

-- 1. Ver datos actuales
SELECT COUNT(*) AS total_antes_eliminar
FROM public.roles;

SELECT *
FROM public.roles
ORDER BY id_rol ASC;


-- 2. Eliminar datos dependientes de la tabla roles
DELETE FROM public.auditoria;
DELETE FROM public.usuarios;


-- 3. Eliminar datos de la tabla roles
DELETE FROM public.roles;


-- 4. Confirmar que se eliminaron
SELECT COUNT(*) AS total_despues_eliminar
FROM public.roles;


-- 5. Restaurar datos desde el respaldo base
INSERT INTO public.roles (
    id_rol,
    nombre_rol,
    descripcion,
    estado,
    fecha_registro
)
SELECT
    id_rol,
    nombre_rol,
    descripcion,
    estado,
    fecha_registro
FROM backup_gba.roles_base
WHERE id_respaldo_base = 1;


-- 6. Restaurar datos dependientes desde el respaldo base
INSERT INTO public.usuarios (
    id_usuario,
    id_rol,
    nombre_completo,
    usuario,
    correo,
    clave,
    estado,
    fecha_registro
)
SELECT
    id_usuario,
    id_rol,
    nombre_completo,
    usuario,
    correo,
    clave,
    estado,
    fecha_registro
FROM backup_gba.usuarios_base
WHERE id_respaldo_base = 1;

INSERT INTO public.auditoria (
    id_auditoria,
    id_usuario,
    modulo,
    operacion,
    descripcion,
    fecha
)
SELECT
    id_auditoria,
    id_usuario,
    modulo,
    operacion,
    descripcion,
    fecha
FROM backup_gba.auditoria_base
WHERE id_respaldo_base = 1;


-- 7. Reajustar secuencias SERIAL
SELECT setval(
    'roles_id_rol_seq',
    COALESCE((SELECT MAX(id_rol) FROM public.roles), 1),
    true
);

SELECT setval(
    'usuarios_id_usuario_seq',
    COALESCE((SELECT MAX(id_usuario) FROM public.usuarios), 1),
    true
);

SELECT setval(
    'auditoria_id_auditoria_seq',
    COALESCE((SELECT MAX(id_auditoria) FROM public.auditoria), 1),
    true
);


-- 8. Verificar recuperación
SELECT COUNT(*) AS total_despues_recuperar
FROM public.roles;




-- =========================================================
-- PRUEBA DE ELIMINACIÓN Y RECUPERACIÓN DE TIPOS_CUENTA
-- Respaldo usado: id_respaldo_base = 1
-- =========================================================

-- 1. Ver datos actuales
SELECT COUNT(*) AS total_antes_eliminar
FROM public.tipos_cuenta;

SELECT *
FROM public.tipos_cuenta
ORDER BY id_tipo_cuenta ASC;


-- 2. Eliminar datos dependientes de la tabla tipos_cuenta
DELETE FROM public.pagos;
DELETE FROM public.transacciones;
DELETE FROM public.cuentas;


-- 3. Eliminar datos de la tabla tipos_cuenta
DELETE FROM public.tipos_cuenta;


-- 4. Confirmar que se eliminaron
SELECT COUNT(*) AS total_despues_eliminar
FROM public.tipos_cuenta;


-- 5. Restaurar datos desde el respaldo base
INSERT INTO public.tipos_cuenta (
    id_tipo_cuenta,
    nombre_tipo,
    descripcion,
    estado
)
SELECT
    id_tipo_cuenta,
    nombre_tipo,
    descripcion,
    estado
FROM backup_gba.tipos_cuenta_base
WHERE id_respaldo_base = 1;


-- 6. Restaurar datos dependientes desde el respaldo base
INSERT INTO public.cuentas (
    id_cuenta,
    id_cliente,
    id_tipo_cuenta,
    numero_cuenta,
    saldo,
    estado,
    fecha_apertura
)
SELECT
    id_cuenta,
    id_cliente,
    id_tipo_cuenta,
    numero_cuenta,
    saldo,
    estado,
    fecha_apertura
FROM backup_gba.cuentas_base
WHERE id_respaldo_base = 1;

INSERT INTO public.transacciones (
    id_transaccion,
    codigo_transaccion,
    tipo_transaccion,
    id_cuenta_origen,
    id_cuenta_destino,
    monto,
    estado,
    descripcion,
    fecha_transaccion
)
SELECT
    id_transaccion,
    codigo_transaccion,
    tipo_transaccion,
    id_cuenta_origen,
    id_cuenta_destino,
    monto,
    estado,
    descripcion,
    fecha_transaccion
FROM backup_gba.transacciones_base
WHERE id_respaldo_base = 1;

INSERT INTO public.pagos (
    id_pago,
    codigo_pago,
    id_cuenta,
    id_servicio,
    referencia,
    monto,
    estado,
    fecha_pago
)
SELECT
    id_pago,
    codigo_pago,
    id_cuenta,
    id_servicio,
    referencia,
    monto,
    estado,
    fecha_pago
FROM backup_gba.pagos_base
WHERE id_respaldo_base = 1;


-- 7. Reajustar secuencias SERIAL
SELECT setval(
    'tipos_cuenta_id_tipo_cuenta_seq',
    COALESCE((SELECT MAX(id_tipo_cuenta) FROM public.tipos_cuenta), 1),
    true
);

SELECT setval(
    'cuentas_id_cuenta_seq',
    COALESCE((SELECT MAX(id_cuenta) FROM public.cuentas), 1),
    true
);

SELECT setval(
    'transacciones_id_transaccion_seq',
    COALESCE((SELECT MAX(id_transaccion) FROM public.transacciones), 1),
    true
);

SELECT setval(
    'pagos_id_pago_seq',
    COALESCE((SELECT MAX(id_pago) FROM public.pagos), 1),
    true
);


-- 8. Verificar recuperación
SELECT COUNT(*) AS total_despues_recuperar
FROM public.tipos_cuenta;















