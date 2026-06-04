-- =========================================================
-- CONFIGURACIÓN WAL / PITR - POSTGRESQL
-- Descripción:
-- Activa configuración necesaria para archivado de WAL,
-- base para recuperación a punto en el tiempo.
-- =========================================================

ALTER SYSTEM SET wal_level = 'replica';

ALTER SYSTEM SET archive_mode = 'on';

ALTER SYSTEM SET archive_timeout = '60s';


-- CONFIGURACI
ALTER SYSTEM SET archive_command = 'test ! -f /var/lib/postgresql/wal_archive/%f && cp %p /var/lib/postgresql/wal_archive/%f';

SELECT pg_reload_conf();

