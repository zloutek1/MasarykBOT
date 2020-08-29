-- Table: server.emojis

-- DROP TABLE server.emojis;

CREATE TABLE server.emojis
(
    message_id bigint NOT NULL,
    name text COLLATE pg_catalog."default",
    count integer,
    CONSTRAINT emojis_fkey_message FOREIGN KEY (message_id)
        REFERENCES server.messages (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE server.emojis
    OWNER to masaryk;
-- Index: emojis_idx_unique

-- DROP INDEX server.emojis_idx_unique;

CREATE UNIQUE INDEX emojis_idx_unique
    ON server.emojis USING btree
    (message_id ASC NULLS LAST, name COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
