from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, TypedDict


PlayID = str
PlayType = str
AllPlays = dict[PlayID, dict]


class Performance(TypedDict):
    playID: PlayID
    audience: int


class Invoice(TypedDict):
    customer: str
    performances: list[Performance]


@dataclass(frozen=True)
class StatementLine:
    play_name: str
    amount: int
    seats: int


@dataclass(frozen=True)
class Statement:
    customer: str
    statement_lines: Iterable[StatementLine]
    credits: int


@dataclass(frozen=True)
class TextStatement(Statement):
    def render(self) -> str:
        result = f"Statement for {self.customer}\n"
        total = 0
        for line in self.statement_lines:
            result += f" {line.play_name}: {format_as_dollars(line.amount)} ({line.seats} seats)\n"
            total += line.amount
        result += f"Amount owed is {format_as_dollars(total)}\n"
        result += f"You earned {self.credits} credits\n"
        return result


class Play(ABC):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    @abstractmethod
    def amount(self, perf: Performance) -> int:
        ...

    @abstractmethod
    def credits(self, perf: Performance) -> int:
        ...


class Tragedy(Play):
    def amount(self, perf: Performance) -> int:
        amount = 40000
        if perf["audience"] > 30:
            amount += 1000 * (perf["audience"] - 30)
        return amount

    def credits(self, perf: Performance):
        return max(perf["audience"] - 30, 0)


class Comedy(Play):
    def amount(self, perf: Performance) -> int:
        amount = 30000 + 300 * perf["audience"]
        if perf["audience"] > 20:
            amount += 10000 + 500 * (perf["audience"] - 20)
        return amount

    def credits(self, perf: Performance):
        return max(perf["audience"] - 30, 0) + perf["audience"] // 5


def format_as_dollars(cents: int) -> str:
    return f"${cents/100:0,.2f}"


def create_play(play_type: PlayType, name: str) -> Play:
    match play_type:
        case "tragedy":
            return Tragedy(name)
        case "comedy":
            return Comedy(name)
        case _:
            raise ValueError(f"unknown type: {play_type}")


def statement(invoice: Invoice, plays: AllPlays, cls=TextStatement) -> str:
    def get_type(perf: Performance):
        return plays[perf["playID"]]["type"]

    def get_name(perf: Performance):
        return plays[perf["playID"]]["name"]

    perfs = invoice["performances"]

    all_plays = [create_play(get_type(perf), get_name(perf)) for perf in perfs]
    statement_lines = (
        StatementLine(play.name, play.amount(perf), perf["audience"])
        for play, perf in zip(all_plays, perfs)
    )
    volume_credits = sum(play.credits(perf) for play, perf in zip(all_plays, perfs))
    return cls(invoice["customer"], statement_lines, volume_credits).render()
