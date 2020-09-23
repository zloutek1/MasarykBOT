-- Table: cogs.rolemenu

-- DROP TABLE cogs.rolemenu;

CREATE TABLE cogs.rolemenu
(
    channel_id bigint NOT NULL,
    message_id bigint NOT NULL,
    role_id bigint NOT NULL,
    emoji character varying COLLATE pg_catalog."default" NOT NULL
)

TABLESPACE pg_default;

ALTER TABLE cogs.rolemenu
    OWNER to masaryk;