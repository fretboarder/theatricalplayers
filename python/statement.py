from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import functools
from typing import Iterable, TypedDict


# Just to have a little type-safety
class Performance(TypedDict):
    playID: str
    audience: int

# Just to have a little type-safety
class Invoice(TypedDict):
    customer: str
    performances: list[Performance]

# Just to have a little type-safety
class Play(TypedDict):
    name: str
    type: str

AllPlays = dict[str, Play]


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

    @property
    def total(self):
        return sum(s.amount for s in self.statement_lines)


def format_as_dollars(cents: int) -> str:
    return f"${cents/100:0,.2f}"


def render_as_text(statement: Statement) -> str:
    result = f"Statement for {statement.customer}\n"
    for line in statement.statement_lines:
        result += f" {line.play_name}: {format_as_dollars(line.amount)} ({line.seats} seats)\n"
    result += f"Amount owed is {format_as_dollars(statement.total)}\n"
    result += f"You earned {statement.credits} credits\n"
    return result


def render_as_html(statement: Statement) -> str:
    result = f"<h1>Statement for {statement.customer}</h1>\n"
    result += "<table>\n"
    result += "<tr><th>play</th><th>seats</th><th>cost</th></tr>\n"
    for line in statement.statement_lines:
        result += f" <tr><td>{line.play_name}</td><td>{line.seats}</td>"
        result += f"<td>{format_as_dollars(statement.total)}</td></tr>\n"
    result += "</table>\n"
    result += f"<p>Amount owed is <em>{format_as_dollars(statement.total)}</em></p>\n"
    result += f"<p>You earned <em>{statement.credits}</em> credits</p>"
    return result


class BillingStrategy(ABC):
    def __init__(self, play: Play, perf: Performance):
        self._play = play
        self._perf = perf

    @property
    def name(self) -> str:
        return self._play["name"]

    @property
    def audience(self) -> int:
        return self._perf["audience"]

    def credits(self) -> int:
        return max(self.audience - 30, 0)

    def statement_line(self) -> StatementLine:
        return StatementLine(self.name, self.amount(), self.audience)

    @abstractmethod
    def amount(self) -> int:
        ...


class TragedyBilling(BillingStrategy):
    def amount(self) -> int:
        amount = 40000
        if self.audience > 30:
            amount += 1000 * (self.audience - 30)
        return amount


class ComedyBilling(BillingStrategy):
    def amount(self) -> int:
        amount = 30000 + 300 * self.audience
        if self.audience > 20:
            amount += 10000 + 500 * (self.audience - 20)
        return amount

    def credits(self) -> int:
        return super().credits() + self.audience // 5

# Add new BillingStrategies here

def billing_strategy(plays: AllPlays, perf: Performance) -> BillingStrategy:
    play_type = plays[perf["playID"]]["type"]
    match play_type:
        case "tragedy":
            return TragedyBilling(plays[perf["playID"]], perf)
        case "comedy":
            return ComedyBilling(plays[perf["playID"]], perf)
        # Insert new play_types here
        case _:
            raise ValueError(f"unknown type: {play_type}")


def calculate(invoice: Invoice, plays: AllPlays) -> Statement:
    lines, credits = functools.reduce(lambda total, strategy:
        (total[0] + [strategy.statement_line()], total[1] + strategy.credits()),
        (billing_strategy(plays, perf) for perf in invoice["performances"]),
        ([], 0)
    )
    return Statement(invoice["customer"], lines, credits)


def statement(invoice: Invoice, plays: AllPlays) -> str:
    return render_as_text(calculate(invoice, plays))


def html_statement(invoice: Invoice, plays: AllPlays) -> str:
    return render_as_html(calculate(invoice, plays))
