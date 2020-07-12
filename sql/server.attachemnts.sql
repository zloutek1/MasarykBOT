-- Table: server.attachments

-- DROP TABLE server.attachments;

CREATE TABLE server.attachments
(
    message_id bigint NOT NULL,
    id bigint NOT NULL,
    filename character varying(127) COLLATE pg_catalog."default",
    url character varying(127) COLLATE pg_catalog."default",
    CONSTRAINT attachments_primary PRIMARY KEY (id),
    CONSTRAINT attachments_messages FOREIGN KEY (message_id)
        REFERENCES server."messages.active" (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)

TABLESPACE pg_default;

ALTER TABLE server.attachments
    OWNER to masaryk;
-- Index: fki_attachments_messages

-- DROP INDEX server.fki_attachments_messages;

CREATE INDEX fki_attachments_messages
    ON server.attachments USING btree
    (message_id ASC NULLS LAST)
    TABLESPACE pg_default;
