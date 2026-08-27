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

# TODO: fill this in from bench readings, one row per colour card.
#
# Each value is a normalised reading, that is the red, green and blue
# shares of the total, so the three numbers in a row always sum to 1.0.
# Take a reading of the card, pass the raw counts through normalise, and
# paste the result here as a row. Keep the names under about 16 characters
# so they fit on the display.
#
#     "red": (0.85, 0.15, 0.00),
#     "green": (0.20, 0.60, 0.20),
#
REFERENCES = {}

# TODO: tune. How far a reading may sit from the nearest reference and
# still be called by that name. Too small and everything reports unknown,
# too large and the glossy samples get confidently mislabelled. Distances
# run from 0.0 for an exact match to about 1.4 for opposite corners of the
# colour space, so a sensible starting range is roughly 0.05 to 0.25.
MAX_DISTANCE = 0.15

# TODO: tune. Minimum clear count for a reading to be trusted at all.
# Zero switches the check off, which is the right setting until bench
# readings show what a too dark reading actually looks like.
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
            "Add one row per colour card, see the TODO in classifier.py")

    name, nearest = min(
        ((name, distance(shares, reference))
         for name, reference in REFERENCES.items()),
        key=lambda pair: pair[1])

    if nearest > MAX_DISTANCE:
        return UNKNOWN
    return name
