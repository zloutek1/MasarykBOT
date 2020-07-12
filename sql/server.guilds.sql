-- Table: server.guilds

-- DROP TABLE server.guilds;

CREATE TABLE server.guilds
(
    id bigint NOT NULL,
    name character varying(127) COLLATE pg_catalog."default",
    icon_url character varying(127) COLLATE pg_catalog."default",
    deleted_at timestamp with time zone NOT NULL DEFAULT to_timestamp((0)::double precision)
) PARTITION BY RANGE (deleted_at) ;

ALTER TABLE server.guilds
    OWNER to masaryk;

-- Partitions SQL

CREATE TABLE server."guilds.active" PARTITION OF server.guilds
    FOR VALUES FROM ('1970-01-01 01:00:00+01') TO ('1970-01-01 01:00:01+01');

CREATE TABLE server."guilds.deleted" PARTITION OF server.guilds
    DEFAULT;
