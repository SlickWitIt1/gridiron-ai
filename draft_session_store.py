import json
from pathlib import Path
from typing import Any


DEFAULT_SAVE_PATH = Path(
    "../output/live_draft_session.json"
)


class DraftSessionStore:
    def __init__(
        self,
        save_path: Path = DEFAULT_SAVE_PATH,
    ) -> None:
        self.save_path = save_path

    def exists(self) -> bool:
        return self.save_path.exists()

    def save(
        self,
        draft_slot: int,
        simulations: int,
        drafted_player_names: tuple[str, ...],
    ) -> None:
        self.save_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "version": 1,
            "draft_slot": draft_slot,
            "simulations": simulations,
            "drafted_player_names": list(
                drafted_player_names
            ),
        }

        temporary_path = self.save_path.with_suffix(
            ".tmp"
        )

        temporary_path.write_text(
            json.dumps(
                payload,
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary_path.replace(
            self.save_path
        )

    def load(self) -> dict[str, Any]:
        if not self.exists():
            raise FileNotFoundError(
                "No saved live draft was found."
            )

        try:
            payload = json.loads(
                self.save_path.read_text(
                    encoding="utf-8"
                )
            )

        except json.JSONDecodeError as error:
            raise ValueError(
                "The saved draft file is damaged "
                "or contains invalid JSON."
            ) from error

        if payload.get("version") != 1:
            raise ValueError(
                "The saved draft uses an "
                "unsupported version."
            )

        draft_slot = payload.get(
            "draft_slot"
        )

        simulations = payload.get(
            "simulations"
        )

        drafted_player_names = payload.get(
            "drafted_player_names"
        )

        if not isinstance(draft_slot, int):
            raise ValueError(
                "Saved draft slot is invalid."
            )

        if not isinstance(simulations, int):
            raise ValueError(
                "Saved simulation count is invalid."
            )

        if not isinstance(
            drafted_player_names,
            list,
        ):
            raise ValueError(
                "Saved draft history is invalid."
            )

        if not all(
            isinstance(player_name, str)
            for player_name
            in drafted_player_names
        ):
            raise ValueError(
                "Saved player names are invalid."
            )

        return {
            "draft_slot": draft_slot,
            "simulations": simulations,
            "drafted_player_names": tuple(
                drafted_player_names
            ),
        }

    def delete(self) -> None:
        if self.exists():
            self.save_path.unlink()