-- Table: cogs.markov

-- DROP TABLE IF EXISTS cogs.markov;

CREATE TABLE IF NOT EXISTS cogs.markov
(
    guild_id bigint NOT NULL,
    context character varying COLLATE pg_catalog."default" NOT NULL,
    follows character varying(1) COLLATE pg_catalog."default" NOT NULL,
    frequency integer NOT NULL,
    CONSTRAINT markov_pkey PRIMARY KEY (guild_id, context, follows),
    CONSTRAINT markov_fkey_guild FOREIGN KEY (guild_id)
        REFERENCES server.guilds (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS cogs.markov
    OWNER to masaryk;
-- Index: fki_markov_fkey_guild

-- DROP INDEX IF EXISTS cogs.fki_markov_fkey_guild;

CREATE INDEX IF NOT EXISTS fki_markov_fkey_guild
    ON cogs.markov USING btree
    (guild_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_markov_guild_context

-- DROP INDEX IF EXISTS cogs.fki_markov_guild_context;

CREATE INDEX IF NOT EXISTS fki_markov_guild_context
    ON cogs.markov USING btree
    (guild_id ASC NULLS LAST, context COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
