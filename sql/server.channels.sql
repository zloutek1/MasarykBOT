-- Table: server.channels

-- DROP TABLE server.channels;

CREATE TABLE server.channels
(
    guild_id bigint NOT NULL,
    category_id bigint NOT NULL,
    id bigint NOT NULL,
    name character varying(127) COLLATE pg_catalog."default",
    "position" integer,
    deleted_at timestamp with time zone NOT NULL DEFAULT to_timestamp((0)::double precision)
) PARTITION BY RANGE (deleted_at) ;

ALTER TABLE server.channels
    OWNER to masaryk;

-- Partitions SQL

CREATE TABLE server."channels.active" PARTITION OF server.channels
    FOR VALUES FROM ('1970-01-01 01:00:00+01') TO ('1970-01-01 01:00:01+01');

CREATE TABLE server."channels.deleted" PARTITION OF server.channels
    DEFAULT;
