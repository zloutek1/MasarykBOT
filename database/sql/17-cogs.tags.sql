-- Table: cogs.tags

-- DROP TABLE cogs.tags;

CREATE TABLE cogs.tags
(
    guild_id bigint NOT NULL,
    author_id bigint NOT NULL,
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    content text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT tags_pkey PRIMARY KEY (name),
    CONSTRAINT tags_fkey_guild FOREIGN KEY (guild_id)
        REFERENCES server.guilds (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT tags_fkey_user FOREIGN KEY (author_id)
        REFERENCES server.users (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE cogs.tags
    OWNER to masaryk;
-- Index: fki_tags_fkey_guild

-- DROP INDEX cogs.fki_tags_fkey_guild;

CREATE INDEX fki_tags_fkey_guild
    ON cogs.tags USING btree
    (guild_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_tags_fkey_user

-- DROP INDEX cogs.fki_tags_fkey_user;

CREATE INDEX fki_tags_fkey_user
    ON cogs.tags USING btree
    (author_id ASC NULLS LAST)
    TABLESPACE pg_default;