from typing import List, Dict

# Channel IDs
verification_channels: List[int] = []
about_you_channels: List[int]  = []
subject_registration_channels: List[int]  = []
starboard_channels: List[int]  = []


# Log Channel IDs
error_log_channels: List[int] = []
mute_log_channels: List[int] = []
other_log_channels: List[int] = []


# <emoji_name, emoji_id>
emojis: Dict[str, int] = {}


# Role IDs
muted_roles: List[int] = []
verified_roles: List[int] = []
moderator_roles: List[int] = []
admin_roles: List[int] = []
show_all_subjects_roles: List[int] = []
mute_roles: List[int] = []


# Misc
NEEDED_REACTIONS: int = 10
FAME_REACT_LIMIT: int = 10
DEBUG: bool = False


# Colors
MUNI_YELLOW: int = 0xEACD59
