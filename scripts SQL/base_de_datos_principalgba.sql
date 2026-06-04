-- =========================================================
-- BASE DE DATOS: Proyecto_Banco_Distribuido
-- SISTEMA: GBA CREDOMATIC
-- =========================================================

-- =========================================================
-- 1. TABLA DE ROLES
-- =========================================================

CREATE TABLE IF NOT EXISTS roles (
    id_rol SERIAL PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 2. TABLA DE USUARIOS INTERNOS
-- =========================================================

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario SERIAL PRIMARY KEY,
    id_rol INTEGER NOT NULL,
    nombre_completo VARCHAR(150) NOT NULL,
    usuario VARCHAR(80) NOT NULL UNIQUE,
    correo VARCHAR(120) NOT NULL UNIQUE,
    clave VARCHAR(255) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_usuario_rol
        FOREIGN KEY (id_rol)
        REFERENCES roles(id_rol)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- =========================================================
-- 3. TABLA DE CLIENTES
-- =========================================================

CREATE TABLE IF NOT EXISTS clientes (
    id_cliente SERIAL PRIMARY KEY,
    dpi VARCHAR(20) NOT NULL UNIQUE,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    correo VARCHAR(120),
    direccion TEXT,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 4. TABLA DE TIPOS DE CUENTA
-- =========================================================

CREATE TABLE IF NOT EXISTS tipos_cuenta (
    id_tipo_cuenta SERIAL PRIMARY KEY,
    nombre_tipo VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO'
);

-- =========================================================
-- 5. TABLA DE CUENTAS BANCARIAS
-- =========================================================

CREATE TABLE IF NOT EXISTS cuentas (
    id_cuenta SERIAL PRIMARY KEY,
    id_cliente INTEGER NOT NULL,
    id_tipo_cuenta INTEGER NOT NULL,
    numero_cuenta VARCHAR(30) NOT NULL UNIQUE,
    saldo NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVA',
    fecha_apertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_cuenta_cliente
        FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_cuenta_tipo
        FOREIGN KEY (id_tipo_cuenta)
        REFERENCES tipos_cuenta(id_tipo_cuenta)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_saldo_no_negativo
        CHECK (saldo >= 0)
);

-- =========================================================
-- 6. TABLA DE TRANSACCIONES
-- =========================================================

CREATE TABLE IF NOT EXISTS transacciones (
    id_transaccion SERIAL PRIMARY KEY,
    codigo_transaccion VARCHAR(40) NOT NULL UNIQUE,
    tipo_transaccion VARCHAR(30) NOT NULL,
    id_cuenta_origen INTEGER,
    id_cuenta_destino INTEGER,
    monto NUMERIC(12,2) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'COMPLETADA',
    descripcion TEXT,
    fecha_transaccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_transaccion_origen
        FOREIGN KEY (id_cuenta_origen)
        REFERENCES cuentas(id_cuenta)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_transaccion_destino
        FOREIGN KEY (id_cuenta_destino)
        REFERENCES cuentas(id_cuenta)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_monto_transaccion
        CHECK (monto > 0),

    CONSTRAINT chk_tipo_transaccion
        CHECK (tipo_transaccion IN ('DEPOSITO', 'RETIRO', 'TRANSFERENCIA', 'PAGO_SERVICIO'))
);

-- =========================================================
-- 7. TABLA DE SERVICIOS
-- =========================================================

CREATE TABLE IF NOT EXISTS servicios (
    id_servicio SERIAL PRIMARY KEY,
    nombre_servicio VARCHAR(80) NOT NULL UNIQUE,
    descripcion TEXT,
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO'
);

-- =========================================================
-- 8. TABLA DE PAGOS DE SERVICIOS
-- =========================================================

CREATE TABLE IF NOT EXISTS pagos (
    id_pago SERIAL PRIMARY KEY,
    codigo_pago VARCHAR(40) NOT NULL UNIQUE,
    id_cuenta INTEGER NOT NULL,
    id_servicio INTEGER NOT NULL,
    referencia VARCHAR(100) NOT NULL,
    monto NUMERIC(12,2) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'PAGADO',
    fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_pago_cuenta
        FOREIGN KEY (id_cuenta)
        REFERENCES cuentas(id_cuenta)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_pago_servicio
        FOREIGN KEY (id_servicio)
        REFERENCES servicios(id_servicio)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_monto_pago
        CHECK (monto > 0)
);

-- =========================================================
-- 9. TABLA DE AUDITORÍA
-- =========================================================

CREATE TABLE IF NOT EXISTS auditoria (
    id_auditoria SERIAL PRIMARY KEY,
    id_usuario INTEGER,
    modulo VARCHAR(80) NOT NULL,
    operacion VARCHAR(80) NOT NULL,
    descripcion TEXT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_auditoria_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- =========================================================
-- 10. TABLA DE SOLICITUDES DE CONTACTO PÚBLICAS
-- =========================================================

CREATE TABLE IF NOT EXISTS solicitudes_contacto (
    id_solicitud SERIAL PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    correo VARCHAR(120) NOT NULL,
    mensaje TEXT NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 11. INSERCIÓN DE ROLES BASE
-- =========================================================

INSERT INTO roles (nombre_rol, descripcion)
VALUES 
('ADMINISTRADOR', 'Gestiona usuarios, seguridad, reportes, auditoría y configuración del sistema.'),
('CAJERO', 'Registra clientes, crea cuentas, procesa transacciones y pagos.'),
('AUDITOR', 'Consulta información, revisa eventos y supervisa operaciones del sistema.')
ON CONFLICT (nombre_rol) DO NOTHING;

-- =========================================================
-- 12. INSERCIÓN DE TIPOS DE CUENTA
-- =========================================================

INSERT INTO tipos_cuenta (nombre_tipo, descripcion)
VALUES
('AHORRO', 'Cuenta de ahorro para clientes individuales.'),
('MONETARIA', 'Cuenta monetaria para operaciones frecuentes.'),
('EMPRESARIAL', 'Cuenta bancaria para empresas y negocios.')
ON CONFLICT (nombre_tipo) DO NOTHING;

-- =========================================================
-- 13. INSERCIÓN DE SERVICIOS BASE
-- =========================================================

INSERT INTO servicios (nombre_servicio, descripcion)
VALUES
('ENERGIA ELECTRICA', 'Pago de servicio de energía eléctrica.'),
('AGUA POTABLE', 'Pago de servicio de agua potable.'),
('INTERNET', 'Pago de servicio de internet residencial o empresarial.'),
('TELEFONIA', 'Pago de servicio de telefonía.')
ON CONFLICT (nombre_servicio) DO NOTHING;

-- =========================================================
-- 14. ÍNDICES
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_usuarios_usuario
ON usuarios(usuario);

CREATE INDEX IF NOT EXISTS idx_usuarios_correo
ON usuarios(correo);

CREATE INDEX IF NOT EXISTS idx_clientes_dpi
ON clientes(dpi);

CREATE INDEX IF NOT EXISTS idx_cuentas_numero
ON cuentas(numero_cuenta);

CREATE INDEX IF NOT EXISTS idx_transacciones_fecha
ON transacciones(fecha_transaccion);

CREATE INDEX IF NOT EXISTS idx_auditoria_fecha
ON auditoria(fecha);

CREATE INDEX IF NOT EXISTS idx_auditoria_usuario
ON auditoria(id_usuario);