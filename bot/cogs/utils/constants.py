from typing import List, Dict

# Channel IDs
verification_channels: List[int] = [
    621365818034356224,     # FI MUNI
]

about_you_channels: List[int] = [
    621365826372632606,     # FI MUNI
    760211019405590540,
]

subject_registration_channels: List[int] = [
    628684083345489950,     # FI MUNI
]

starboard_channels: List[int] = [
    761552082159271936,     # FI MUNI
]

# Log Channel IDs
error_log_channels: List[int] = [
    609413180137144331,     # FI MUNI
]
mute_log_channels: List[int] = []
other_log_channels: List[int] = []


# Emoji server
emojis: Dict[str, int] = {
    "Verification": 617745093889359872
}


# Roles
muted_roles: List[int] = []
verified_roles: List[int] = [
    621304939502632960,     # FI MUNI
]
moderator_roles: List[int] = []
admin_roles: List[int] = []
show_all_subjects_roles: List[int] = [
    628684833039712266,     # FI MUNI
]
mute_roles: List[int] = [
    627901278365810698,     # FI MUNI
]


# Misc
NEEDED_REACTIONS: int = 10
STARBOARD_REACT_LIMIT: int = 10
DEBUG: bool = False


# Colors
MUNI_YELLOW: int = 0xEACD59
