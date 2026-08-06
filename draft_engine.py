from decision_engine import DecisionEngine
from draft_pick import DraftPick
from draft_state import DraftState
from preferences import normalize_name


class DraftEngine:
    def __init__(
        self,
        state: DraftState,
        approved_players: set[str] | None = None,
        forbidden_players_by_pick: dict[
            int,
            set[str],
        ] | None = None,
    ):
        self.state = state

        self.league = state.league
        self.board = state.board
        self.market = state.market

        self.user_team_number = (
            state.user_team_number
        )

        self.approved_players = approved_players

        self.forbidden_players_by_pick = (
            forbidden_players_by_pick or {}
        )

        self.decision_engine = DecisionEngine(
            self.market
        )

        self.draft_results: list[DraftPick] = []

    def run(
        self,
        print_picks: bool = True,
        max_overall_pick: int | None = None,
    ) -> list[DraftPick]:
        self.draft_results = []

        if print_picks:
            print("\n==============================")
            print("      STARTING DRAFT")
            print("==============================\n")

        for overall_pick, team_number in enumerate(
            self.league.draft_order,
            start=1,
        ):
            if (
                max_overall_pick is not None
                and overall_pick > max_overall_pick
            ):
                break

            self.state.current_pick = overall_pick

            team = self.league.teams[
                team_number - 1
            ]

            current_round = (
                (overall_pick - 1)
                // self.league.num_teams
            ) + 1

            team_approved_players = None
            excluded_players: set[str] = set()

            if team_number == self.user_team_number:
                team_approved_players = (
                    self.approved_players
                )

                excluded_players = {
                    normalize_name(player_name)
                    for player_name in (
                        self.forbidden_players_by_pick.get(
                            overall_pick,
                            set(),
                        )
                    )
                }

            player = self.decision_engine.choose_player(
                team=team,
                available_players=(
                    self.board.available_players
                ),
                available_names=(
                    self.board.available_names
                ),
                current_round=current_round,
                approved_players=(
                    team_approved_players
                ),
                excluded_players=excluded_players,
            )

            if player is None:
                raise RuntimeError(
                    f"Team {team_number} had no "
                    f"eligible player available at "
                    f"overall pick {overall_pick}."
                )

            team.add_player(player)
            self.board.draft_player(player)

            pick_in_round = (
                (overall_pick - 1)
                % self.league.num_teams
            ) + 1

            draft_pick = DraftPick(
                overall=overall_pick,
                round_number=current_round,
                pick_in_round=pick_in_round,
                team_number=team_number,
                player=player,
            )

            self.draft_results.append(
                draft_pick
            )

            if print_picks:
                marker = (
                    "  <-- YOUR PICK"
                    if team_number
                    == self.user_team_number
                    else ""
                )

                print(
                    f"{draft_pick}{marker}"
                )

        if print_picks:
            print("\n==============================")
            print("      DRAFT COMPLETE")
            print("==============================")

        return self.draft_results