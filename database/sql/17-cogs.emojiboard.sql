-- Table: cogs.emojiboard

-- DROP TABLE cogs.emojiboard;

CREATE TABLE cogs.emojiboard
(
    channel_id bigint,
    author_id bigint,
    emoji_id bigint,
    count integer
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE cogs.emojiboard
    OWNER to masaryk;
-- Index: emojiboard_idx_unique

-- DROP INDEX cogs.emojiboard_idx_unique;

CREATE UNIQUE INDEX emojiboard_idx_unique
    ON cogs.emojiboard USING btree
    (channel_id ASC NULLS LAST, author_id ASC NULLS LAST, emoji_id bigint ASC NULLS LAST)
    TABLESPACE pg_default;




-- FUNCTION: server.update_emojiboard_message_emoji()

-- DROP FUNCTION server.update_emojiboard_message_emoji;

CREATE FUNCTION server.update_emojiboard_message_emoji()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
	INSERT INTO cogs.emojiboard AS eb (channel_id, author_id, emoji_id, count)
	SELECT channel_id, author_id, NEW.emoji_id, NEW.count
		FROM server.messages WHERE server.messages.id = NEW.message_id
	ON CONFLICT (channel_id, author_id, emoji_id) DO UPDATE
		SET count = eb.count + NEW.count;
	RETURN NEW;
END
$BODY$;

ALTER FUNCTION server.update_emojiboard_message_emoji()
    OWNER TO masaryk;


-- Trigger: update_emojiboard

-- DROP TRIGGER update_emojiboard ON server.emojis;

CREATE TRIGGER update_emojiboard
    AFTER INSERT
    ON server.message_emojis
    FOR EACH ROW
    EXECUTE PROCEDURE server.update_emojiboard_message_emoji();




-- FUNCTION: server.update_emojiboard_reaction()

-- DROP FUNCTION server.update_emojiboard_reaction();

CREATE FUNCTION server.update_emojiboard_reaction()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
	INSERT INTO cogs.emojiboard AS eb (channel_id, author_id, emoji_id, count)
	SELECT channel_id, unnest(NEW.member_ids) as author_id, NEW.emoji_id, 1
		FROM server.messages WHERE server.messages.id = NEW.message_id
	ON CONFLICT (channel_id, author_id, emoji_id) DO UPDATE
		SET count = eb.count + array_length(NEW.member_ids, 1);
	RETURN NEW;
END
$BODY$;

ALTER FUNCTION server.update_emojiboard_reaction()
    OWNER TO masaryk;


-- Trigger: update_emojiboard

-- DROP TRIGGER update_emojiboard ON server.reactions;

CREATE TRIGGER update_emojiboard
    AFTER INSERT
    ON server.reactions
    FOR EACH ROW
    EXECUTE PROCEDURE server.update_emojiboard_reaction();