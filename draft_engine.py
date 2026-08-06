from decision_engine import DecisionEngine
from draft_pick import DraftPick
from draft_state import DraftState
from player import Player
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
        initial_player_names: tuple[str, ...] = (),
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

        self.players_by_name = {
            normalize_name(player.name): player
            for player in self.market.sorted_players
        }

        self.draft_results: list[DraftPick] = []

        self._apply_initial_picks(
            initial_player_names
        )

    def _player_for_name(
        self,
        player_name: str,
    ) -> Player:
        player = self.players_by_name.get(
            normalize_name(player_name)
        )

        if player is None:
            raise ValueError(
                f"Initial drafted player was not found: "
                f"{player_name}"
            )

        return player

    def _apply_initial_picks(
        self,
        player_names: tuple[str, ...],
    ) -> None:
        if len(player_names) > len(
            self.league.draft_order
        ):
            raise ValueError(
                "Initial draft history contains too many picks."
            )

        for overall_pick, player_name in enumerate(
            player_names,
            start=1,
        ):
            team_number = self.league.draft_order[
                overall_pick - 1
            ]

            team = self.league.teams[
                team_number - 1
            ]

            player = self._player_for_name(
                player_name
            )

            if not self.board.is_available(player):
                raise ValueError(
                    f"{player.name} appears more than once "
                    f"in the initial draft history."
                )

            team.add_player(player)
            self.board.draft_player(player)

            round_number = (
                (overall_pick - 1)
                // self.league.num_teams
            ) + 1

            pick_in_round = (
                (overall_pick - 1)
                % self.league.num_teams
            ) + 1

            self.draft_results.append(
                DraftPick(
                    overall=overall_pick,
                    round_number=round_number,
                    pick_in_round=pick_in_round,
                    team_number=team_number,
                    player=player,
                )
            )

        self.state.current_pick = (
            len(self.draft_results) + 1
        )

    def run(
        self,
        print_picks: bool = True,
        max_overall_pick: int | None = None,
    ) -> list[DraftPick]:
        if print_picks:
            print("\n==============================")
            print("      STARTING DRAFT")
            print("==============================\n")

        starting_pick = (
            len(self.draft_results) + 1
        )

        for overall_pick in range(
            starting_pick,
            len(self.league.draft_order) + 1,
        ):
            if (
                max_overall_pick is not None
                and overall_pick > max_overall_pick
            ):
                break

            team_number = self.league.draft_order[
                overall_pick - 1
            ]

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

        self.state.current_pick = (
            len(self.draft_results) + 1
        )

        if print_picks:
            print("\n==============================")
            print("      DRAFT COMPLETE")
            print("==============================")

        return self.draft_results