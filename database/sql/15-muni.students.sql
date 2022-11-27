-- Table: muni.students

-- DROP TABLE muni.students;

CREATE TABLE muni.students
(
    faculty character varying COLLATE pg_catalog."default" NOT NULL,
    code character varying COLLATE pg_catalog."default" NOT NULL,
    guild_id bigint NOT NULL,
    member_id bigint NOT NULL,
    joined_at timestamp without time zone NOT NULL DEFAULT now(),
    left_at timestamp without time zone,
    CONSTRAINT students_pkey PRIMARY KEY (faculty, code, guild_id, member_id),
    CONSTRAINT students_fkey_code FOREIGN KEY (code, faculty)
        REFERENCES muni.courses (code, faculty) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT students_fkey_guild FOREIGN KEY (guild_id)
        REFERENCES server.guilds (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE muni.students
    OWNER to masaryk;
-- Index: fki_students_fkey_code

-- DROP INDEX IF EXISTS muni.fki_students_fkey_code;

CREATE INDEX IF NOT EXISTS fki_students_fkey_code
    ON muni.students USING btree
    (code COLLATE pg_catalog."default" ASC NULLS LAST, faculty COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_students_fkey_guild

-- DROP INDEX IF EXISTS muni.fki_students_fkey_guild;

CREATE INDEX IF NOT EXISTS fki_students_fkey_guild
    ON muni.students USING btree
    (guild_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: fki_students_fkey_subject

-- DROP INDEX IF EXISTS muni.fki_students_fkey_subject;

CREATE INDEX IF NOT EXISTS fki_students_fkey_subject
    ON muni.students USING btree
    (code COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;