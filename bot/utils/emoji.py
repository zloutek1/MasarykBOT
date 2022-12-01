from .extra_types import AnyEmote



def get_emoji_id(emoji: AnyEmote) -> int:
    if isinstance(emoji, str):
        return sum(map(ord, emoji))
    assert emoji.id, f"emoji {emoji} has no id"
    return emoji.id


def get_emoji_name(emoji: AnyEmote) -> str:
    if isinstance(emoji, str):
        return emoji
    return emoji.name
