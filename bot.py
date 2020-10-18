"""
Implement higher or lower bot more neatly as a class.
Update the environment variables on the host server to set the
DEATH_PROB, MAX_SLEEP, and TOKEN.
"""

import os
import random
import time

from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()
DEATH_PROB = float(os.getenv('DEATH_PROB'))
MAX_SLEEP = float(os.getenv('MAX_SLEEP'))
TOKEN = os.getenv('DISCORD_TOKEN')


class BetEnum:
    low = 0
    same = 1
    high = 2


class HigherOrLowerBot(commands.Bot):
    """Roll the dice."""
    def __init__(self, *args, **kwargs):
        super().__init__(
            command_prefix='!',
            case_insensitive=True,
            description="Come play the galaxy's favourite game!",
            *args, **kwargs,
        )
        self.bet_outcomes = {
            BetEnum.low: self._bet_low,
            BetEnum.same: self._bet_same,
            BetEnum.high: self._bet_high,
        }
        self.first_value = None
        self.sides = None
        self.command_kwargs = {
            self.first_roll: {
                'parent': self,
                'name': 'horl',
            },
            self.lower: {
                'parent': self,
                'name': 'lower',
                'aliases': ['l', 'lo'],
            },
            self.same: {
                'parent': self,
                'name': 'same',
                'aliases': ['s', 'thesame'],
            },
            self.higher: {
                'parent': self,
                'name': 'higher',
                'aliases': ['h', 'hi'],
            },
        }
        self._add_all_commands()

    def _add_all_commands(self):
        for func, kwargs in self.command_kwargs.items():
            self.add_command(commands.command(**kwargs)(func))

    async def first_roll(self, ctx, sides=6):
        self.first_value = random.randint(1, sides)
        self.sides = sides
        await ctx.send(self.first_value)

    async def lower(self, ctx):
        await self._second_roll(ctx, BetEnum.low)

    async def same(self, ctx):
        await self._second_roll(ctx, BetEnum.same)

    async def higher(self, ctx):
        await self._second_roll(ctx, BetEnum.high)

    async def _second_roll(self, ctx, bet_enum):
        if did_i_die():
            await ctx.send("You died...")
            return
        await ctx.send("rolling...")
        second_value = random.randint(1, self.sides)
        outcome = self.bet_outcomes[bet_enum](second_value)
        sleep_time = random.randint(0, MAX_SLEEP)
        print(f"sleep {sleep_time}s")
        time.sleep(sleep_time)
        await ctx.send(outcome)

    def _bet_low(self, second_roll):
        if self.first_value is None:
            return "Roll before betting."
        elif second_roll < self.first_value:
            return f"{second_roll} - Lower was correct! 🎉"
        elif second_roll >= self.first_value:
            return f"{second_roll} - Lower was wrong."
        else:
            return "Something went wrong!"

    def _bet_same(self, second_roll):
        if self.first_value is None:
            return "Roll before betting."
        elif second_roll == self.first_value:
            return f"{second_roll} - The same was correct! 🎉"
        elif second_roll < self.first_value or second_roll > self.first_value:
            return f"{second_roll} - The same was wrong."
        else:
            return "Something went wrong!"

    def _bet_high(self, second_roll):
        if self.first_value is None:
            return "Roll before betting."
        elif second_roll > self.first_value:
            return f"{second_roll} - Higher was correct! 🎉"
        elif second_roll <= self.first_value:
            return f"{second_roll} - Higher was wrong."
        else:
            return "Something went wrong!"


def did_i_die():
    return random.random() < DEATH_PROB


bot = HigherOrLowerBot()


@bot.event
async def on_ready():
    print(f'{bot.user} tester has connected to Discord!')


@bot.command(name='cancel', aliases=['c', 'e', 'q', 'exit', 'quit'])
async def cancel(ctx):
    await ctx.send("cancel")


bot.run(TOKEN)
