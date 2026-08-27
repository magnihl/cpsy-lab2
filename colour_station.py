"""Colour sensing station.

Reads a colour with the TCS34725, names it with classifier.classify and
shows the name on the SSD1306 OLED. Both devices sit on I2C bus 1 of the
Raspberry Pi Zero 2 W and share the same 3.3V and ground rails.

Run on the Pi, inside the venv:

    ~/cpsy-display-ip/cpsy/bin/python colour_station.py
"""

import time

import adafruit_ssd1306
import adafruit_tcs34725
import board
import busio

from classifier import classify

SENSOR_ADDRESS = 0x29
DISPLAY_ADDRESS = 0x3C
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64
READ_INTERVAL_SECONDS = 1.0


class ColourSensor:
    """The TCS34725 colour sensor at I2C address 0x29."""

    def __init__(self, i2c, integration_time=100, gain=4):
        self._sensor = adafruit_tcs34725.TCS34725(i2c)
        self._sensor.integration_time = integration_time
        self._sensor.gain = gain
        # The first reading is taken before a full integration cycle has
        # completed and always comes back as zeros. Throw it away so the
        # caller never sees it.
        self._sensor.color_raw

    def read(self):
        """Return one reading as a (r, g, b, clear) tuple of raw counts."""
        return self._sensor.color_raw

    @property
    def lux(self):
        """Estimated illuminance, useful for spotting specular reflection."""
        return self._sensor.lux


class Display:
    """The SSD1306 128x64 OLED at I2C address 0x3C."""

    def __init__(self, i2c, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT,
                 address=DISPLAY_ADDRESS):
        self._oled = adafruit_ssd1306.SSD1306_I2C(width, height, i2c,
                                                  addr=address)
        self.blank()

    def show(self, label, reading):
        """Draw the colour name with the raw numbers that produced it."""
        r, g, b, clear = reading
        self._oled.fill(0)
        self._oled.text(label, 0, 0, 1)
        self._oled.text("R {} G {} B {}".format(r, g, b), 0, 20, 1)
        self._oled.text("Clear {}".format(clear), 0, 32, 1)
        self._oled.show()

    def blank(self):
        """Clear the panel.

        The OLED holds its last image through a reboot because the reset
        line is not power cycled, so a station that exits without blanking
        leaves a stale colour on screen that looks like a live reading.
        """
        self._oled.fill(0)
        self._oled.show()


class Station:
    """Ties the sensor, the classifier and the display into one loop."""

    def __init__(self, sensor, display, interval=READ_INTERVAL_SECONDS):
        self._sensor = sensor
        self._display = display
        self._interval = interval

    def step(self):
        """Run one pass and return the label that was shown.

        Kept separate from run so a single pass can be triggered by hand
        while testing at the bench.
        """
        reading = self._sensor.read()
        label = classify(*reading)
        self._display.show(label, reading)
        return label

    def run(self):
        """Read, classify and display forever, pausing between passes."""
        while True:
            self.step()
            time.sleep(self._interval)


def main():
    i2c = busio.I2C(board.SCL, board.SDA)
    display = Display(i2c)
    sensor = ColourSensor(i2c)
    station = Station(sensor, display)
    try:
        station.run()
    except KeyboardInterrupt:
        pass
    finally:
        display.blank()


if __name__ == "__main__":
    main()
