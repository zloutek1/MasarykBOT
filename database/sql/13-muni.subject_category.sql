-- Table: muni.subject_category

-- DROP TABLE muni.subject_category;

CREATE TABLE muni.subject_category
(
    code character varying COLLATE pg_catalog."default" NOT NULL,
    guild_id bigint NOT NULL,
    category_name character varying COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT subject_category_fkey_code FOREIGN KEY (code)
        REFERENCES muni.subjects (code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT subject_category_fkey_guild FOREIGN KEY (guild_id)
        REFERENCES server.guilds (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE muni.subject_category
    OWNER to masaryk;
-- Index: fki_subject_category_fkey_code

-- DROP INDEX muni.fki_subject_category_fkey_code;

CREATE INDEX fki_subject_category_fkey_code
    ON muni.subject_category USING btree
    (code COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_subject_category_fkey_guild

-- DROP INDEX muni.fki_subject_category_fkey_guild;

CREATE INDEX fki_subject_category_fkey_guild
    ON muni.subject_category USING btree
    (guild_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: subject_category_idx_unique

-- DROP INDEX muni.subject_category_idx_unique;

CREATE UNIQUE INDEX subject_category_idx_unique
    ON muni.subject_category USING btree
    (code COLLATE pg_catalog."default" ASC NULLS LAST, guild_id ASC NULLS LAST)
    TABLESPACE pg_default;