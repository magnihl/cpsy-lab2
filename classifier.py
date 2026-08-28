"""Turns a raw TCS34725 reading into a colour name.

No hardware imports, so this runs and can be tested without the Pi.
"""

import math

UNKNOWN = "unknown"

# Normalised bench readings, one row per object. Averaging the four reds
# into one row made the dark tie match yellow.
REFERENCES = [
    ("red", (0.771, 0.104, 0.125)),     # matte cloth
    ("red", (0.719, 0.164, 0.118)),     # coke can, glossy
    ("red", (0.658, 0.179, 0.163)),     # tie, held against the sensor
    ("red", (0.597, 0.239, 0.165)),     # tie, held loosely
    ("yellow", (0.619, 0.266, 0.115)),  # book
    ("yellow", (0.585, 0.299, 0.116)),  # book, held closer
    ("green", (0.395, 0.438, 0.167)),   # book
    ("light blue", (0.217, 0.431, 0.352)),
    ("blue", (0.322, 0.290, 0.388)),  # tie, only two readings
]

# Every reading that should get a name lands within 0.026 of its row, and
# every reading that should be refused is past 0.081. Sitting in the middle
# of that gap leaves room on both sides.
MAX_DISTANCE = 0.05

# Off. Dark tie reads clear 170, sensor at nothing reads 110. Too close.
MIN_CLEAR = 0


def normalise(r, g, b):
    """Shares of the total, so brightness drops out. None if no light."""
    total = r + g + b
    if total == 0:
        return None
    return (r / total, g / total, b / total)


def distance(first, second):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(first, second)))


def classify(r, g, b, clear):
    """Name the nearest reference row, or UNKNOWN if nothing is close."""
    if clear < MIN_CLEAR:
        return UNKNOWN

    shares = normalise(r, g, b)
    if shares is None:
        return UNKNOWN

    name, nearest = min(
        ((name, distance(shares, reference))
         for name, reference in REFERENCES),
        key=lambda pair: pair[1])

    return name if nearest <= MAX_DISTANCE else UNKNOWN
