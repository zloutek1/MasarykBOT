import inject

from .leaderboard import LeaderboardRepository, LeaderboardEntity
from .logger import LoggerRepository, LoggerEntity
from .markov import MarkovRepository, MarkovEntity

REPOSITORIES = (LeaderboardRepository, LoggerRepository, MarkovRepository)
ENTITIES = (LeaderboardEntity, LoggerEntity, MarkovEntity)



def setup_injections(binder: inject.Binder) -> None:
    for repo_type in REPOSITORIES:
        binder.bind_to_constructor(repo_type, repo_type)
