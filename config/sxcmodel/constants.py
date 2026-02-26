MAX_TIME_SECONDS = 90 * 60  # 1.5 hours in seconds
QUESTIONS_PER_SECTION = 20

# Subjects whose order is randomized
RANDOMIZED_SUBJECTS = ['PHY', 'CHE', 'BIO', 'MAT']

# Subjects displayed in DB order (preserved)
ORDERED_SUBJECTS = ['ENG', 'IQ_GK']

# All subjects in display order (randomized ones first, then ordered)
# The actual sequence is determined at attempt-creation time.
ALL_SUBJECTS = RANDOMIZED_SUBJECTS + ORDERED_SUBJECTS

# Scoring formula weights
MARKS_WEIGHT = 0.80   # 80% of final grade from marks
TIME_WEIGHT = 0.20    # 20% of final grade from speed bonus