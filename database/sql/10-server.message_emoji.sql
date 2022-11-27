-- Table: server.message_emoji

-- DROP TABLE server.message_emoji;

CREATE TABLE server.message_emoji
(
    message_id bigint NOT NULL,
    emoji_id bigint NOT NULL,
    count integer NOT NULL,
    edited_at timestamp without time zone,
    CONSTRAINT message_emoji_fkey_emoji FOREIGN KEY (emoji_id)
        REFERENCES server.emojis (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT message_emoji_fkey_message FOREIGN KEY (message_id)
        REFERENCES server.messages (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE server.message_emoji
    OWNER to masaryk;
-- Index: fki_message_emojis_fkey_emoji

-- DROP INDEX server.fki_message_emojis_fkey_emoji;

CREATE INDEX fki_message_emojis_fkey_emoji
    ON server.message_emoji USING btree
    (emoji_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_message_emojis_fkey_message

-- DROP INDEX server.fki_message_emojis_fkey_message;

CREATE INDEX fki_message_emojis_fkey_message
    ON server.message_emoji USING btree
    (message_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: idx_message_emojis_unique

-- DROP INDEX server.idx_message_emojis_unique;

CREATE UNIQUE INDEX idx_message_emojis_unique
    ON server.message_emoji USING btree
    (message_id ASC NULLS LAST, emoji_id ASC NULLS LAST)
    TABLESPACE pg_default;