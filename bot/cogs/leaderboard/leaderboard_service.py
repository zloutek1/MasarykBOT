from typing import Tuple, List

import inject

from bot.db import LeaderboardRepository, Record
from bot.db.leaderboard import Filters



class LeaderboardService:
    @inject.autoparams('leaderboard_repository')
    def __init__(self, leaderboard_repository: LeaderboardRepository) -> None:
        self.leaderboard_repository = leaderboard_repository

    async def get_data(self, user_id: int, filters: Filters) -> Tuple[List[Record], List[Record]]:
        await self.leaderboard_repository.preselect(filters)
        return (
            await self.leaderboard_repository.get_top10(),
            await self.leaderboard_repository.get_around(user_id)
        )
