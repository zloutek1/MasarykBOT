-- Table: muni.registers

-- DROP TABLE muni.registers;

CREATE TABLE muni.registers
(
    faculty character varying COLLATE pg_catalog."default" NOT NULL,
    code character varying COLLATE pg_catalog."default" NOT NULL,
    guild_id bigint NOT NULL,
    member_ids bigint[] NOT NULL,
    CONSTRAINT registers_fkey_code FOREIGN KEY (code, faculty)
        REFERENCES muni.subjects (code, faculty) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT registers_fkey_guild FOREIGN KEY (guild_id)
        REFERENCES server.guilds (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE muni.registers
    OWNER to masaryk;
-- Index: fki_registers_fkey_code

-- DROP INDEX muni.fki_registers_fkey_code;

CREATE INDEX fki_registers_fkey_code
    ON muni.registers USING btree
    (code COLLATE pg_catalog."default" ASC NULLS LAST, faculty COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_registers_fkey_guild

-- DROP INDEX muni.fki_registers_fkey_guild;

CREATE INDEX fki_registers_fkey_guild
    ON muni.registers USING btree
    (guild_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_registers_fkey_subject

-- DROP INDEX muni.fki_registers_fkey_subject;

CREATE INDEX fki_registers_fkey_subject
    ON muni.registers USING btree
    (code COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: registers_fkey_unique

-- DROP INDEX muni.registers_fkey_unique;

CREATE UNIQUE INDEX registers_fkey_unique
    ON muni.registers USING btree
    (code COLLATE pg_catalog."default" ASC NULLS LAST, guild_id ASC NULLS LAST)
    TABLESPACE pg_default;