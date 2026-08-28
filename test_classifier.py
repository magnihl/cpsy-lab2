"""Test cases for the classifier: input, expected output, pass criterion.

Readings were recorded from the sensor on 2026-08-27 at integration_time
100 and gain 4. Nothing here touches I2C, so it runs without the Pi.

    python3 test_classifier.py
"""

from collections import namedtuple

import classifier

Case = namedtuple("Case", "sample reading expected criterion")

CASES = [
    Case("first read after init", (0, 0, 0, 0), classifier.UNKNOWN,
         "No integration cycle has finished, so there is no colour to name."),
    Case("red cloth, close", (1555, 190, 245, 1667), "red",
         "A strong matte sample is the easiest case there is."),
    Case("red cloth, further away", (595, 85, 102, 614), "red",
         "A third of the light, same cloth, so the label must not change."),
    Case("coke can, glossy", (3550, 809, 581, 4785), "red",
         "Gloss reflects the LED and reads less saturated, still red."),
    Case("red tie, dark", (162, 44, 40, 170), "red",
         "Clear 170 against the can's 4785, so darkness must not matter."),
    Case("red tie, held loosely", (150, 61, 43, 232), "red",
         "More light than the reading above but less red, because room "
         "light leaked in. The furthest red from its row."),
    Case("sensor pulled off the tie", (77, 44, 47, 110), classifier.UNKNOWN,
         "Room light is warm and looks reddish. Must not be named a colour."),
    Case("yellow book", (3291, 1417, 610, 5304), "yellow",
         "The nearest red row is 0.067 away, the tightest call in the table."),
    Case("yellow book, closer", (7550, 3853, 1494, 13050), "yellow",
         "Two and a half times the light, same label."),
    Case("blue tie", (178, 169, 238, 563), "blue",
         "A dark navy reads only 0.39 blue, because a dark sample returns "
         "little of anything. Still 0.179 from light blue."),
    Case("blue tie, second reading", (199, 171, 216, 518), "blue",
         "The two tie readings differ by 0.052, wider than any other "
         "object here, so this is the loosest row in the table."),
    Case("green book", (2372, 2595, 963, 6162), "green",
         "Best separated colour in the table at 0.241 from its neighbour."),
    Case("green book, partly off", (1168, 798, 357, 2356), classifier.UNKNOWN,
         "Sits 0.101 from yellow and 0.144 from green, so the nearest row "
         "is the wrong colour and only MAX_DISTANCE catches it."),
    Case("light blue", (334, 658, 535, 1636), "light blue",
         "Green reads higher than blue here, because the sensor's green "
         "channel is the most sensitive. Matching a measured row still works."),
    Case("light blue, more light", (400, 833, 697, 2089), "light blue",
         "A third more light, same label."),
    Case("light blue, sensor lifted", (193, 263, 232, 680), classifier.UNKNOWN,
         "Lands 0.081 from the nearest row against a limit of 0.05, so it "
         "is refused with room to spare."),
    Case("light purple", (3219, 2197, 1565, 7143), "purple",
         "Nearest row of another colour is 0.147 away, the best separated "
         "colour in the table."),
    Case("light purple, less light", (1207, 718, 527, 2453), "purple",
         "A third of the light, same object, same label."),
    Case("darker purple", (2065, 1866, 1401, 5542), "purple",
         "A second purple object 0.105 from the first, so purple needs two "
         "rows the way red needs four."),
    Case("darker purple, less light", (579, 481, 356, 1448), "purple",
         "A quarter of the light off the same object."),
    Case("orange highlighter", (4491, 2072, 867, 7654), "yellow",
         "Orange is not in the table and lands on yellow. Recorded on "
         "purpose: eight readings of two orange objects all did this, and "
         "orange sits closer to yellow than repeat readings of one object "
         "sit to each other."),
]

NORMALISE_CASES = [
    Case("shares sum to one", (92, 16, 0), 1.0,
         "Shares of a total must add up to 1.0."),
    Case("brightness drops out", (46, 8, 0), classifier.normalise(92, 16, 0),
         "Half the light off the same surface must give the same shares."),
    Case("no light at all", (0, 0, 0), None,
         "Nothing to divide by, so it reports that instead of crashing."),
]

# Two rows with different names must sit further apart than the spread of
# repeated readings of one object, or the label comes down to noise.
MIN_SEPARATION = 0.06


def check(sample, actual, expected):
    if actual == expected:
        print("PASS {}: got {}".format(sample, actual))
        return True
    print("FAIL {}: got {}, expected {}".format(sample, actual, expected))
    return False


def check_separation():
    gaps = [(classifier.distance(row_a, row_b), name_a, name_b)
            for i, (name_a, row_a) in enumerate(classifier.REFERENCES)
            for name_b, row_b in classifier.REFERENCES[i + 1:]
            if name_a != name_b]
    gap, name_a, name_b = min(gaps)

    if gap >= MIN_SEPARATION:
        print("PASS row separation: {} and {} are {:.3f} apart"
              .format(name_a, name_b, gap))
        return True
    print("FAIL row separation: {} and {} only {:.3f} apart"
          .format(name_a, name_b, gap))
    return False


def run():
    results = [check_separation()]

    for case in NORMALISE_CASES:
        actual = classifier.normalise(*case.reading)
        if case.sample == "shares sum to one":
            actual = round(sum(actual), 6)
        results.append(check(case.sample, actual, case.expected))

    for case in CASES:
        results.append(
            check(case.sample, classifier.classify(*case.reading),
                  case.expected))

    passed = results.count(True)
    print("\n{} passed, {} failed".format(passed, len(results) - passed))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(run())
