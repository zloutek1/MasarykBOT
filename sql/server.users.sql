-- Table: server.users

-- DROP TABLE server.users;

CREATE TABLE server.users
(
    id bigint NOT NULL,
    names character varying[] COLLATE pg_catalog."default" NOT NULL,
    avarar_url character varying(100) COLLATE pg_catalog."default",
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    edited_at timestamp with time zone,
    deleted_at timestamp with time zone,
    CONSTRAINT users_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE server.users
    OWNER to masaryk;
