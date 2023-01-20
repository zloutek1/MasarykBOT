-- Table: server.emojis

-- DROP TABLE server.emojis;

CREATE TABLE server.emojis
(
    id bigint NOT NULL,
    name character varying COLLATE pg_catalog."default" NOT NULL,
    url character varying COLLATE pg_catalog."default",
    animated boolean,
    created_at timestamp with time zone DEFAULT now(),
    edited_at timestamp with time zone,
    deleted_at timestamp with time zone,
    CONSTRAINT emojis_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE server.emojis
    OWNER to masaryk;