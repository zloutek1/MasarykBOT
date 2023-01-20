-- Table: muni.course_guild

-- DROP TABLE muni.course_guild;

CREATE TABLE muni.course_guild
(
    faculty character varying COLLATE pg_catalog."default" NOT NULL,
    code character varying COLLATE pg_catalog."default" NOT NULL,
    guild_id bigint NOT NULL,
    category_id bigint,
    channel_id bigint NOT NULL,
    CONSTRAINT course_guild_fkey_channel FOREIGN KEY (channel_id)
        REFERENCES server.channels (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT course_guild_fkey_code FOREIGN KEY (code, faculty)
        REFERENCES muni.courses (code, faculty) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT course_guild_fkey_guild FOREIGN KEY (guild_id)
        REFERENCES server.guilds (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE muni.course_guild
    OWNER to masaryk;
-- Index: fki_course_guild_fkey_channel

-- DROP INDEX muni.fki_course_guild_fkey_channel;

CREATE INDEX fki_course_guild_fkey_channel
    ON muni.course_guild USING btree
    (channel_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_course_guild_fkey_code

-- DROP INDEX muni.fki_course_guild_fkey_code;

CREATE INDEX fki_course_guild_fkey_code
    ON muni.course_guild USING btree
    (code COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_course_guild_fkey_guild

-- DROP INDEX muni.fki_course_guild_fkey_guild;

CREATE INDEX fki_course_guild_fkey_guild
    ON muni.course_guild USING btree
    (guild_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: course_guild_idx_unique

-- DROP INDEX muni.course_guild_idx_unique;

CREATE UNIQUE INDEX course_guild_idx_unique
    ON muni.course_guild USING btree
    (faculty COLLATE pg_catalog."default" ASC NULLS LAST, code COLLATE pg_catalog."default" ASC NULLS LAST, guild_id ASC NULLS LAST)
    TABLESPACE pg_default;
