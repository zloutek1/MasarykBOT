-- Table: muni.registers

-- DROP TABLE muni.registers;

CREATE TABLE muni.registers
(
    guild_id bigint NOT NULL,
    code character varying COLLATE pg_catalog."default" NOT NULL,
    channel_id bigint,
    member_ids bigint[] NOT NULL DEFAULT ARRAY[]::bigint[],
    CONSTRAINT registers_fkey_subject FOREIGN KEY (code)
        REFERENCES muni.subjects (code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE muni.registers
    OWNER to masaryk;
-- Index: fki_registers_fkey_subject

-- DROP INDEX muni.fki_registers_fkey_subject;

CREATE INDEX fki_registers_fkey_subject
    ON muni.registers USING btree
    (code COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: registers_idx_unique

-- DROP INDEX muni.registers_idx_unique;

CREATE UNIQUE INDEX registers_idx_unique
    ON muni.registers USING btree
    (guild_id ASC NULLS LAST, code COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
