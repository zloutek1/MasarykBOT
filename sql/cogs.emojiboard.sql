-- View: cogs.emojiboard

-- DROP MATERIALIZED VIEW cogs.emojiboard;

CREATE MATERIALIZED VIEW cogs.emojiboard
TABLESPACE pg_default
AS
 SELECT m.channel_id,
    unnest(reactions.member_ids) AS author_id,
    reactions.name
   FROM server.reactions
     JOIN server.messages m ON reactions.message_id = m.id
UNION
 SELECT m.channel_id,
    m.author_id,
    emojis.name
   FROM server.emojis
     JOIN server.messages m ON emojis.message_id = m.id
WITH DATA;

ALTER TABLE cogs.emojiboard
    OWNER TO masaryk;
