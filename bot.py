"""
Implement higher or lower bot more neatly as a class.
Update the environment variables on the host server to set the
DEATH_PROB, MAX_SLEEP, TOKEN, and EMOJIS.
"""

import operator
import os
import random
import time
from abc import ABC
from enum import Enum

from discord.ext import commands
from dotenv import load_dotenv


load_dotenv(encoding='utf-8')
DEATH_PROB = float(os.getenv('DEATH_PROB'))
MIN_SLEEP = float(os.getenv('MIN_SLEEP'))
MAX_SLEEP = float(os.getenv('MAX_SLEEP'))
SLEEP_STEP = float(os.getenv('SLEEP_STEP'))
TOKEN = os.getenv('DISCORD_TOKEN')

GOOD_EMOJIS = "🤩🥳😘🤗😲👽😼🎉🎀🎊"
BAD_EMOJIS = "🙃🤬😭😤🥺😖😒🤯🥵🥶😱😳👹⛈💔❌⛔🔕"


def main():
    bot = HigherOrLowerBot()
    @bot.event
    async def on_ready(): print(f'{bot.user} has connected to Discord!')
    bot.run(TOKEN)


class BetEnum(Enum):
    lower = 0
    same = 1
    higher = 2


bet_strings = {
    BetEnum.lower: "Lower",
    BetEnum.same: "The same",
    BetEnum.higher: "Higher",
}


class IHigherOrLowerBot(ABC):
    """Bot interface for type hinting context manager."""
    is_rx_on = True


class CheckRxChannel:
    """
    Context manager to block commands when bot is busy.
    Returns bool of rx channel is open. If false do not run
    another command.
    """
    def __init__(self, bot: IHigherOrLowerBot):
        self.bot = bot
        self.keep_closed = False

    def __enter__(self):
        # If rx not on, don't execute command.
        exec_cmd = self.bot.is_rx_on
        # If rx is open, close it to lock out other cmds.
        # If rx is closed, keep it closed when exiting.
        if self.bot.is_rx_on:
            self.bot.is_rx_on = False
        else:
            self.keep_closed = True
        return exec_cmd

    def __exit__(self, e, v, t):
        if self.keep_closed:
            self.bot.is_rx_on = False
        else:
            self.bot.is_rx_on = True


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
        self.is_rx_on = True

        # Kwargs needed to create commands out of methods.
        self.command_kwargs = {
            self.first_roll: {
                'parent': self,
                'name': 'horl',
                'aliases': ['higherorlower',]
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
            self.random: {
                'parent': self,
                'name': 'rand',
                'aliases': [],
            },
            self.infected: {
                'parent': self,
                'name': 'infected',
                'aliases': [],
            },
            self.particle_model: {
                'parent': self,
                'name': 'particles',
                'aliases': [],
            },
        }
        self._add_all_commands()

    async def infected(self, ctx, prob):
        with CheckRxChannel(self) as is_open:
            if is_open:
                infected = random.random() < float(prob)
                if infected:
                    msg = "You are infected!"
                else:
                    msg = "Not infected."
                await ctx.send(msg)

    async def first_roll(self, ctx, sides=6):
        bid_message = "Did you know? Bid Deals is Gungan for \"The floppy eared one\" a great honour among Gungans."
        with CheckRxChannel(self) as is_open:
            if is_open:
                self.first_value = random.randint(1, sides)
                self.sides = sides
                await ctx.send(self.first_value)
                if random.random() < 0.1:
                    await ctx.send(bid_message)

    async def higher(self, ctx):
        with CheckRxChannel(self) as is_open:
            if is_open:
                self.bet_enum = BetEnum.higher
                await self._second_roll(ctx)

    async def lower(self, ctx):
        with CheckRxChannel(self) as is_open:
            if is_open:
                self.bet_enum = BetEnum.lower
                await self._second_roll(ctx)

    async def random(self, ctx):
        with CheckRxChannel(self) as is_open:
            if is_open:
                self.bet_enum = random.choice(list(BetEnum))
                await self._second_roll(ctx)

    async def same(self, ctx):
        with CheckRxChannel(self) as is_open:
            if is_open:
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
            message = f"{self.second_value} - {bet_str} was wrong, "\
                      f"you lose. {emoji}"
            return message

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
            message = "You died... 🙃"
        else:
            # Choose rand int with same range as first roll.
            self.second_value = random.randint(1, self.sides)
            # Uses bet_enum value to choose operation from dict.
            math_op = self.bet_operator[self.bet_enum]
            self.success = math_op(self.second_value, self.first_value)
            message = self._bet_message()
            # Build tension.
            await self._suspense_messages(ctx)

        # Send msg and reset roll params.
        await ctx.send(message)
        self._reset_roll_params()

    @staticmethod
    async def _suspense_messages(ctx):
        # Wait random time and log to the console.
        msg_num = random.randint(MIN_SLEEP, MAX_SLEEP)
        # Log sleep time.
        print(f"sleep {msg_num}")

        # Build tension by sending "rolling" messages.
        for i in range(msg_num):
            dots = '.' * i
            await ctx.send(f"rolling {dots}")
            time.sleep((i+1) * SLEEP_STEP)

    @staticmethod
    async def particle_model(ctx):
        # Particles come apart.
        for i in range(5):
            dots = ('' + ' ' * i).join(['.'] * 5)
            await ctx.send(dots)
            time.sleep((i+1) * SLEEP_STEP / 5)
        for i in range(5, 0):
            dots = ('' + ' ' * i).join(['.'] * 5)
            await ctx.send(dots)
            time.sleep((i+1) * SLEEP_STEP / 5)


IHigherOrLowerBot.register(HigherOrLowerBot)


def did_i_die():
    """DEATH_PROB chance of returning True."""
    return random.random() < DEATH_PROB


if __name__ == '__main__':
    main()
