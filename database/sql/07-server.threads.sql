-- Table: server.threads

-- DROP TABLE server.threads;

CREATE TABLE server.threads
(
    parent_id bigint,
    id bigint NOT NULL,
    "name" character varying(100) COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    archived_at timestamp with time zone,
    edited_at timestamp with time zone,
    deleted_at timestamp with time zone,
    CONSTRAINT threads_pkey PRIMARY KEY (id),
    CONSTRAINT threads_fkey_channel FOREIGN KEY (parent_id)
        REFERENCES server.channels (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE server.threads
    OWNER to masaryk;
-- Index: fki_threads_fkey_channel

-- DROP INDEX server.fki_threads_fkey_channel;

CREATE INDEX fki_threads_fkey_channel
    ON server.threads USING btree
    (parent_id ASC NULLS LAST)
    TABLESPACE pg_default;
