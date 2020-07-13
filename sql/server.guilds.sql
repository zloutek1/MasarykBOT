-- Table: server.guilds

-- DROP TABLE server.guilds;

CREATE TABLE server.guilds
(
    id bigint NOT NULL,
    name character varying(30) COLLATE pg_catalog."default" NOT NULL,
    icon_url character varying(100) COLLATE pg_catalog."default",
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    modified_at timestamp with time zone,
    deleted_at timestamp with time zone,
    CONSTRAINT guilds_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE server.guilds
    OWNER to masaryk;
