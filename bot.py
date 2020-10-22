"""
Implement higher or lower bot more neatly as a class.
Update the environment variables on the host server to set the
DEATH_PROB, MAX_SLEEP, TOKEN, and EMOJIS.
"""

import operator
import os
import pickle
import random
import time
from enum import Enum

from discord.ext import commands
from discord.ext.commands.context import Context
from discord.guild import Guild
from dotenv import load_dotenv


load_dotenv(encoding='utf-8')
DEATH_PROB = float(os.getenv('DEATH_PROB'))
FACT_PROB = float(os.getenv('FACT_PROB'))
MIN_SLEEP = float(os.getenv('MIN_SLEEP'))
MAX_SLEEP = float(os.getenv('MAX_SLEEP'))
SLEEP_STEP = float(os.getenv('SLEEP_STEP'))
TOKEN = os.getenv('TEST_TOKEN')

GOOD_EMOJIS = "🤩🥳😘🤗😲👽😼🎉🎀🎊"
BAD_EMOJIS = "🙃🤬😭😤🥺😖😒🤯🥵🥶😱😳👹⛈💔❌⛔🔕"


class BetEnum(Enum):
    lower = 0
    same = 1
    higher = 2


BET_STRINGS = {
    BetEnum.lower: "Lower",
    BetEnum.same: "The same",
    BetEnum.higher: "Higher",
}
BET_OPS = {
    BetEnum.lower: operator.lt,
    BetEnum.same: operator.eq,
    BetEnum.higher: operator.gt,
}
GUILDS = {}


def main():
    bot = HigherOrLowerBot()
    @bot.event
    async def on_ready(): print(f'{bot.user} has connected to Discord!')
    bot.run(TOKEN)


class HorlGuild:
    def __init__(self, guild: Guild):
        self.guild = guild
        self.first_value = None
        self.second_value = None
        self.sides = None
        self.success = None
        self.bet_enum = None
        self.is_rx_on = True


class CheckRxChannel:
    """
    Context manager to block commands when bot is busy.
    Returns bool of rx channel is open. If false do not run
    another command.
    """
    def __init__(self, ctx: Context):
        if ctx.guild.id not in GUILDS.keys():
            GUILDS[ctx.guild.id] = HorlGuild(ctx.guild)
        self.guild: HorlGuild = GUILDS[ctx.guild.id]
        self.keep_closed = False

    def __enter__(self):
        # If rx not on, don't execute command.
        exec_cmd = self.guild.is_rx_on
        # If rx is open, close it to lock out other cmds.
        # If rx is closed, keep it closed when exiting.
        if self.guild.is_rx_on: self.guild.is_rx_on = False
        else: self.keep_closed = True
        return exec_cmd

    def __exit__(self, e, v, t):
        if self.keep_closed: self.guild.is_rx_on = False
        else: self.guild.is_rx_on = True


class HigherOrLowerBot(commands.Bot):
    """Roll the dice."""
    def __init__(self, *args, **kwargs):
        super().__init__(
            command_prefix='!',
            case_insensitive=True,
            description="Come play the galaxy's favourite game!",
            *args, **kwargs,
        )
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

    async def higher(self, ctx):
        with CheckRxChannel(ctx) as is_open:
            if is_open:
                guild = GUILDS[ctx.guild.id]
                guild.bet_enum = BetEnum.higher
                await self._second_roll(ctx)

    async def lower(self, ctx):
        with CheckRxChannel(ctx) as is_open:
            if is_open:
                guild = GUILDS[ctx.guild.id]
                guild.bet_enum = BetEnum.lower
                await self._second_roll(ctx)

    async def random(self, ctx):
        with CheckRxChannel(ctx) as is_open:
            if is_open:
                guild = GUILDS[ctx.guild.id]
                guild.bet_enum = random.choice(list(BetEnum))
                await self._second_roll(ctx)

    async def same(self, ctx):
        with CheckRxChannel(ctx) as is_open:
            if is_open:
                guild = GUILDS[ctx.guild.id]
                guild.bet_enum = BetEnum.same
                await self._second_roll(ctx)

    def _add_all_commands(self):
        """Create commands from methods, add them to internal list."""
        for meth, kwargs in self.command_kwargs.items():
            self.add_command(commands.command(**kwargs)(meth))

    async def _second_roll(self, ctx):
        """Based on params of first roll & the bet made."""
        guild = GUILDS[ctx.guild.id]
        if guild.first_value is None:
            message = "Roll before betting."
        elif did_i_die():
            message = "You died... 🙃"
        else:
            # Choose rand int with same range as first roll.
            guild.second_value = random.randint(1, guild.sides)
            # Uses bet_enum value to choose operation from dict.
            math_op = BET_OPS[guild.bet_enum]
            guild.success = math_op(guild.second_value, guild.first_value)
            message = self._bet_message(ctx)
            # Build tension.
            await self._suspense_messages(ctx)

        # Send msg and reset roll params.
        await ctx.send(message)
        self._reset_roll_params(guild)

    @staticmethod
    async def first_roll(ctx, sides=6):
        with CheckRxChannel(ctx) as is_open:
            if is_open:
                guild = GUILDS[ctx.guild.id]
                guild.first_value = random.randint(1, sides)
                guild.sides = sides
                await ctx.send(guild.first_value)
                if random.random() < FACT_PROB:
                    with open("facts.pkl", "rb") as file:
                        fact = random.choice(pickle.load(file))
                        await ctx.send(fact)

    @staticmethod
    async def infected(ctx, prob):
        with CheckRxChannel(ctx) as is_open:
            if is_open:
                infected = random.random() < float(prob)
                if infected:
                    msg = "You are infected!"
                else:
                    msg = "Not infected."
                await ctx.send(msg)

    @staticmethod
    async def particle_model(ctx):
        with CheckRxChannel(ctx) as is_open:
            if is_open:
                await ctx.send("Particles depricated, I hated it.")

    @staticmethod
    def _bet_message(ctx):
        guild = GUILDS[ctx.guild.id]
        bet_str = BET_STRINGS[guild.bet_enum]
        if guild.success is None:
            return f"self.success is None."
        elif guild.success:
            emoji = random.choice(GOOD_EMOJIS)
            return f"{guild.second_value} - {bet_str} was correct! {emoji}"
        else:
            emoji = random.choice(BAD_EMOJIS)
            message = f"{guild.second_value} - {bet_str} was wrong, "\
                      f"you lose. {emoji}"
            return message

    @staticmethod
    def _reset_roll_params(guild):
        guild.first_value = None
        guild.second_value = None
        guild.sides = None
        guild.success = None
        guild.bet_enum = None

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


def did_i_die():
    """DEATH_PROB chance of returning True."""
    return random.random() < DEATH_PROB


if __name__ == '__main__':
    main()
