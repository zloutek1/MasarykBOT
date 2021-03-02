-- Table: server.message_emotes

-- DROP TABLE server.message_emotes;

CREATE TABLE server.message_emotes
(
    message_id bigint NOT NULL,
    emoji_id bigint NOT NULL,
    count integer NOT NULL,
    CONSTRAINT message_emotes_fkey_emoji FOREIGN KEY (emoji_id)
        REFERENCES server.emojis (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT message_emotes_fkey_message FOREIGN KEY (message_id)
        REFERENCES server.messages (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE server.message_emotes
    OWNER to masaryk;
-- Index: fki_message_emotes_fkey_emoji

-- DROP INDEX server.fki_message_emotes_fkey_emoji;

CREATE INDEX fki_message_emotes_fkey_emoji
    ON server.message_emotes USING btree
    (emoji_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_message_emotes_fkey_message

-- DROP INDEX server.fki_message_emotes_fkey_message;

CREATE INDEX fki_message_emotes_fkey_message
    ON server.message_emotes USING btree
    (message_id ASC NULLS LAST)
    TABLESPACE pg_default;
