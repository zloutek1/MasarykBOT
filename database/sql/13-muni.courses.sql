-- Table: muni.courses

-- DROP TABLE muni.courses;

CREATE TABLE IF NOT EXISTS muni.courses
(
    faculty character varying COLLATE pg_catalog."default" NOT NULL,
    code character varying COLLATE pg_catalog."default" NOT NULL,
    name character varying COLLATE pg_catalog."default" NOT NULL,
    url text COLLATE pg_catalog."default" NOT NULL,
    terms character varying[] COLLATE pg_catalog."default" NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    edited_at timestamp with time zone,
    deleted_at timestamp with time zone,
    CONSTRAINT courses_pkey PRIMARY KEY (faculty, code),
    CONSTRAINT fki_course_faculty_fkey_faculty FOREIGN KEY (faculty)
        REFERENCES muni.faculties (code) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE muni.courses
    OWNER to masaryk;
-- Index: fki_course_faculty_fkey_faculty

-- DROP INDEX IF EXISTS muni.fki_course_faculty_fkey_faculty;

CREATE INDEX IF NOT EXISTS fki_course_faculty_fkey_faculty
    ON muni.courses USING btree
    (faculty COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: courses_autocomplete_idx

-- DROP INDEX IF EXISTS muni.courses_autocomplete_idx;

CREATE INDEX IF NOT EXISTS courses_autocomplete_idx
    ON muni.courses USING btree
    ((faculty::text || ':'::text || code::text || ' '::text || substr(name::text, 1, 50)) COLLATE pg_catalog."default" text_pattern_ops ASC NULLS LAST)
    TABLESPACE pg_default;
