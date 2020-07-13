import unittest

import os
import asyncio
import asyncpg

from dotenv import load_dotenv
load_dotenv()


class TestDatabase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        try:
            self.pool = await asyncpg.create_pool(os.getenv("POSTGRES"), command_timeout=60)
        except Exception as e:
            self.fail(e)

    async def asyncTearDown(self):
        self.pool.terminate()

    async def test_connection(self):
        async with self.pool.acquire() as con:
            ret = await con.fetchval('SELECT 1')
            self.assertEqual(ret, 1)

    async def test_server_collection(self):
        async with self.pool.acquire() as con:
            ret = await con.fetch("SELECT * FROM pg_catalog.pg_tables WHERE schemaname = 'server'")
            names = list(map(lambda row: row.get("tablename"), ret))

            self.assertIn("guilds", names)
            self.assertIn("categories", names)
            self.assertIn("channels", names)
            self.assertIn("messages", names)
            self.assertIn("attachments", names)

    async def test_server_partitioned(self):
        async with self.pool.acquire() as con:
            ret = await con.fetch("SELECT * FROM pg_catalog.pg_tables WHERE schemaname = 'server'")
            names = list(map(lambda row: row.get("tablename"), ret))

            self.assertIn("guilds.active", names)
            self.assertIn("guilds.deleted", names)

            self.assertIn("categories.active", names)
            self.assertIn("categories.deleted", names)

            self.assertIn("channels.active", names)
            self.assertIn("channels.deleted", names)

            self.assertIn("messages.active", names)
            self.assertIn("messages.deleted", names)

            self.assertNotIn("attachments.active", names)
            self.assertNotIn("attachments.deleted", names)

    async def test_server_guild_active(self):
        snowflake = 111111111111111111
        name = "_@test@_"

        async with self.pool.acquire() as con:
            await con.execute("""
                DELETE FROM server.guilds
                       WHERE id = $1 AND name = $2
            """, snowflake, name)

            # insert once
            await con.execute("""
                INSERT INTO server.guilds (id, name, icon_url, deleted_at)
                    VALUES ($1, $2, $3, to_timestamp(0));""", snowflake, name, None)

            # fails on duplicate
            with self.assertRaises(asyncpg.exceptions.UniqueViolationError):
                await con.execute("""
                    INSERT INTO server.guilds (id, name, icon_url, deleted_at)
                           VALUES ($1, $2, $3, to_timestamp(0));""", snowflake, name, None)

            await con.execute("""
                DELETE FROM server.guilds
                       WHERE id = $1 AND name = $2
            """, snowflake, name)

    async def test_server_guild_deleted(self):
        snowflake = 111111111111111111
        name = "_@test@_"

        async with self.pool.acquire() as con:
            await con.execute("""
                DELETE FROM server.guilds
                       WHERE id = $1 AND name = $2
            """, snowflake, name)

            for i in range(3):
                # insert once
                await con.execute("""
                    INSERT INTO server.guilds (id, name, icon_url, deleted_at)
                        VALUES ($1, $2, $3, to_timestamp(0));""", snowflake, name, None)

                # soft delete
                await con.execute("""
                    UPDATE server.guilds
                        SET deleted_at=NOW()
                        WHERE id = $1 AND name = $2;""", snowflake, name)

            await con.execute("""
                DELETE FROM server.guilds
                       WHERE id = $1 AND name = $2
            """, snowflake, name)


if __name__ == "__main__":
    unittest.main()
