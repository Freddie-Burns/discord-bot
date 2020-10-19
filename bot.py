"""
Implement higher or lower bot more neatly as a class.
Update the environment variables on the host server to set the
DEATH_PROB, MAX_SLEEP, and TOKEN.
"""

import operator
import os
import random
import time

from discord.ext import commands
from dotenv import load_dotenv


load_dotenv(encoding='utf-8')
DEATH_PROB = float(os.getenv('DEATH_PROB'))
MAX_SLEEP = float(os.getenv('MAX_SLEEP'))
TOKEN = os.getenv('DISCORD_TOKEN')

BAD_EMOJIS = os.getenv('BAD_EMOJIS').split(',')
GOOD_EMOJIS = os.getenv('GOOD_EMOJIS').split(',')


def main():
    bot = HigherOrLowerBot()
    @bot.event
    async def on_ready(): print(f'{bot.user} has connected to Discord!')
    bot.run(TOKEN)


class BetEnum:
    lower = 0
    same = 1
    higher = 2


bet_strings = {
    BetEnum.lower: "Lower",
    BetEnum.same: "The same",
    BetEnum.higher: "Higher",
}


class HigherOrLowerBot(commands.Bot):
    """Roll the dice."""
    def __init__(self, *args, **kwargs):
        super().__init__(
            command_prefix='!',
            case_insensitive=True,
            description="Come play the galaxy's favourite game!",
            *args, **kwargs,
        )
        self.bet_operator = {
            BetEnum.lower: operator.lt,
            BetEnum.same: operator.eq,
            BetEnum.higher: operator.gt,
        }
        self.first_value = None
        self.second_value = None
        self.sides = None
        self.success = None
        self.bet_enum = None

        # Kwargs needed to create commands out of methods.
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

    async def first_roll(self, ctx, sides=6):
        self.first_value = random.randint(1, sides)
        self.sides = sides
        await ctx.send(self.first_value)

    async def higher(self, ctx):
        self.bet_enum = BetEnum.higher
        await self._second_roll(ctx)

    async def lower(self, ctx):
        self.bet_enum = BetEnum.lower
        await self._second_roll(ctx)

    async def same(self, ctx):
        self.bet_enum = BetEnum.same
        await self._second_roll(ctx)

    def _add_all_commands(self):
        """Create commands from methods, add them to internal list."""
        for meth, kwargs in self.command_kwargs.items():
            self.add_command(commands.command(**kwargs)(meth))

    def _bet_message(self):
        bet_str = bet_strings[self.bet_enum]
        if self.success is None:
            return f"self.success is None."
        elif self.success:
            emoji = random.choice(GOOD_EMOJIS)
            return f"{self.second_value} - {bet_str} was correct! {emoji}"
        else:
            emoji = random.choice(BAD_EMOJIS)
            return f"{self.second_value} - {bet_str} was wrong. {emoji}"

    def _reset_roll_params(self):
        self.first_value = None
        self.second_value = None
        self.sides = None
        self.success = None
        self.bet_enum = None

    async def _second_roll(self, ctx):
        """Based on params of first roll & the bet made."""
        if self.first_value is None:
            message = "Roll before betting."

        elif did_i_die():
            message = "You died..."

        else:
            # Choose rand int with same range as first roll.
            self.second_value = random.randint(1, self.sides)
            await ctx.send("rolling...")

            # Uses bet_enum value to choose operation from dict.
            math_op = self.bet_operator[self.bet_enum]
            self.success = math_op(self.second_value, self.first_value)
            message = self._bet_message()

            # Wait random time and log to the console.
            sleep_time = random.randint(0, MAX_SLEEP)
            print(f"sleep {sleep_time}s")
            time.sleep(sleep_time)

        # Send msg and reset roll params.
        await ctx.send(message)
        self._reset_roll_params()


def did_i_die():
    """DEATH_PROB chance of returning True."""
    return random.random() < DEATH_PROB


if __name__ == '__main__':
    main()
