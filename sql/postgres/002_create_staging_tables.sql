-- sql/postgres/002_create_staging_tables.sql
-- Crea las tablas staging iniciales para Parquet analíticos.

CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.visit_index (
    load_id text NOT NULL REFERENCES audit.load_control (load_id),
    loaded_at timestamptz NOT NULL DEFAULT now(),
    source_start_date date NOT NULL,
    source_end_date date NOT NULL,
    source_file text NOT NULL,
    source_file_hash text NOT NULL,

    patient_guid text,
    patient_id_num text,
    patient_last_name text,
    patient_first_name text,
    pat_visit_id bigint NOT NULL,
    pat_visit_guid text,
    visit_datetime timestamp without time zone,
    has_fvl boolean,
    has_dlco boolean,
    has_pleth boolean,
    has_mip_mep boolean,
    has_methacholine boolean,
    test_count bigint,

    CONSTRAINT ux_visit_index_load_visit
        UNIQUE (load_id, pat_visit_id)
);

CREATE TABLE IF NOT EXISTS staging.fvl_analytics (
    load_id text NOT NULL REFERENCES audit.load_control (load_id),
    loaded_at timestamptz NOT NULL DEFAULT now(),
    source_start_date date NOT NULL,
    source_end_date date NOT NULL,
    source_file text NOT NULL,
    source_file_hash text NOT NULL,
    pat_visit_id bigint NOT NULL
);

CREATE TABLE IF NOT EXISTS staging.dlco_analytics (
    load_id text NOT NULL REFERENCES audit.load_control (load_id),
    loaded_at timestamptz NOT NULL DEFAULT now(),
    source_start_date date NOT NULL,
    source_end_date date NOT NULL,
    source_file text NOT NULL,
    source_file_hash text NOT NULL,
    pat_visit_id bigint NOT NULL
);

CREATE TABLE IF NOT EXISTS staging.pleth_analytics (
    load_id text NOT NULL REFERENCES audit.load_control (load_id),
    loaded_at timestamptz NOT NULL DEFAULT now(),
    source_start_date date NOT NULL,
    source_end_date date NOT NULL,
    source_file text NOT NULL,
    source_file_hash text NOT NULL,
    pat_visit_id bigint NOT NULL
);

CREATE TABLE IF NOT EXISTS staging.mip_mep_analytics (
    load_id text NOT NULL REFERENCES audit.load_control (load_id),
    loaded_at timestamptz NOT NULL DEFAULT now(),
    source_start_date date NOT NULL,
    source_end_date date NOT NULL,
    source_file text NOT NULL,
    source_file_hash text NOT NULL,
    pat_visit_id bigint NOT NULL
);

CREATE TABLE IF NOT EXISTS staging.methacholine_analytics (
    load_id text NOT NULL REFERENCES audit.load_control (load_id),
    loaded_at timestamptz NOT NULL DEFAULT now(),
    source_start_date date NOT NULL,
    source_end_date date NOT NULL,
    source_file text NOT NULL,
    source_file_hash text NOT NULL,
    pat_visit_id bigint NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_fvl_analytics_load_visit
    ON staging.fvl_analytics (load_id, pat_visit_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_dlco_analytics_load_visit
    ON staging.dlco_analytics (load_id, pat_visit_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_pleth_analytics_load_visit
    ON staging.pleth_analytics (load_id, pat_visit_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_mip_mep_analytics_load_visit
    ON staging.mip_mep_analytics (load_id, pat_visit_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_methacholine_analytics_load_visit
    ON staging.methacholine_analytics (load_id, pat_visit_id);

CREATE INDEX IF NOT EXISTS ix_visit_index_pat_visit_id
    ON staging.visit_index (pat_visit_id);

CREATE INDEX IF NOT EXISTS ix_visit_index_visit_datetime
    ON staging.visit_index (visit_datetime);

CREATE INDEX IF NOT EXISTS ix_fvl_analytics_pat_visit_id
    ON staging.fvl_analytics (pat_visit_id);

CREATE INDEX IF NOT EXISTS ix_dlco_analytics_pat_visit_id
    ON staging.dlco_analytics (pat_visit_id);

CREATE INDEX IF NOT EXISTS ix_pleth_analytics_pat_visit_id
    ON staging.pleth_analytics (pat_visit_id);

CREATE INDEX IF NOT EXISTS ix_mip_mep_analytics_pat_visit_id
    ON staging.mip_mep_analytics (pat_visit_id);

CREATE INDEX IF NOT EXISTS ix_methacholine_analytics_pat_visit_id
    ON staging.methacholine_analytics (pat_visit_id);
