NUM_TEAMS = 10
NUM_ROUNDS = 16

ROSTER_SIZE = 16
BENCH_SIZE = 7
IR_SLOTS = 1

STARTER_REQUIREMENTS = {
    "QB": 1,
    "RB": 2,
    "WR": 2,
    "TE": 1,
    "DST": 1,
    "K": 1,
}

FLEX_SLOTS = 1
FLEX_ELIGIBLE_POSITIONS = {"RB", "WR", "TE"}

# ESPN's actual roster maximums from your league settings.
POSITION_MAXIMUMS = {
    "QB": 4,
    "RB": 8,
    "WR": 8,
    "TE": 3,
    "DST": 3,
    "K": 3,
}

USER_TEAM_NUMBER = 7


SCORING = {
    # Passing
    "passing_yard": 0.04,
    "passing_td": 6.0,
    "interception_thrown": -2.0,
    "passing_two_point_conversion": 2.0,

    # Rushing
    "rushing_yard": 0.10,
    "rushing_td": 6.0,
    "rushing_two_point_conversion": 2.0,

    # Receiving
    "receiving_yard": 0.10,
    "reception": 0.50,
    "receiving_td": 6.0,
    "receiving_two_point_conversion": 2.0,

    # Miscellaneous offense
    "fumble_lost": -2.0,
    "kick_return_td": 6.0,
    "punt_return_td": 6.0,
    "offensive_fumble_recovery_td": 6.0,

    # Kicking
    "pat_made": 1.0,
    "pat_missed": -1.0,
    "field_goal_missed": -1.0,
    "field_goal_made_0_39": 3.0,
    "field_goal_made_40_49": 4.0,
    "field_goal_made_50_59": 5.0,
    "field_goal_made_60_plus": 6.0,

    # Defense and special teams
    "defensive_sack": 1.0,
    "defensive_interception": 2.0,
    "defensive_fumble_recovery": 2.0,
    "defensive_safety": 2.0,
    "blocked_kick": 2.0,
    "defensive_td": 6.0,
    "defensive_two_point_return": 2.0,
    "defensive_one_point_safety": 1.0,

    # Points allowed
    "points_allowed_0": 5.0,
    "points_allowed_1_6": 4.0,
    "points_allowed_7_13": 3.0,
    "points_allowed_14_17": 1.0,
    "points_allowed_18_27": 0.0,
    "points_allowed_28_34": -1.0,
    "points_allowed_35_45": -3.0,
    "points_allowed_46_plus": -5.0,

    # Total yards allowed
    "yards_allowed_under_100": 5.0,
    "yards_allowed_100_199": 3.0,
    "yards_allowed_200_299": 2.0,
    "yards_allowed_300_349": 0.0,
    "yards_allowed_350_399": -1.0,
    "yards_allowed_400_449": -3.0,
    "yards_allowed_450_499": -5.0,
    "yards_allowed_500_549": -6.0,
    "yards_allowed_550_plus": -7.0,
}