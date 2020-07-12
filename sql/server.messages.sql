-- Table: server.messages

-- DROP TABLE server.messages;

CREATE TABLE server.messages
(
    channel_id bigint NOT NULL,
    id bigint NOT NULL,
    content text COLLATE pg_catalog."default",
    created_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone NOT NULL DEFAULT to_timestamp((0)::double precision)
) PARTITION BY RANGE (deleted_at) ;

ALTER TABLE server.messages
    OWNER to masaryk;

-- Partitions SQL

CREATE TABLE server."messages.active" PARTITION OF server.messages
    FOR VALUES FROM ('1970-01-01 01:00:00+01') TO ('1970-01-01 01:00:01+01');

CREATE TABLE server."messages.deleted" PARTITION OF server.messages
    DEFAULT;
