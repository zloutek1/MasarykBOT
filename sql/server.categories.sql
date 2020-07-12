-- Table: server.categories

-- DROP TABLE server.categories;

CREATE TABLE server.categories
(
    guild_id bigint NOT NULL,
    id bigint NOT NULL,
    name character varying(127) COLLATE pg_catalog."default",
    "position" integer,
    deleted_at timestamp with time zone NOT NULL DEFAULT to_timestamp((0)::double precision)
) PARTITION BY RANGE (deleted_at) ;

ALTER TABLE server.categories
    OWNER to masaryk;

-- Partitions SQL

CREATE TABLE server."categories.active" PARTITION OF server.categories
    FOR VALUES FROM ('1970-01-01 01:00:00+01') TO ('1970-01-01 01:00:01+01');

CREATE TABLE server."categories.deleted" PARTITION OF server.categories
    DEFAULT;
