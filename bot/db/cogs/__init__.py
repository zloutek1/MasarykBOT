import inject

from .leaderboard import LeaderboardRepository, LeaderboardEntity
from .logger import LoggerRepository, LoggerEntity

REPOSITORIES = (LeaderboardRepository, LoggerRepository)
ENTITIES = (LeaderboardEntity, LoggerEntity)



def setup_injections(binder: inject.Binder) -> None:
    for repo_type in REPOSITORIES:
        binder.bind_to_constructor(repo_type, repo_type)
