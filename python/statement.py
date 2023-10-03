from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import functools
from typing import Iterable, TypedDict


AllPlays = dict[str, dict[str, str]]

# Just to have a little type-safety
class Performance(TypedDict):
    playID: str
    audience: int


# Just to have a little type-safety
class Invoice(TypedDict):
    customer: str
    performances: list[Performance]


@dataclass(frozen=True)
class StatementLine:
    """Representing a single line on the invoice"""
    play_name: str
    amount: int
    seats: int


@dataclass(frozen=True)
class Statement:
    """Representing the final statement."""
    customer: str
    statement_lines: Iterable[StatementLine]
    credits: int


def render_as_text(statement: Statement) -> str:
    result = f"Statement for {statement.customer}\n"
    total = 0
    for line in statement.statement_lines:
        result += f" {line.play_name}: {format_as_dollars(line.amount)} ({line.seats} seats)\n"
        total += line.amount
    result += f"Amount owed is {format_as_dollars(total)}\n"
    result += f"You earned {statement.credits} credits\n"
    return result


class BillingStrategy(ABC):
    def __init__(self, name: str):
        self._name = name

    @property
    def play(self):
        return self._name

    @abstractmethod
    def amount(self, perf: Performance) -> int:
        ...

    @abstractmethod
    def credits(self, perf: Performance) -> int:
        ...


class TragedyBilling(BillingStrategy):
    def amount(self, perf: Performance) -> int:
        amount = 40000
        if perf["audience"] > 30:
            amount += 1000 * (perf["audience"] - 30)
        return amount

    def credits(self, perf: Performance):
        return max(perf["audience"] - 30, 0)


class ComedyBilling(BillingStrategy):
    def amount(self, perf: Performance) -> int:
        amount = 30000 + 300 * perf["audience"]
        if perf["audience"] > 20:
            amount += 10000 + 500 * (perf["audience"] - 20)
        return amount

    def credits(self, perf: Performance):
        return max(perf["audience"] - 30, 0) + perf["audience"] // 5


def format_as_dollars(cents: int) -> str:
    return f"${cents/100:0,.2f}"


def create_billing(plays: AllPlays, perf: Performance) -> BillingStrategy:
    play_type, play_name = plays[perf["playID"]]["type"], plays[perf["playID"]]["name"]
    match play_type:
        case "tragedy":
            return TragedyBilling(play_name)
        case "comedy":
            return ComedyBilling(play_name)
        case _:
            raise ValueError(f"unknown type: {play_type}")


def calculate(invoice: Invoice, plays: AllPlays) -> Statement:
    perfs = invoice["performances"]
    all_billings = [create_billing(plays, perf) for perf in perfs]
    return Statement(
        invoice["customer"],
        (
            StatementLine(billing.play, billing.amount(perf), perf["audience"])
            for billing, perf in zip(all_billings, perfs)
        ),
        sum(billing.credits(perf) for billing, perf in zip(all_billings, perfs))
    )


def statement(invoice: Invoice, plays: AllPlays) -> str:
    return render_as_text(calculate(invoice, plays))
