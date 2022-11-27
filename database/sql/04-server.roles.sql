-- Table: server.roles

-- DROP TABLE server.roles;

CREATE TABLE server.roles
(
    guild_id bigint NOT NULL,
    id bigint NOT NULL,
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    color character varying(8) COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    edited_at timestamp without time zone,
    deleted_at timestamp without time zone,
    CONSTRAINT roles_pkey PRIMARY KEY (id),
    CONSTRAINT roles_fkey_guild FOREIGN KEY (guild_id)
        REFERENCES server.guilds (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE server.roles
    OWNER to masaryk;
