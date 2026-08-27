"""Reads a colour, names it, shows it on the OLED.

Run on the Pi:  ~/cpsy-display-ip/cpsy/bin/python colour_station.py
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
    """TCS34725 at 0x29."""

    def __init__(self, i2c, address=SENSOR_ADDRESS, integration_time=100,
                 gain=4):
        self._sensor = adafruit_tcs34725.TCS34725(i2c, address=address)
        self._sensor.integration_time = integration_time
        self._sensor.gain = gain
        # First read happens before an integration cycle finishes and is
        # always zeros.
        _ = self._sensor.color_raw

    def read(self):
        return self._sensor.color_raw

    @property
    def lux(self):
        return self._sensor.lux


class Display:
    """SSD1306 128x64 at 0x3C."""

    def __init__(self, i2c, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT,
                 address=DISPLAY_ADDRESS):
        self._oled = adafruit_ssd1306.SSD1306_I2C(width, height, i2c,
                                                  addr=address)
        self.blank()

    def show(self, label, reading):
        r, g, b, clear = reading
        self._oled.fill(0)
        self._oled.text(label, 0, 0, 1)
        self._oled.text("R {} G {} B {}".format(r, g, b), 0, 20, 1)
        self._oled.text("Clear {}".format(clear), 0, 32, 1)
        self._oled.show()

    def blank(self):
        # The panel keeps its last image through a reboot, so exiting
        # without blanking leaves a stale reading on screen.
        self._oled.fill(0)
        self._oled.show()


class Station:
    def __init__(self, sensor, display, interval=READ_INTERVAL_SECONDS):
        self._sensor = sensor
        self._display = display
        self._interval = interval

    def step(self):
        """One pass. Separate from run so it can be triggered by hand."""
        reading = self._sensor.read()
        label = classify(*reading)
        self._display.show(label, reading)
        return label

    def run(self):
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
