-- Table: cogs.logger

-- DROP TABLE cogs.logger;

CREATE TABLE cogs.logger
(
    guild_id bigint NOT NULL DEFAULT nextval('cogs.logger_id_seq'::regclass),
    from_date timestamp without time zone NOT NULL,
    to_date timestamp without time zone NOT NULL,
    finished_at timestamp without time zone
)

TABLESPACE pg_default;

ALTER TABLE cogs.logger
    OWNER to masaryk;
-- Index: logger_idx_unique_end

-- DROP INDEX cogs.logger_idx_unique_end;

CREATE UNIQUE INDEX logger_idx_unique_end
    ON cogs.logger USING btree
    (guild_id ASC NULLS LAST, to_date ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: logger_idx_unique_start

-- DROP INDEX cogs.logger_idx_unique_start;

CREATE UNIQUE INDEX logger_idx_unique_start
    ON cogs.logger USING btree
    (guild_id ASC NULLS LAST, from_date ASC NULLS LAST)
    TABLESPACE pg_default;
