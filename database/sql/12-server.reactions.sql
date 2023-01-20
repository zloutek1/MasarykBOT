-- Table: server.reactions

-- DROP TABLE server.reactions;

CREATE TABLE server.reactions
(
    message_id bigint NOT NULL,
    emoji_id bigint NOT NULL,
    member_ids bigint[] NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    edited_at timestamp with time zone,
    deleted_at timestamp with time zone,
    CONSTRAINT reactions_fkey_emoji FOREIGN KEY (emoji_id)
        REFERENCES server.emojis (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT reactions_fkey_message FOREIGN KEY (message_id)
        REFERENCES server.messages (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE server.reactions
    OWNER to masaryk;
-- Index: fki_reactions_fkey_emoji

-- DROP INDEX server.fki_reactions_fkey_emoji;

CREATE INDEX fki_reactions_fkey_emoji
    ON server.reactions USING btree
    (emoji_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_reactions_fkey_message

-- DROP INDEX server.fki_reactions_fkey_message;

CREATE INDEX fki_reactions_fkey_message
    ON server.reactions USING btree
    (message_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: idx_reactions_unique

-- DROP INDEX server.idx_reactions_unique;

CREATE UNIQUE INDEX idx_reactions_unique
    ON server.reactions USING btree
    (message_id ASC NULLS LAST, emoji_id ASC NULLS LAST)
    TABLESPACE pg_default;

-- Trigger: update_emojiboard