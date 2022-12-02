-- Table: server.categories

-- DROP TABLE server.categories;

CREATE TABLE server.categories
(
    guild_id bigint NOT NULL,
    id bigint NOT NULL,
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    "position" integer,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    edited_at timestamp with time zone,
    deleted_at timestamp with time zone,
    CONSTRAINT categories_pkey PRIMARY KEY (id),
    CONSTRAINT categories_fkey_guild FOREIGN KEY (guild_id)
        REFERENCES server.guilds (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE server.categories
    OWNER to masaryk;
-- Index: categories_idx_position

-- DROP INDEX server.categories_idx_position;

CREATE UNIQUE INDEX categories_idx_position
    ON server.categories USING btree
    (guild_id ASC NULLS LAST, id ASC NULLS LAST, "position" ASC NULLS LAST)
    TABLESPACE pg_default
    WHERE deleted_at IS NOT NULL;
-- Index: fki_categories_fkey_guild

-- DROP INDEX server.fki_categories_fkey_guild;

CREATE INDEX fki_categories_fkey_guild
    ON server.categories USING btree
    (guild_id ASC NULLS LAST)
    TABLESPACE pg_default;
