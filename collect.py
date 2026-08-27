"""Record bench readings for the reference table.

Hold a colour card in front of the sensor, type what it is, press enter.
Prints the raw counts, appends them to readings.csv so nothing is lost,
and prints a line ready to paste straight into REFERENCES in classifier.py.

Run on the Pi, inside the venv:

    ~/cpsy-display-ip/cpsy/bin/python collect.py
"""

import csv
import os

import board
import busio

import classifier
from colour_station import ColourSensor

OUTPUT_FILE = "readings.csv"
COLUMNS = ["sample", "r", "g", "b", "clear", "lux",
           "red_share", "green_share", "blue_share"]


def main():
    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = ColourSensor(i2c)

    new_file = not os.path.exists(OUTPUT_FILE)
    with open(OUTPUT_FILE, "a", newline="") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(COLUMNS)

        print("Hold a card in front of the sensor, type what it is, press "
              "enter.")
        print("Press enter on an empty name to stop.\n")

        while True:
            sample = input("sample: ").strip()
            if not sample:
                break

            r, g, b, clear = sensor.read()
            lux = sensor.lux
            shares = classifier.normalise(r, g, b)

            if shares is None:
                print("  no light reached the sensor, try again\n")
                continue

            writer.writerow([sample, r, g, b, clear, round(lux, 1)]
                            + [round(share, 4) for share in shares])
            handle.flush()

            print("  raw     r {} g {} b {} clear {} lux {}"
                  .format(r, g, b, clear, round(lux, 1)))
            print('  paste   "{}": ({:.3f}, {:.3f}, {:.3f}),\n'
                  .format(sample, *shares))

    print("Saved to {}".format(OUTPUT_FILE))


if __name__ == "__main__":
    main()
