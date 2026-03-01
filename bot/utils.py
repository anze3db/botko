import re

KARMA_EMOJIS = (
    "botko",
    "100",
    "1000",
    "+1",
    "thumbs",
    "thumbsup_all",
    "heavy_plus_sign",
    "laughing",
    "joy",
    "rolling_on_the_floor_laughing",
    "joy_cat",
    "smile",
    "smiling_face_with_3_hearts",
    "heart",
    "hearts",
    "lolsob",
    "fire",
    "rocket",
    "tada",
    "face_holding_back_tears",
)


def parse_karma_from_text(text: str) -> list[str]:
    users = [match for match in re.findall(r"<@(U[A-Z0-9]*)>.?\+\+", text)]
    return users
