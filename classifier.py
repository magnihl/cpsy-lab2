"""Colour classification logic for the sensing station.

This module deliberately imports nothing from board, busio or any Adafruit
package. It turns numbers into a name and nothing else, which means it can
be tested on a laptop with no Raspberry Pi and no sensor attached.

The rule is a nearest reference lookup rather than a chain of if
statements, so adding a colour means adding a row to REFERENCES rather
than writing more logic.
"""

import math

# Label returned when a reading cannot be trusted, for example the all zero
# reading the TCS34725 produces before its first integration cycle finishes,
# or a sample that sits too far from every known colour.
UNKNOWN = "unknown"

# Reference readings, one row per object scanned, several rows allowed per
# colour name. Each value is a normalised reading, that is the red, green
# and blue shares of the total, so a row always sums to 1.0.
#
# A list of pairs rather than a dict keyed by name, because one row per
# colour is not enough. Averaging four red objects into a single row put
# that row where no real red object sits, close enough to yellow that the
# dark red tie came out nearer to the yellow book than to its own colour.
# Keeping each object as its own row compares against measured points
# instead of an invented midpoint.
#
# To add a colour, scan the object, pass the raw counts through normalise
# and append the result with a name. Keep names under about 16 characters
# so they fit the display.
REFERENCES = [
    ("red", (0.771, 0.104, 0.125)),     # matte cloth
    ("red", (0.719, 0.164, 0.118)),     # coke can, glossy
    ("red", (0.658, 0.179, 0.163)),     # tie, dark, held against the sensor
    ("red", (0.597, 0.239, 0.165)),     # tie, held loosely, room light leaking
    ("yellow", (0.619, 0.266, 0.115)),  # book
    ("yellow", (0.585, 0.299, 0.116)),  # book, held closer
    ("green", (0.395, 0.438, 0.167)),   # book
    ("light blue", (0.217, 0.431, 0.352)),
]

# How far a reading may sit from the nearest reference row and still take
# that row's name. Bench readings of one object land within about 0.03 of
# their row, while the closest two rows of different colours, the dark red
# tie and the yellow book, are 0.061 apart. 0.08 sits above the noise and
# below that gap.
MAX_DISTANCE = 0.08

# Minimum clear count for a reading to be trusted at all. Zero switches the
# check off, which is where it stays for now: the dark red tie is a good
# reading at clear 170 and the sensor held away from a sample is a bad one
# at clear 110, too close together for a threshold to separate. Readings
# with no sample in front of the sensor are currently rejected on distance
# instead.
MIN_CLEAR = 0

def normalise(r, g, b):
    """Turn raw counts into shares of the total, dropping brightness.

    A bright red card and a dim red card produce very different raw
    counts but almost the same shares, which is what makes the reference
    table survive a change in lighting.

    Returns None when the reading carries no light at all and so cannot
    be normalised.
    """
    total = r + g + b
    if total == 0:
        return None
    return (r / total, g / total, b / total)


def distance(first, second):
    """Straight line distance between two normalised colours."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(first, second)))


def classify(r, g, b, clear):
    """Turn one raw sensor reading into a colour name.

    Args:
        r: raw red count from the TCS34725.
        g: raw green count.
        b: raw blue count.
        clear: raw unfiltered light count, that is the total light the
            sensor saw. Used only to reject readings taken in too little
            light to mean anything.

    Returns:
        The name of the nearest row in REFERENCES, or UNKNOWN when the
        reading cannot be trusted or sits further than MAX_DISTANCE from
        every known colour.
    """
    if clear < MIN_CLEAR:
        return UNKNOWN

    shares = normalise(r, g, b)
    if shares is None:
        return UNKNOWN

    if not REFERENCES:
        raise NotImplementedError(
            "REFERENCES is empty, so there is nothing to compare against. "
            "Add one row per object scanned, see the note in classifier.py")

    name, nearest = min(
        ((name, distance(shares, reference))
         for name, reference in REFERENCES),
        key=lambda pair: pair[1])

    if nearest > MAX_DISTANCE:
        return UNKNOWN
    return name
