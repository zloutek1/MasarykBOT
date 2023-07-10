from dependency_injector import containers, providers

from channel.category.syncer import CategoryChannelSyncer
from channel.text.syncer import TextChannelSyncer
from role.syncer import RoleSyncer


class Syncer(containers.DeclarativeContainer):
    """
    Setup injections of the application's synchronizes
    """

    role_repository = providers.Dependency()
    role = providers.Singleton(RoleSyncer, repository=role_repository)

    category_channel_repository = providers.Dependency()
    category_channel = providers.Singleton(CategoryChannelSyncer, repository=category_channel_repository)

    text_channel_repository = providers.Dependency()
    text_channel = providers.Singleton(TextChannelSyncer, repository=text_channel_repository)

    all = providers.List(
        role, category_channel, text_channel
    )
