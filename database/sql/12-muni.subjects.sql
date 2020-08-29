-- Table: muni.subjects

-- DROP TABLE muni.subjects;

CREATE TABLE muni.subjects
(
    faculty character varying COLLATE pg_catalog."default" NOT NULL,
    code character varying COLLATE pg_catalog."default" NOT NULL,
    name character varying COLLATE pg_catalog."default" NOT NULL,
    url text COLLATE pg_catalog."default" NOT NULL,
    terms character varying[] COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    edited_at timestamp without time zone,
    deleted_at timestamp without time zone,
    CONSTRAINT subjects_pkey PRIMARY KEY (code)
)

TABLESPACE pg_default;

ALTER TABLE muni.subjects
    OWNER to masaryk;
