-- Table: server.users

-- DROP TABLE server.users;

CREATE TABLE server.users
(
    id bigint NOT NULL,
    names character varying[] COLLATE pg_catalog."default" NOT NULL,
    avatar_url character varying(100) COLLATE pg_catalog."default",
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    edited_at timestamp without time zone,
    deleted_at timestamp without time zone,
    CONSTRAINT users_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE server.users
    OWNER to masaryk;
