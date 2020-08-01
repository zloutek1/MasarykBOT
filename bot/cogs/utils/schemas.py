SQL_INSERT_GUILD = """
    INSERT INTO server.guilds AS g (id, name, icon_url, created_at)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (id) DO UPDATE
        SET name=$2,
            icon_url=$3,
            created_at=$4,
            edited_at=NOW()
        WHERE g.name<>excluded.name OR
              g.icon_url<>excluded.icon_url OR
              g.created_at<>excluded.created_at
"""

SQL_INSERT_CATEGORY = """
    INSERT INTO server.categories AS c (guild_id, id, name, position, created_at)
    VALUES ($1, $2, $3, $4, $5)
    ON CONFLICT (id) DO UPDATE
        SET name=$3,
            position=$4,
            created_at=$5,
            edited_at=NOW()
        WHERE c.name<>excluded.name OR
              c.position<>excluded.position OR
              c.created_at<>excluded.created_at
"""

SQL_INSERT_CHANNEL = """
    INSERT INTO server.channels AS ch (guild_id, category_id, id, name, position, created_at)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (id) DO UPDATE
        SET name=$4,
            position=$5,
            created_at=$6,
            edited_at=NOW()
        WHERE ch.name<>excluded.name OR
              ch.position<>excluded.position OR
              ch.created_at<>excluded.created_at
"""

SQL_INSERT_USER = """
    INSERT INTO server.users AS u (id, names, avatar_url, created_at)
    VALUES ($1, ARRAY[$2], $3, $4)
    ON CONFLICT (id) DO UPDATE
        SET names=array_prepend($2::varchar, u.names),
            avatar_url=$3,
            created_at=$4,
            edited_at=NOW()
        WHERE $2<>ANY(u.names) OR
              u.avatar_url<>excluded.avatar_url OR
              u.created_at<>excluded.created_at
"""


SQL_INSERT_ROLE = """
    INSERT INTO server.roles AS r (guild_id, id, name, color, created_at)
    VALUES ($1, $2, $3, $4, $5)
    ON CONFLICT (id) DO UPDATE
        SET name=$3,
            color=$4,
            created_at=$5,
            edited_at=NOW()
        WHERE r.name<>excluded.name OR
              r.color<>excluded.color OR
              r.created_at<>excluded.created_at
"""

SQL_INSERT_MESSAGE = """
    INSERT INTO server.messages AS m (channel_id, author_id, id, content, created_at, edited_at)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (id) DO UPDATE
        SET content=$4,
            created_at=$5,
            edited_at=$6
        WHERE m.content<>excluded.content OR
              m.created_at<>excluded.created_at OR
              m.edited_at<>excluded.edited_at
"""

SQL_INSERT_ATTACHEMNT = """
    INSERT INTO server.attachments AS a (message_id, id, filename, url)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (id) DO UPDATE
        SET filename=$3,
            url=$4
        WHERE a.filename<>excluded.filename OR
              a.url<>excluded.url
"""

SQL_INSERT_REACTIONS = """
    INSERT INTO server.reactions AS r (message_id, name, member_ids)
    VALUES ($1, $2, $3)
    ON CONFLICT (message_id, name) DO NOTHING
"""

SQL_INSERT_EMOJIS = """
    INSERT INTO server.emojis AS r (message_id, name, count)
    VALUES ($1, $2, $3)
    ON CONFLICT (message_id, name) DO NOTHING
"""

SQL_SELECT_LEADERBOARD = """
    CREATE TEMPORARY TABLE IF NOT EXISTS ldb_lookup AS
        SELECT
            ROW_NUMBER() OVER (ORDER BY sent_total DESC), *
        FROM (
            SELECT
                author_id,
                author.names[1] AS author,
                SUM(messages_sent) AS sent_total
            FROM cogs.leaderboard
            INNER JOIN server.users AS author
                ON author_id = author.id
            INNER JOIN server.channels AS channel
                ON channel_id = channel.id
            WHERE guild_id = $1::bigint AND
                  author_id<>ALL($2::bigint[]) AND
                  ($3::bigint IS NULL OR channel_id = $3)
            GROUP BY author_id, author.names
            ORDER BY sent_total DESC
        ) AS lookup
"""

SQL_AROUND_SELECT_LEADERBOARD = """
    WITH desired_count AS (
        SELECT sent_total
        FROM ldb_lookup
        WHERE author_id = $1
    )

    (   SELECT *
        FROM ldb_lookup
        WHERE sent_total >= (SELECT * FROM desired_count) AND author_id <> $1
        ORDER BY sent_total LIMIT 2
    ) UNION (
        SELECT *
        FROM ldb_lookup
        WHERE sent_total = (SELECT * FROM desired_count)
    ) UNION (
        SELECT *
        FROM ldb_lookup
        WHERE sent_total < (SELECT * FROM desired_count) AND author_id <> $1 LIMIT 2
    ) ORDER BY sent_total DESC
"""

SQL_SELECT_EMOJIBOARD = """
    SELECT
        emoji.name,
        COUNT(*) AS sent_total
    FROM cogs.emojiboard AS emoji
    INNER JOIN server.channels AS channel
        ON channel_id = channel.id
    WHERE guild_id = $1::bigint AND
          author_id<>ALL($2::bigint[]) AND
          ($3::bigint IS NULL OR channel_id = $3)
    GROUP BY emoji.name
    ORDER BY sent_total DESC
    LIMIT 10
"""
