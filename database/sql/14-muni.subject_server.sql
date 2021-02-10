-- Table: muni.subject_server

-- DROP TABLE muni.subject_server;

CREATE TABLE muni.subject_server
(
    faculty character varying COLLATE pg_catalog."default" NOT NULL,
    code character varying COLLATE pg_catalog."default" NOT NULL,
    guild_id bigint NOT NULL,
    category_id bigint,
    channel_id bigint NOT NULL,
    voice_channel_id bigint,
    CONSTRAINT subject_server_fkey_channel FOREIGN KEY (channel_id)
        REFERENCES server.channels (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT subject_server_fkey_code FOREIGN KEY (code, faculty)
        REFERENCES muni.subjects (code, faculty) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT subject_server_fkey_guild FOREIGN KEY (guild_id)
        REFERENCES server.guilds (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE muni.subject_server
    OWNER to masaryk;
-- Index: fki_subject_server_fkey_channel

-- DROP INDEX muni.fki_subject_server_fkey_channel;

CREATE INDEX fki_subject_server_fkey_channel
    ON muni.subject_server USING btree
    (channel_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_subject_server_fkey_code

-- DROP INDEX muni.fki_subject_server_fkey_code;

CREATE INDEX fki_subject_server_fkey_code
    ON muni.subject_server USING btree
    (code COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_subject_server_fkey_guild

-- DROP INDEX muni.fki_subject_server_fkey_guild;

CREATE INDEX fki_subject_server_fkey_guild
    ON muni.subject_server USING btree
    (guild_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: subject_server_idx_unique

-- DROP INDEX muni.subject_server_idx_unique;

CREATE UNIQUE INDEX subject_server_idx_unique
    ON muni.subject_server USING btree
    (code COLLATE pg_catalog."default" ASC NULLS LAST, guild_id ASC NULLS LAST)
    TABLESPACE pg_default;