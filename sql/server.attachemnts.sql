-- Table: server.attachments

-- DROP TABLE server.attachments;

CREATE TABLE server.attachments
(
    message_id bigint NOT NULL,
    id bigint NOT NULL,
    filename text COLLATE pg_catalog."default",
    url text COLLATE pg_catalog."default",
    CONSTRAINT attachments_pkey PRIMARY KEY (id),
    CONSTRAINT attachments_fkey_message FOREIGN KEY (message_id)
        REFERENCES server.messages (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE server.attachments
    OWNER to masaryk;
-- Index: fki_attachments_fkey_message

-- DROP INDEX server.fki_attachments_fkey_message;

CREATE INDEX fki_attachments_fkey_message
    ON server.attachments USING btree
    (message_id ASC NULLS LAST)
    TABLESPACE pg_default;
