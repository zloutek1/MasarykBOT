-- Type: NGram

-- DROP TYPE IF EXISTS cogs."NGram";

CREATE TYPE cogs."NGram" AS
(
	first character varying,
	second character varying,
	third character varying
);

ALTER TYPE cogs."NGram"
    OWNER TO masaryk;

-- FUNCTION: cogs.array_to_ngram(text[])

-- DROP FUNCTION IF EXISTS cogs.array_to_ngram(text[]);

CREATE OR REPLACE FUNCTION cogs.array_to_ngram(
	words text[])
    RETURNS cogs."NGram"
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
	BEGIN
		RETURN ROW(words[1], words[2], words[3]) :: cogs."NGram";
	END
$BODY$;

ALTER FUNCTION cogs.array_to_ngram(text[])
    OWNER TO masaryk;

-- Table: cogs.markov

-- DROP TABLE IF EXISTS cogs.markov;

CREATE TABLE IF NOT EXISTS cogs.markov
(
    ngram cogs."NGram" NOT NULL,
    next character varying COLLATE pg_catalog."default" NOT NULL,
    weight bigint NOT NULL,
    CONSTRAINT markov_pkey PRIMARY KEY (ngram, next)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS cogs.markov
    OWNER to masaryk;

-- FUNCTION: cogs.markov_filter_words(text[])

-- DROP FUNCTION IF EXISTS cogs.markov_filter_words(text[]);

CREATE OR REPLACE FUNCTION cogs.markov_filter_words(
	words text[])
    RETURNS text[]
    LANGUAGE 'sql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
	SELECT array_agg(word)
	FROM unnest(words) as word
	WHERE NOT (
		word LIKE '!%' OR
		word LIKE '@%' OR
		word LIKE '<@%'
	)
$BODY$;

ALTER FUNCTION cogs.markov_filter_words(text[])
    OWNER TO masaryk;

-- PROCEDURE: cogs.markov_train_line(text)

-- DROP PROCEDURE IF EXISTS cogs.markov_train_line(text);

CREATE OR REPLACE PROCEDURE cogs.markov_train_line(
	msg text)
LANGUAGE 'plpgsql'
AS $BODY$
	#variable_conflict use_column
	DECLARE
		N         int := 3; -- depends on size of cogs."NGram"
		i         int;

		words     text[];
		length    int;

		ngram     cogs."NGram";
		next      text;
	BEGIN
		words := string_to_array(msg, ' ');
		words := cogs.markov_filter_words(words);

		IF words IS NULL THEN
			RETURN;
		END IF;

		length := array_length(words, 1);

		FOR i IN 1..length - N - 1 LOOP
			ngram := cogs.array_to_ngram(words[i:i+N]);
			next := words[i+N];

			INSERT INTO cogs.markov
			VALUES (ngram, next, 1)
			ON CONFLICT (ngram, next) DO UPDATE
				SET weight = cogs.markov.weight + 1;
		END LOOP;
	END
$BODY$;

-- PROCEDURE: cogs.markov_train()

-- DROP PROCEDURE IF EXISTS cogs.markov_train();

CREATE OR REPLACE PROCEDURE cogs.markov_train(
	)
LANGUAGE 'plpgsql'
AS $BODY$
	DECLARE
		msg   text;
	BEGIN
		TRUNCATE cogs.markov;
		FOR msg IN EXECUTE 'SELECT content FROM server.messages'
		LOOP
			IF msg <> '' THEN
				msg := '​SOF​ ' || msg || ' ​EOF​';
				CALL cogs.markov_train_line(msg);
			END IF;
		END LOOP;
	END
$BODY$;
