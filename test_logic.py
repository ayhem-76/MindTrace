from assessment_logic import next_difficulty, wilson_interval


assert next_difficulty("Moderate", True) == "Difficult"
assert next_difficulty("Difficult", False) == "Moderate"
assert next_difficulty("Challenging", True) == "Challenging"
assert wilson_interval(0, 0) == (0, 0)

print("ALL LOGIC TESTS PASSED")
