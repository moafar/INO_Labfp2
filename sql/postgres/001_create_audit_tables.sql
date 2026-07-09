-- sql/postgres/001_create_audit_tables.sql
-- Crea las tablas mínimas de auditoría para cargas a PostgreSQL staging.

CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS audit.load_control (
    load_id text PRIMARY KEY,
    pipeline_name text NOT NULL,
    target_schema text NOT NULL,
    target_table text NOT NULL,
    source_system text NOT NULL,
    source_start_date date NOT NULL,
    source_end_date date NOT NULL,
    source_file text NOT NULL,
    source_file_hash text NOT NULL,
    rows_read bigint NOT NULL DEFAULT 0,
    rows_loaded bigint NOT NULL DEFAULT 0,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    status text NOT NULL,
    error_message text
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_load_control_target_file_hash
    ON audit.load_control (
        target_schema,
        target_table,
        source_file_hash
    );

CREATE INDEX IF NOT EXISTS ix_load_control_target
    ON audit.load_control (target_schema, target_table);

CREATE INDEX IF NOT EXISTS ix_load_control_window
    ON audit.load_control (source_start_date, source_end_date);
