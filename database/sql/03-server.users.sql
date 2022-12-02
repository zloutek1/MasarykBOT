-- Table: server.users

-- DROP TABLE server.users;

CREATE TABLE server.users
(
    id bigint NOT NULL,
    name character varying COLLATE pg_catalog."default" NOT NULL,
    avatar_url text COLLATE pg_catalog."default",
    is_bot boolean NOT NULL DEFAULT false,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    edited_at timestamp with time zone,
    deleted_at timestamp with time zone,
    CONSTRAINT users_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE server.users
    OWNER to masaryk;
