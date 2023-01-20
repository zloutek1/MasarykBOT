-- Table: cogs.leaderboard

-- DROP TABLE cogs.leaderboard;

CREATE TABLE cogs.leaderboard
(
    channel_id bigint,
    author_id bigint,
    messages_sent integer
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

CREATE FUNCTION server.update_leaderboard() RETURNS trigger
    LANGUAGE plpgsql
AS
$$
BEGIN
    IF NEW.channel_id IS NULL THEN
        INSERT INTO cogs.leaderboard AS ldb (channel_id, author_id, messages_sent)
        SELECT channel.id, NEW.author_id, 1
            FROM server.threads as thread
            INNER JOIN server.channels channel on channel.id = thread.parent_id
            WHERE thread.id = NEW.thread_id
        ON CONFLICT (channel_id, author_id) DO UPDATE
            SET messages_sent = ldb.messages_sent + 1;

        INSERT INTO cogs.leaderboard AS ldb (channel_id, author_id, messages_sent)
        VALUES (NEW.thread_id, NEW.author_id, 1)
        ON CONFLICT (channel_id, author_id) DO UPDATE
            SET messages_sent = ldb.messages_sent + 1;
    ELSE
        INSERT INTO cogs.leaderboard AS ldb (channel_id, author_id, messages_sent)
        VALUES (NEW.channel_id, NEW.author_id, 1)
        ON CONFLICT (channel_id, author_id) DO UPDATE
            SET messages_sent = ldb.messages_sent + 1;
    END IF;
    RETURN NEW;
END
$$;

ALTER FUNCTION server.update_leaderboard()
    OWNER TO masaryk;

-- Trigger: update_leaderboard

-- DROP TRIGGER update_leaderboard ON server.messages;

CREATE TRIGGER update_leaderboard
    AFTER INSERT
    ON server.messages
    FOR EACH ROW
    EXECUTE PROCEDURE server.update_leaderboard();