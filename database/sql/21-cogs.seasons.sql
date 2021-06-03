-- Table: cogs.seasons

-- DROP TABLE cogs.seasons;

CREATE TABLE IF NOT EXISTS cogs.seasons
(
    guild_id bigint NOT NULL,
    event_name character varying COLLATE pg_catalog."default" NOT NULL,
    from_date timestamp without time zone,
    to_date timestamp without time zone,
    icon bytea,
    banner bytea,
    CONSTRAINT seasons_pkey PRIMARY KEY (guild_id, event_name)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE cogs.seasons
    OWNER to masaryk_dev;
-- Index: idx_seasons_unique

-- DROP INDEX cogs.idx_seasons_unique;

CREATE UNIQUE INDEX idx_seasons_unique
    ON cogs.seasons USING btree
    (guild_id ASC NULLS LAST, event_name ASC NULLS LAST, from_date ASC NULLS LAST, to_date ASC NULLS LAST)
    TABLESPACE pg_default;