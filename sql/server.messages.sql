-- Table: server.messages

-- DROP TABLE server.messages;

CREATE TABLE server.messages
(
    channel_id bigint NOT NULL,
    author_id bigint NOT NULL,
    id bigint NOT NULL,
    content text COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    edited_at timestamp without time zone,
    deleted_at timestamp without time zone,
    CONSTRAINT messages_pkey PRIMARY KEY (id),
    CONSTRAINT messages_fkey_channel FOREIGN KEY (channel_id)
        REFERENCES server.channels (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT messages_fkey_user FOREIGN KEY (author_id)
        REFERENCES server.users (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)

TABLESPACE pg_default;

ALTER TABLE server.messages
    OWNER to masaryk;
-- Index: fki_messages_fkey_channel

-- DROP INDEX server.fki_messages_fkey_channel;

CREATE INDEX fki_messages_fkey_channel
    ON server.messages USING btree
    (channel_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_messages_fkey_user

-- DROP INDEX server.fki_messages_fkey_user;

CREATE INDEX fki_messages_fkey_user
    ON server.messages USING btree
    (author_id ASC NULLS LAST)
    TABLESPACE pg_default;
