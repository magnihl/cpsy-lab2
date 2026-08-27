"""Test cases for classifier.classify.

Every case is a real reading recorded from the sensor at the bench, the
label the rule is expected to produce for it, and the reason that label is
the right pass criterion. Nothing here touches the I2C bus, so the whole
table runs on a laptop with the Raspberry Pi switched off.

Run with:

    python3 test_classifier.py
"""

from collections import namedtuple

import classifier

# Marks a reading whose clear value was not written down at the bench.
# Cases carrying it are skipped until the reading is taken again.
NOT_RECORDED = None

Case = namedtuple("Case", "sample reading expected criterion")

CASES = [
    Case(
        sample="first read after init",
        reading=(0, 0, 0, 0),
        expected=classifier.UNKNOWN,
        criterion="No integration cycle has finished, so the reading carries "
                  "no colour information and must not be named as a colour.",
    ),
    Case(
        sample="coke can",
        reading=(92, 16, NOT_RECORDED, NOT_RECORDED),
        expected=None,
        criterion="Red is far above green and blue, so the rule should name "
                  "it red.",
    ),
    Case(
        sample="coke can, repeat read",
        reading=(92, 16, NOT_RECORDED, NOT_RECORDED),
        expected=None,
        criterion="Byte identical to the previous read, so it must produce "
                  "the identical label. Confirms the rule is deterministic.",
    ),
    Case(
        sample="green vaseline tub",
        reading=(25, 25, NOT_RECORDED, NOT_RECORDED),
        expected=None,
        criterion="A glossy surface reflects the onboard LED, so red and "
                  "green read equal despite the tub being green. Decide "
                  "whether the rule names this green or reports unknown.",
    ),
    # TODO: add a case per colour card, and one taken with the LED tied to
    # ground so the sample is lit only by the room.
]


def run():
    passed = failed = skipped = 0

    for case in CASES:
        if case.expected is None:
            print("SKIP {}: expected label not chosen yet".format(case.sample))
            skipped += 1
            continue
        if NOT_RECORDED in case.reading:
            print("SKIP {}: reading incomplete, clear value not recorded"
                  .format(case.sample))
            skipped += 1
            continue

        try:
            actual = classifier.classify(*case.reading)
        except NotImplementedError:
            print("SKIP {}: classify has not been written yet"
                  .format(case.sample))
            skipped += 1
            continue

        if actual == case.expected:
            print("PASS {}: {} gave {}"
                  .format(case.sample, case.reading, actual))
            passed += 1
        else:
            print("FAIL {}: {} gave {}, expected {}"
                  .format(case.sample, case.reading, actual, case.expected))
            failed += 1

    print("\n{} passed, {} failed, {} skipped"
          .format(passed, failed, skipped))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(run())
