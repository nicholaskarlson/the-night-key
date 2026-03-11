from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GameState:
    day: int = 1
    energy: int = 5
    support: int = 3
    guilt: int = 2
    warmth: int = 2
    flags: dict[str, bool] = field(default_factory=dict)

    def has_flag(self, flag: str) -> bool:
        return bool(self.flags.get(flag, False))

    def has_flags(self, flags: Iterable[str]) -> bool:
        return all(self.has_flag(f) for f in flags)

    def any_flags(self, flags: Iterable[str]) -> bool:
        return any(self.has_flag(f) for f in flags)

    def with_flags(
        self,
        *,
        set_flags: Iterable[str] = (),
        clear_flags: Iterable[str] = (),
    ) -> GameState:
        new_flags = dict(self.flags)
        for f in set_flags:
            f = str(f).strip()
            if not f:
                continue
            new_flags[f] = True
        for f in clear_flags:
            f = str(f).strip()
            if not f:
                continue
            new_flags.pop(f, None)

        return GameState(
            day=self.day,
            energy=self.energy,
            support=self.support,
            guilt=self.guilt,
            warmth=self.warmth,
            flags=new_flags,
        )

    def with_updates(self, **kwargs: int) -> GameState:
        day = self.day
        energy = self.energy
        support = self.support
        guilt = self.guilt
        warmth = self.warmth
        flags = dict(self.flags)

        for k, v in kwargs.items():
            if not isinstance(v, int):
                raise TypeError(f"State updates must be int: {k}={v!r}")

            if k == "day":
                day = v
            elif k == "energy":
                energy = v
            elif k == "support":
                support = v
            elif k == "guilt":
                guilt = v
            elif k == "warmth":
                warmth = v
            elif k == "flags":
                raise KeyError("Use with_flags() for flags updates.")
            else:
                raise KeyError(f"Unknown state field: {k}")

        return GameState(
            day=day,
            energy=energy,
            support=support,
            guilt=guilt,
            warmth=warmth,
            flags=flags,
        )
