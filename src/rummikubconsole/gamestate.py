"""Migration support to move pickled gamestates to rummikub_solver"""

from typing import Any

from rummikub_solver import GameState as NewGameState


class GameState:
    def __new__(cls) -> NewGameState:
        # we would only ever get to this point if a shelve for an older version
        # of RummikubConsole is being loaded, in case we need to migrate those
        # to a new rummikub_solver.GameState.

        def __setstate__(self: NewGameState, state: dict[str, Any]):
            from ._console import current_ruleset_empty_game

            tmap = current_ruleset_empty_game._tile_map  # type: ignore[reportPrivateUsage]
            self.__init__(tmap, state["table"].elements(), state["rack"].elements())
            self.initial = state["initial"]

        NewGameState.__setstate__ = __setstate__  # type: ignore[reportAttributeAccessIssue]
        return NewGameState.__new__(NewGameState)
