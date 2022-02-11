-- Table: cogs.tags

-- DROP TABLE IF EXISTS cogs.tags;

CREATE TABLE IF NOT EXISTS cogs.tags
(
    guild_id bigint NOT NULL,
    author_id bigint,
    parent_id integer,
    id SERIAL NOT NULL,
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    content text COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    edited_at timestamp without time zone,
    deleted_at timestamp without time zone,
    CONSTRAINT tags_pkey PRIMARY KEY (id),
    CONSTRAINT tags_fkey_author FOREIGN KEY (author_id)
        REFERENCES server.users (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT tags_fkey_guild FOREIGN KEY (guild_id)
        REFERENCES server.guilds (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS cogs.tags
    OWNER to masaryk;
-- Index: fki_tags_fkey_author

-- DROP INDEX IF EXISTS cogs.fki_tags_fkey_author;

CREATE INDEX IF NOT EXISTS fki_tags_fkey_author
    ON cogs.tags USING btree
    (author_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_tags_fkey_guild

-- DROP INDEX IF EXISTS cogs.fki_tags_fkey_guild;

CREATE INDEX IF NOT EXISTS fki_tags_fkey_guild
    ON cogs.tags USING btree
    (guild_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: tags_unique_name

-- DROP INDEX IF EXISTS cogs.tags_unique_name;

CREATE UNIQUE INDEX IF NOT EXISTS tags_unique_name
    ON cogs.tags USING btree
    (guild_id ASC NULLS LAST, author_id ASC NULLS LAST, name COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
