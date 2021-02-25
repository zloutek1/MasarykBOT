-- Table: cogs.leaderboard

-- DROP TABLE cogs.leaderboard;

CREATE TABLE cogs.leaderboard
(
    channel_id bigint,
    author_id bigint,
    messages_sent integer
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE cogs.leaderboard
    OWNER to masaryk;

-- Index: leaderboard_unique

-- DROP INDEX cogs.leaderboard_unique;

CREATE UNIQUE INDEX leaderboard_unique
    ON cogs.leaderboard USING btree
    (channel_id ASC NULLS LAST, author_id ASC NULLS LAST)
    TABLESPACE pg_default;




-- FUNCTION: server.update_leaderboard()

-- DROP FUNCTION server.update_leaderboard();

CREATE FUNCTION server.update_leaderboard()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
	INSERT INTO cogs.leaderboard AS ldb (channel_id, author_id, messages_sent)
	VALUES (NEW.channel_id, NEW.author_id, 1)
	ON CONFLICT (channel_id, author_id) DO UPDATE
		SET messages_sent = ldb.messages_sent + 1;
	RETURN NEW;
END
$BODY$;

ALTER FUNCTION server.update_leaderboard()
    OWNER TO masaryk;

-- Trigger: update_leaderboard

-- DROP TRIGGER update_leaderboard ON server.messages;

CREATE TRIGGER update_leaderboard
    AFTER INSERT
    ON server.messages
    FOR EACH ROW
    EXECUTE PROCEDURE server.update_leaderboard();