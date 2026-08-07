from difflib import get_close_matches

from draft_board import DraftBoard
from draft_pick import DraftPick
from draft_state import DraftState
from league import League
from loader import load_players
from market import DraftMarket
from player import Player
from preferences import normalize_name


class LiveDraftSession:
    def __init__(
        self,
        user_team_number: int,
        completed_player_names: tuple[
            str,
            ...,
        ] = (),
    ) -> None:
        if not 1 <= user_team_number <= 10:
            raise ValueError(
                "Draft slot must be between 1 and 10."
            )

        self.players = load_players()

        self.players_by_name = {
            normalize_name(player.name): player
            for player in self.players
        }

        self.board = DraftBoard(
            self.players
        )

        self.league = League()

        self.market = DraftMarket(
            players=self.players,
            seed=0,
        )

        self.state = DraftState(
            league=self.league,
            board=self.board,
            market=self.market,
            user_team_number=user_team_number,
        )

        self.draft_results: list[
            DraftPick
        ] = []

        self.state.current_pick = 1

        self.restore_picks(
            completed_player_names
        )

    @property
    def user_team_number(self) -> int:
        return self.state.user_team_number

    @property
    def current_pick(self) -> int:
        return len(self.draft_results) + 1

    @property
    def is_complete(self) -> bool:
        return self.current_pick > len(
            self.league.draft_order
        )

    @property
    def current_team_number(
        self,
    ) -> int | None:
        if self.is_complete:
            return None

        return self.league.draft_order[
            self.current_pick - 1
        ]

    @property
    def is_user_turn(self) -> bool:
        return (
            self.current_team_number
            == self.user_team_number
        )

    @property
    def next_user_pick(self) -> int | None:
        for overall_pick in range(
            self.current_pick + 1,
            len(self.league.draft_order) + 1,
        ):
            team_number = (
                self.league.draft_order[
                    overall_pick - 1
                ]
            )

            if (
                team_number
                == self.user_team_number
            ):
                return overall_pick

        return None

    @property
    def completed_player_names(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            draft_pick.player.name
            for draft_pick
            in self.draft_results
        )

    def player_for_name(
        self,
        player_name: str,
    ) -> Player | None:
        return self.players_by_name.get(
            normalize_name(player_name)
        )

    def is_player_available(
        self,
        player_name: str,
    ) -> bool:
        player = self.player_for_name(
            player_name
        )

        if player is None:
            return False

        return self.board.is_available(
            player
        )

    def name_suggestions(
        self,
        player_name: str,
        limit: int = 5,
    ) -> tuple[str, ...]:
        normalized_target = normalize_name(
            player_name
        )

        normalized_names = list(
            self.players_by_name.keys()
        )

        matches = get_close_matches(
            normalized_target,
            normalized_names,
            n=limit,
            cutoff=0.55,
        )

        return tuple(
            self.players_by_name[
                match
            ].name
            for match in matches
        )

    def restore_picks(
        self,
        player_names: tuple[str, ...],
    ) -> None:
        if not player_names:
            return

        if len(player_names) > len(
            self.league.draft_order
        ):
            raise ValueError(
                "Saved draft contains too many picks."
            )

        for player_name in player_names:
            self.record_pick(
                player_name
            )

    def record_pick(
        self,
        player_name: str,
    ) -> DraftPick:
        if self.is_complete:
            raise RuntimeError(
                "The draft is already complete."
            )

        player = self.player_for_name(
            player_name
        )

        if player is None:
            suggestions = self.name_suggestions(
                player_name
            )

            suggestion_text = ""

            if suggestions:
                suggestion_text = (
                    " Did you mean: "
                    + ", ".join(suggestions)
                    + "?"
                )

            raise ValueError(
                f"Player not found: {player_name}."
                f"{suggestion_text}"
            )

        if not self.board.is_available(
            player
        ):
            raise ValueError(
                f"{player.name} has already "
                f"been drafted."
            )

        overall_pick = self.current_pick
        team_number = (
            self.current_team_number
        )

        if team_number is None:
            raise RuntimeError(
                "Could not determine the "
                "team on the clock."
            )

        team = self.league.teams[
            team_number - 1
        ]

        team.add_player(
            player
        )

        self.board.draft_player(
            player
        )

        round_number = (
            (overall_pick - 1)
            // self.league.num_teams
        ) + 1

        pick_in_round = (
            (overall_pick - 1)
            % self.league.num_teams
        ) + 1

        draft_pick = DraftPick(
            overall=overall_pick,
            round_number=round_number,
            pick_in_round=pick_in_round,
            team_number=team_number,
            player=player,
        )

        self.draft_results.append(
            draft_pick
        )

        self.state.current_pick = (
            self.current_pick
        )

        return draft_pick


    def undo_last_pick(self) -> DraftPick:
        """Undo one pick in place without rebuilding/replaying the full session."""
        if not self.draft_results:
            raise RuntimeError("There is no draft pick to undo.")

        draft_pick = self.draft_results.pop()
        player = draft_pick.player
        team = self.league.teams[draft_pick.team_number - 1]

        # record_pick() always appends to that team's roster, so the matching
        # player can be removed directly while preserving draft order.
        for index in range(len(team.players) - 1, -1, -1):
            if team.players[index].name == player.name:
                team.players.pop(index)
                break

        self.board.restore_player(player)
        self.state.current_pick = self.current_pick
        return draft_pick

    def available_players(
        self,
        limit: int | None = None,
    ) -> list[Player]:
        players = (
            self.board.available_players
        )

        if limit is None:
            return players.copy()

        return players[:limit]