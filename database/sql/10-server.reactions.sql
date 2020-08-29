-- Table: server.reactions

-- DROP TABLE server.reactions;

CREATE TABLE server.reactions
(
    message_id bigint NOT NULL,
    name text COLLATE pg_catalog."default",
    member_ids bigint[],
    CONSTRAINT reactions_fkey_message FOREIGN KEY (message_id)
        REFERENCES server.messages (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE server.reactions
    OWNER to masaryk;
-- Index: fki_reactions_fkey_message

-- DROP INDEX server.fki_reactions_fkey_message;

CREATE INDEX fki_reactions_fkey_message
    ON server.reactions USING btree
    (message_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: reactions_idx_unique

-- DROP INDEX server.reactions_idx_unique;

CREATE UNIQUE INDEX reactions_idx_unique
    ON server.reactions USING btree
    (message_id ASC NULLS LAST, name COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
