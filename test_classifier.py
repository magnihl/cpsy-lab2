"""Test cases for the classifier.

Every case states an input, the expected output, and the criterion that
makes that output the right answer. Nothing here touches the I2C bus, so
the whole table runs on a laptop with the Raspberry Pi switched off.

Run with:

    python3 test_classifier.py
"""

from collections import namedtuple

import classifier

# Marks a clear value that was not written down at the bench. The rule
# normalises by r + g + b rather than by clear, so clear feeds only the
# minimum light gate. Substituting MIN_CLEAR lets these cases run while
# leaving the gate honest, since it neither passes nor fails on clear.
NOT_RECORDED = None

Case = namedtuple("Case", "sample reading expected criterion")

# Readings recorded from the real sensor at the bench.
CLASSIFY_CASES = [
    Case(
        sample="first read after init",
        reading=(0, 0, 0, 0),
        expected=classifier.UNKNOWN,
        criterion="No integration cycle has finished, so the reading holds "
                  "no colour information and must not be named a colour.",
    ),
    Case(
        sample="coke can",
        reading=(92, 16, 0, NOT_RECORDED),
        expected="red",
        criterion="Red dominates green and blue by a wide margin, so the "
                  "nearest reference must be the red row.",
    ),
    Case(
        sample="coke can, repeat read",
        reading=(92, 16, 0, NOT_RECORDED),
        expected="red",
        criterion="Byte identical to the previous read, so it must produce "
                  "the identical label. Confirms the rule is deterministic.",
    ),
    Case(
        sample="green vaseline tub",
        reading=(25, 25, 4, NOT_RECORDED),
        expected=None,
        criterion="A glossy surface reflects the onboard LED, so red and "
                  "green read equal despite the tub being green. Decide "
                  "whether this should name green or report unknown, then "
                  "fill the expected label in.",
    ),
    # TODO: add a case per colour card, and one taken with the LED tied to
    # ground so the sample is lit only by the room.
]

# Normalising is what makes the reference table survive a lighting change,
# so it is worth testing on its own rather than only through classify.
NORMALISE_CASES = [
    Case(
        sample="shares sum to one",
        reading=(92, 16, 0),
        expected=1.0,
        criterion="Normalising splits a reading into shares of the total, "
                  "so the three shares must always add up to 1.0.",
    ),
    Case(
        sample="brightness drops out",
        reading=(46, 8, 0),
        expected=classifier.normalise(92, 16, 0),
        criterion="Half the light off the same surface must normalise to "
                  "the same shares, otherwise the table would need "
                  "re-tuning every time the lighting changed.",
    ),
    Case(
        sample="no light at all",
        reading=(0, 0, 0),
        expected=None,
        criterion="A reading with no light cannot be split into shares, so "
                  "normalise reports that rather than dividing by zero.",
    ),
]


def fill_clear(reading):
    """Substitute an unrecorded clear value with the gate threshold."""
    r, g, b, clear = reading
    if clear is NOT_RECORDED:
        clear = classifier.MIN_CLEAR
    return (r, g, b, clear)


def check(sample, actual, expected):
    if actual == expected:
        print("PASS {}: got {}".format(sample, actual))
        return "pass"
    print("FAIL {}: got {}, expected {}".format(sample, actual, expected))
    return "fail"


def run():
    results = []

    for case in NORMALISE_CASES:
        actual = classifier.normalise(*case.reading)
        if case.sample == "shares sum to one":
            actual = round(sum(actual), 6)
        results.append(check(case.sample, actual, case.expected))

    for case in CLASSIFY_CASES:
        if case.expected is None:
            print("SKIP {}: expected label not chosen yet".format(case.sample))
            results.append("skip")
            continue
        try:
            actual = classifier.classify(*fill_clear(case.reading))
        except NotImplementedError:
            print("SKIP {}: REFERENCES is still empty".format(case.sample))
            results.append("skip")
            continue
        results.append(check(case.sample, actual, case.expected))

    print("\n{} passed, {} failed, {} skipped".format(
        results.count("pass"), results.count("fail"), results.count("skip")))
    return 1 if "fail" in results else 0


if __name__ == "__main__":
    raise SystemExit(run())
