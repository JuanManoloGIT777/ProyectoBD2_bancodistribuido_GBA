-- =========================================================
-- CONSULTA 1: HISTORIAL DE MOVIMIENTOS POR CUENTA
-- Sirve para ver depósitos, retiros, transferencias y pagos
-- donde participa una cuenta.
-- =========================================================

-- Consulta normal
SELECT
    t.codigo_transaccion,
    t.tipo_transaccion,
    co.numero_cuenta AS cuenta_origen,
    cd.numero_cuenta AS cuenta_destino,
    t.monto,
    t.estado,
    t.fecha_transaccion
FROM public.transacciones t
LEFT JOIN public.cuentas co ON t.id_cuenta_origen = co.id_cuenta
LEFT JOIN public.cuentas cd ON t.id_cuenta_destino = cd.id_cuenta
WHERE co.numero_cuenta = '1000010001'
   OR cd.numero_cuenta = '1000010001'
ORDER BY t.fecha_transaccion DESC;


-- Índices para optimizar
CREATE INDEX IF NOT EXISTS idx_cuentas_numero_cuenta
ON public.cuentas (numero_cuenta);

CREATE INDEX IF NOT EXISTS idx_transacciones_origen_fecha
ON public.transacciones (id_cuenta_origen, fecha_transaccion DESC);

CREATE INDEX IF NOT EXISTS idx_transacciones_destino_fecha
ON public.transacciones (id_cuenta_destino, fecha_transaccion DESC);


-- Análisis de rendimiento
EXPLAIN ANALYZE
SELECT
    t.codigo_transaccion,
    t.tipo_transaccion,
    co.numero_cuenta AS cuenta_origen,
    cd.numero_cuenta AS cuenta_destino,
    t.monto,
    t.estado,
    t.fecha_transaccion
FROM public.transacciones t
LEFT JOIN public.cuentas co ON t.id_cuenta_origen = co.id_cuenta
LEFT JOIN public.cuentas cd ON t.id_cuenta_destino = cd.id_cuenta
WHERE co.numero_cuenta = '1000010001'
   OR cd.numero_cuenta = '1000010001'
ORDER BY t.fecha_transaccion DESC;



-- =========================================================
-- CONSULTA 2: ESTADO DE CUENTA DE UN CLIENTE
-- Sirve para ver las cuentas, tipo de cuenta y saldo de un cliente.
-- =========================================================

-- Consulta normal
SELECT
    cl.dpi,
    cl.nombres,
    cl.apellidos,
    c.numero_cuenta,
    tc.nombre_tipo AS tipo_cuenta,
    c.saldo,
    c.estado,
    c.fecha_apertura
FROM public.clientes cl
INNER JOIN public.cuentas c ON cl.id_cliente = c.id_cliente
INNER JOIN public.tipos_cuenta tc ON c.id_tipo_cuenta = tc.id_tipo_cuenta
WHERE cl.dpi = '78654326789057'
ORDER BY c.fecha_apertura DESC;


-- Índices para optimizar
CREATE INDEX IF NOT EXISTS idx_clientes_dpi
ON public.clientes (dpi);

CREATE INDEX IF NOT EXISTS idx_cuentas_cliente_fecha
ON public.cuentas (id_cliente, fecha_apertura DESC);


-- Análisis de rendimiento
EXPLAIN ANALYZE
SELECT
    cl.dpi,
    cl.nombres,
    cl.apellidos,
    c.numero_cuenta,
    tc.nombre_tipo AS tipo_cuenta,
    c.saldo,
    c.estado,
    c.fecha_apertura
FROM public.clientes cl
INNER JOIN public.cuentas c ON cl.id_cliente = c.id_cliente
INNER JOIN public.tipos_cuenta tc ON c.id_tipo_cuenta = tc.id_tipo_cuenta
WHERE cl.dpi = '78654326789057'
ORDER BY c.fecha_apertura DESC;



-- =========================================================
-- CONSULTA 3: AUDITORÍA POR OPERACIÓN
-- Sirve para revisar eventos específicos del sistema.
-- =========================================================

-- Consulta normal
SELECT
    a.fecha,
    COALESCE(u.usuario, 'Sistema BD') AS usuario,
    a.modulo,
    a.operacion,
    a.descripcion
FROM public.auditoria a
LEFT JOIN public.usuarios u ON a.id_usuario = u.id_usuario
WHERE a.modulo = 'Transacciones'
  AND a.operacion = 'RETIRO'
ORDER BY a.fecha DESC;


-- Índice para optimizar
CREATE INDEX IF NOT EXISTS idx_auditoria_modulo_operacion_fecha
ON public.auditoria (modulo, operacion, fecha DESC);


-- Análisis de rendimiento
EXPLAIN ANALYZE
SELECT
    a.fecha,
    COALESCE(u.usuario, 'Sistema BD') AS usuario,
    a.modulo,
    a.operacion,
    a.descripcion
FROM public.auditoria a
LEFT JOIN public.usuarios u ON a.id_usuario = u.id_usuario
WHERE a.modulo = 'Transacciones'
  AND a.operacion = 'RETIRO'
ORDER BY a.fecha DESC;



-- =========================================================
-- CONSULTA 4: REPORTE DE TRANSACCIONES POR TIPO
-- Sirve para resumir las operaciones bancarias por categoría.
-- =========================================================

-- Consulta normal
SELECT
    tipo_transaccion,
    COUNT(*) AS cantidad_operaciones,
    SUM(monto) AS monto_total,
    ROUND(AVG(monto), 2) AS monto_promedio
FROM public.transacciones
GROUP BY tipo_transaccion
ORDER BY monto_total DESC;


-- Índice para optimizar
CREATE INDEX IF NOT EXISTS idx_transacciones_fecha_tipo
ON public.transacciones (fecha_transaccion DESC, tipo_transaccion);


-- Análisis de rendimiento
EXPLAIN ANALYZE
SELECT
    tipo_transaccion,
    COUNT(*) AS cantidad_operaciones,
    SUM(monto) AS monto_total,
    ROUND(AVG(monto), 2) AS monto_promedio
FROM public.transacciones
GROUP BY tipo_transaccion
ORDER BY monto_total DESC;




-- =========================================================
-- CONSULTA 5: CLIENTES CON MAYOR MOVIMIENTO BANCARIO
-- Sirve para identificar clientes con más actividad financiera.
-- =========================================================

-- Consulta normal
SELECT
    cl.dpi,
    cl.nombres,
    cl.apellidos,
    COUNT(t.id_transaccion) AS cantidad_transacciones,
    SUM(t.monto) AS monto_total_movido
FROM public.clientes cl
INNER JOIN public.cuentas c ON cl.id_cliente = c.id_cliente
INNER JOIN public.transacciones t 
    ON c.id_cuenta = t.id_cuenta_origen
    OR c.id_cuenta = t.id_cuenta_destino
GROUP BY
    cl.dpi,
    cl.nombres,
    cl.apellidos
ORDER BY monto_total_movido DESC;


-- Índices para optimizar
CREATE INDEX IF NOT EXISTS idx_cuentas_cliente_movimiento
ON public.cuentas (id_cliente, id_cuenta);

CREATE INDEX IF NOT EXISTS idx_transacciones_origen_movimiento
ON public.transacciones (id_cuenta_origen);

CREATE INDEX IF NOT EXISTS idx_transacciones_destino_movimiento
ON public.transacciones (id_cuenta_destino);


-- Análisis de rendimiento
EXPLAIN ANALYZE
SELECT
    cl.dpi,
    cl.nombres,
    cl.apellidos,
    COUNT(t.id_transaccion) AS cantidad_transacciones,
    SUM(t.monto) AS monto_total_movido
FROM public.clientes cl
INNER JOIN public.cuentas c ON cl.id_cliente = c.id_cliente
INNER JOIN public.transacciones t 
    ON c.id_cuenta = t.id_cuenta_origen
    OR c.id_cuenta = t.id_cuenta_destino
GROUP BY
    cl.dpi,
    cl.nombres,
    cl.apellidos
ORDER BY monto_total_movido DESC;






