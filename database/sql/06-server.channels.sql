-- Type: channel_type

-- DROP TYPE IF EXISTS server.channel_type;

CREATE TYPE server.channel_type AS ENUM
    ('text', 'forum');

ALTER TYPE server.channel_type
    OWNER TO masaryk;

-- Table: server.channels

-- DROP TABLE server.channels;

CREATE TABLE server.channels
(
    guild_id bigint NOT NULL,
    category_id bigint,
    id bigint NOT NULL,
    "name" character varying(100) COLLATE pg_catalog."default" NOT NULL,
    "type" server.channel_type NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    edited_at timestamp with time zone,
    deleted_at timestamp with time zone,
    CONSTRAINT channels_pkey PRIMARY KEY (id),
    CONSTRAINT channels_fkey_category FOREIGN KEY (category_id)
        REFERENCES server.categories (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT channels_fkey_guild FOREIGN KEY (guild_id)
        REFERENCES server.guilds (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE server.channels
    OWNER to masaryk;
-- Index: fki_channels_fkey_category

-- DROP INDEX server.fki_channels_fkey_category;

CREATE INDEX fki_channels_fkey_category
    ON server.channels USING btree
    (category_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_channels_fkey_guild

-- DROP INDEX server.fki_channels_fkey_guild;

CREATE INDEX fki_channels_fkey_guild
    ON server.channels USING btree
    (guild_id ASC NULLS LAST)
    TABLESPACE pg_default;
