-- Table: muni.faculties

-- DROP TABLE IF EXISTS muni.faculties;

CREATE TABLE IF NOT EXISTS muni.faculties
(
    id integer NOT NULL,
    code character varying COLLATE pg_catalog."default" NOT NULL,
    name character varying COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    edited_at timestamp without time zone,
    deleted_at timestamp without time zone,
    CONSTRAINT faculties_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS muni.faculties
    OWNER to masaryk;
-- Index: faculties_code_idx_unique

-- DROP INDEX IF EXISTS muni.faculties_code_idx_unique;

CREATE UNIQUE INDEX IF NOT EXISTS faculties_code_idx_unique
    ON muni.faculties USING btree
    (code COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;