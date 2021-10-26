-- SEQUENCE: cogs.seasons_id_seq

-- DROP SEQUENCE cogs.seasons_id_seq;

CREATE SEQUENCE cogs.seasons_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;

ALTER SEQUENCE cogs.seasons_id_seq
    OWNER TO masaryk_dev;

-- Table: cogs.seasons

-- DROP TABLE cogs.seasons;

CREATE TABLE IF NOT EXISTS cogs.seasons
(
    guild_id bigint NOT NULL,
    id integer NOT NULL DEFAULT nextval('cogs.seasons_id_seq'::regclass),
    name character varying COLLATE pg_catalog."default" NOT NULL,
    from_date timestamp with time zone,
    to_date timestamp with time zone,
    icon bytea,
    banner bytea,
    CONSTRAINT seasons_pkey PRIMARY KEY (guild_id, id)
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
    (guild_id ASC NULLS LAST, name COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;