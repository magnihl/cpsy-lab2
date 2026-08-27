"""Colour classification logic for the sensing station.

This module deliberately imports nothing from board, busio or any Adafruit
package. It turns numbers into a name and nothing else, which means it can
be tested on a laptop with no Raspberry Pi and no sensor attached.
"""

# Label returned when a reading cannot be trusted, for example the all zero
# reading the TCS34725 produces before its first integration cycle finishes.
UNKNOWN = "unknown"


def classify(r, g, b, clear):
    """Turn one raw sensor reading into a colour name.

    Args:
        r: raw red count from the TCS34725.
        g: raw green count.
        b: raw blue count.
        clear: raw unfiltered light count, that is the total light the
            sensor saw. Dividing r, g and b by clear turns the reading
            into shares of the total rather than absolute amounts, which
            keeps the rule working when the ambient lighting changes.

    Returns:
        A short colour name, suitable for printing on the OLED. Keep the
        names under about 16 characters so they fit the display.

    Recorded readings to calibrate against, from the bench session:

        coke can            r=92  g=16  b=0   lux=164.3
        green vaseline tub  r=25  g=25  b=4   lux=236.1
        first read on boot  r=0   g=0   b=0   lux=0.0

    Note that the glossy samples read r roughly equal to g with a raised
    lux, because the sensor sees its own LED reflected back rather than
    the colour of the surface.
    """
    # TODO: write the classification rule here.
    #
    # Two decisions to make, in this order:
    #
    #   1. Basis. Threshold the raw r, g and b values directly, or first
    #      divide each by clear and threshold the resulting shares? Raw is
    #      simpler to explain; shares survive a change in lighting.
    #
    #   2. Numbers. Pick the actual cut off values, using the recorded
    #      readings above and any new ones taken at the bench.
    #
    # Decide what happens with an untrustworthy reading too, and return
    # UNKNOWN for it rather than guessing a colour.
    raise NotImplementedError("classify has not been written yet")
