-- Table: server.emojis

-- DROP TABLE server.emojis;

CREATE TABLE server.emojis
(
    id bigint NOT NULL,
    name character varying COLLATE pg_catalog."default" NOT NULL,
    url character varying COLLATE pg_catalog."default",
    created_at timestamp without time zone,
    animated boolean,
    CONSTRAINT emojis_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE server.emojis
    OWNER to masaryk_dev;