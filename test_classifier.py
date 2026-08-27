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

# Readings recorded from the real sensor at the bench on 2026-08-27, with
# integration_time 100 and gain 4. Readings from earlier sessions were taken
# at unknown exposure settings and disagreed with these by more than the gap
# between two different colours, so they have been dropped rather than mixed
# in.
CLASSIFY_CASES = [
    Case(
        sample="first read after init",
        reading=(0, 0, 0, 0),
        expected=classifier.UNKNOWN,
        criterion="No integration cycle has finished, so the reading holds "
                  "no colour information and must not be named a colour.",
    ),
    Case(
        sample="red cloth, held close",
        reading=(1555, 190, 245, 1667),
        expected="red",
        criterion="A strongly coloured matte sample is the easiest case "
                  "there is. If this fails, nothing else will work.",
    ),
    Case(
        sample="red cloth, held further away",
        reading=(595, 85, 102, 614),
        expected="red",
        criterion="Same cloth at roughly a third of the light. Distance to "
                  "the sensor must not change the label, which is the whole "
                  "reason the rule normalises before comparing.",
    ),
    Case(
        sample="coke can, glossy red",
        reading=(3550, 809, 581, 4785),
        expected="red",
        criterion="A glossy surface reflects the onboard LED and reads less "
                  "saturated than matte cloth. It must still come out red.",
    ),
    Case(
        sample="red tie, dark red",
        reading=(162, 44, 40, 170),
        expected="red",
        criterion="A dark sample returns few counts, 170 clear against the "
                  "coke can's 4785. Shares still carry the colour, so the "
                  "label must not depend on how much light came back.",
    ),
    Case(
        sample="red tie, held loosely",
        reading=(150, 61, 43, 232),
        expected="red",
        criterion="More light arrived than the reading above, 232 against "
                  "170, yet the sample reads less red, because room light "
                  "leaked in around the edges. The furthest red from the "
                  "reference row and so the case that sets MAX_DISTANCE.",
    ),
    Case(
        sample="sensor pulled away from the tie",
        reading=(77, 44, 47, 110),
        expected=classifier.UNKNOWN,
        criterion="With no sample against it the sensor reads room light, "
                  "which is warm and so looks reddish. Must not be reported "
                  "as a colour just because red happens to be nearest.",
    ),
    Case(
        sample="yellow book",
        reading=(3291, 1417, 610, 5304),
        expected="yellow",
        criterion="The nearest red row, the loosely held tie, sits 0.067 "
                  "away. Yellow is the tightest call the table has to make, "
                  "so this is the case that guards it.",
    ),
    Case(
        sample="yellow book, held closer",
        reading=(7550, 3853, 1494, 13050),
        expected="yellow",
        criterion="Two and a half times the light of the reading above. "
                  "Must not change the label.",
    ),
    Case(
        sample="blue tie",
        reading=(178, 169, 238, 563),
        expected=classifier.UNKNOWN,
        criterion="No blue row has been added yet. An unknown colour must "
                  "report unknown rather than take the name of whichever "
                  "known row happens to be least far away.",
    ),
    # TODO: re-scan the green vaseline tub at these exposure settings, and
    # add a row per remaining colour.
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
