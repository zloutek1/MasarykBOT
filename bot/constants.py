# pyright: reportMissingImports=false, reportUntypedClassDecorator=false

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

import yaml
from enforce_typing import enforce_types


@enforce_types
@dataclass(frozen=True)
class BotConfig(yaml.YAMLObject):
    yaml_tag = u'!bots'

    prefix: str
    DEBUG: bool = False


@enforce_types
@dataclass(frozen=True)
class StarboardChannelConfig(yaml.YAMLObject):
    yaml_tag = u'!starch'

    ignored: List[str | int]
    penalised: List[str | int]


@enforce_types
@dataclass(frozen=True)
class StarbardEmojiConfig(yaml.YAMLObject):
    yaml_tag = u'!starem'

    ignored: List[str | int]
    penalised: List[str | int]


@enforce_types
@dataclass(frozen=True)
class StarboardConfig(yaml.YAMLObject):
    yaml_tag = u'!starboard'

    starboard: int
    channels: StarboardChannelConfig
    emojis: StarbardEmojiConfig
    best_of_memes: Optional[int] = None
    best_of_masaryk: Optional[int] = None
    REACT_LIMIT: Optional[int] = None


@enforce_types
@dataclass(frozen=True)
class ChannelConfig(yaml.YAMLObject):
    yaml_tag = u'!channels'

    verification: Optional[int] = None
    about_you: Optional[int] = None
    subject_registration: Optional[int] = None
    starboard: Optional[StarboardConfig] = None
    threaded: List[int] = field(default_factory=list)


@enforce_types
@dataclass(frozen=True)
class LogsConfig(yaml.YAMLObject):
    yaml_tag = u'!logs'

    errors: Optional[int] = None
    mute: Optional[int] = None
    other: Optional[int] = None
    webhook: Optional[str] = None


@enforce_types
@dataclass(frozen=True)
class RoleConfig(yaml.YAMLObject):
    yaml_tag = u'!roles'

    muted: Optional[int] = None
    verified: Optional[int] = None
    moderator: Optional[int] = None
    admin: Optional[int] = None
    show_all: Optional[int] = None


@enforce_types
@dataclass(frozen=True)
class GuildConfig(yaml.YAMLObject):
    yaml_tag = u'!guilds'

    id: int
    name: str
    channels: ChannelConfig
    logs: LogsConfig
    roles: RoleConfig
    NEEDED_REACTIONS: Optional[int] = None


@enforce_types
@dataclass(frozen=True)
class EmojiConfig(yaml.YAMLObject):
    yaml_tag = u'!emojis'

    Verification: Optional[int] = None


@enforce_types
@dataclass(frozen=True)
class ColorConfig(yaml.YAMLObject):
    yaml_tag = u'!colors'

    MUNI_YELLOW: Optional[int] = None


@enforce_types
@dataclass(frozen=True)
class Config(yaml.YAMLObject):
    yaml_tag = u'!Config'

    bot: BotConfig
    emoji: EmojiConfig
    colors: ColorConfig
    guilds: List[GuildConfig]


T = TypeVar('T', bound=yaml.YAMLObject)


def class_loader(clazz: Type[T]) -> Callable[[yaml.SafeLoader, yaml.nodes.MappingNode], T]:
    def constructor(loader: yaml.SafeLoader, node: yaml.nodes.MappingNode) -> T:
        mapping: Dict[str, Any] = loader.construct_mapping(node)
        obj = object.__new__(clazz)
        obj.__init__(**mapping)  # type: ignore
        return obj

    return constructor


def get_loader() -> Type[yaml.Loader]:
    """Return a yaml loader."""
    loader = yaml.Loader
    loader.add_constructor("!bots", class_loader(BotConfig))
    loader.add_constructor("!starch", class_loader(StarboardChannelConfig))
    loader.add_constructor("!starem", class_loader(StarbardEmojiConfig))
    loader.add_constructor("!starboard", class_loader(StarboardConfig))
    loader.add_constructor("!chnls", class_loader(ChannelConfig))
    loader.add_constructor("!logs", class_loader(LogsConfig))
    loader.add_constructor("!roles", class_loader(RoleConfig))
    loader.add_constructor("!guilds", class_loader(GuildConfig))
    loader.add_constructor("!emojis", class_loader(EmojiConfig))
    loader.add_constructor("!colors", class_loader(ColorConfig))
    loader.add_constructor("!Config", class_loader(Config))
    return loader


path = Path(__file__).parent.parent.joinpath('config.yml')
with open(path, encoding="UTF-8") as file:
    print("Loading Config")
    CONFIG: Config = yaml.load(file.read(), get_loader())
