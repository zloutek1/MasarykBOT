-- Table: muni.faculties

-- DROP TABLE muni.faculties;

CREATE TABLE muni.faculties
(
    id integer NOT NULL,
    code character varying COLLATE pg_catalog."default" NOT NULL,
    name character varying COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    edited_at timestamp without time zone,
    deleted_at timestamp without time zone,
    CONSTRAINT faculties_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE muni.faculties
    OWNER to masaryk;