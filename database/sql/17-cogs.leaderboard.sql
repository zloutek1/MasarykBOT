-- View: cogs.leaderboard

-- DROP MATERIALIZED VIEW cogs.leaderboard;

CREATE MATERIALIZED VIEW cogs.leaderboard
TABLESPACE pg_default
AS
 SELECT messages.channel_id,
    messages.author_id,
    count(*) AS messages_sent
   FROM server.messages
  GROUP BY messages.channel_id, messages.author_id
  ORDER BY (count(*)) DESC
WITH DATA;

ALTER TABLE cogs.leaderboard
    OWNER TO masaryk;


CREATE UNIQUE INDEX leaderboard_idx_unique
    ON cogs.leaderboard USING btree
    (channel_id, author_id)
    TABLESPACE pg_default;
