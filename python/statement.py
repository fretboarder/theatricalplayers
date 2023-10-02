from dataclasses import dataclass
from typing import NewType

PlayID = NewType("PlayID", str)
PlayType = NewType("PlayType", str)

@dataclass(frozen=True)
class Play:
    name: str
    type: PlayType


@dataclass(frozen=True)
class Performance:
    playID: PlayID
    audience: int


@dataclass
class Invoice:
    customer: str
    performances: list[Performance]

    def __post_init__(self):
        self.performances = [Performance(**p) for p in self.performances]


Plays = dict[PlayID, Play]


def map_invoice(invoice: dict) -> Invoice:
    return Invoice(**invoice)


def map_plays(plays: dict) -> Plays:
    return {play_id: Play(**attr) for play_id, attr in plays.items()}


def performance_amount(perf: Performance, play: Play):
    if play.type == "tragedy":
        amount = 40000
        if perf.audience > 30:
            amount += 1000 * (perf.audience - 30)
    elif play.type == "comedy":
        amount = 30000
        if perf.audience > 20:
            amount += 10000 + 500 * (perf.audience - 20)
        amount += 300 * perf.audience
    else:
        raise ValueError(f'unknown type: {play.type}')

    return amount


@dataclass(frozen=True)
class StatementLine:
    play_name: str
    amount: int
    seats: int


@dataclass
class Statement:
    customer: str
    statement_lines: list[StatementLine]
    credits: int


@dataclass
class TextStatement(Statement):
    def render(self) -> str:
        result = f"Statement for {self.customer}\n"
        total = 0
        for line in self.statement_lines:
            result += f" {line.play_name}: {format_as_dollars(line.amount/100)} ({line.seats} seats)\n"
            total += line.amount
        result += f'Amount owed is {format_as_dollars(total/100)}\n'
        result += f'You earned {self.credits} credits\n'
        return result


def format_as_dollars(amount):
    return f"${amount:0,.2f}"


def calculate_credits(perf: Performance, play: Play):
    credits = max(perf.audience - 30, 0)
    # add extra credit for every ten comedy attendees
    if "comedy" == play.type:
        credits += perf.audience // 5
    return credits


def statement(_invoice: dict, _plays: dict, cls = TextStatement):
    # Map everything to real types to better support type checking
    invoice, plays = map_invoice(_invoice), map_plays(_plays)

    volume_credits = 0
    lines = []

    for perf in invoice.performances:
        # add volume credits
        volume_credits += calculate_credits(perf, plays[perf.playID])
        # generate a statement line
        lines.append(
            StatementLine(plays[perf.playID].name, performance_amount(perf, plays[perf.playID]), perf.audience)
        )

    return cls(invoice.customer, lines, volume_credits).render()
