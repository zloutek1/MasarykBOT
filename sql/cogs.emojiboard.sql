-- View: cogs.emojiboard

-- DROP MATERIALIZED VIEW cogs.emojiboard;

CREATE MATERIALIZED VIEW cogs.emojiboard
TABLESPACE pg_default
AS
 SELECT emojis.name,
    sum(emojis.count) AS count
   FROM ( SELECT emojis_1.message_id,
            emojis_1.name,
            emojis_1.count
           FROM server.emojis emojis_1
        UNION
         SELECT reactions.message_id,
            reactions.name,
            reactions.count
           FROM server.reactions) emojis
  GROUP BY emojis.name
  ORDER BY (sum(emojis.count)) DESC
WITH DATA;

ALTER TABLE cogs.emojiboard
    OWNER TO masaryk;
