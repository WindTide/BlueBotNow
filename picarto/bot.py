from utils.tools import read_env
from utils.logging import Logger

from discord.ext import commands
from requests.models import Response

from .channel_embed import get_big_embed, get_minimal_embed

import os
import requests

from .models.channelDetails import ChannelDetails


class CallerError(RuntimeError):
    def __init__(self, response: Response, *args: object) -> None:
        super().__init__(str(response))
        self._response = response

    @property
    def status_code(self) -> int:
        return self._response.status_code

    @property
    def text(self) -> str:
        return self._response.text

    @property
    def ux_message(self) -> str:
        return f"Failed call: {self.status_code}"

    @property
    def full_message(self) -> str:
        text = 'Requires capta' if 'meta name="captcha-bypass"' in self.text else self.text

        return f"Failed call with code: {self.status_code}.\n" + text


def get_channel_data(channel_name: str) -> ChannelDetails:
    host = read_env('PICARTO_HOST', 'https://api.picarto.tv/api/v1')

    uri = f"{host}/channel/name/{channel_name}"
    headers = {
        "User-Agent": "curl/7.68.0"
    }

    response = requests.get(uri, headers=headers)

    if response.status_code != 200:
        raise CallerError(response)

    data = response.json()
    details = ChannelDetails.parse_obj(data)

    return details


class Picarto(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self._bot = bot

    @commands.group()
    async def picarto(self, ctx: commands.Context):
        Logger("picarto").info(ctx.author.name, "invoked a picarto command")

    @picarto.command()
    async def check(self, ctx: commands.Context, name: str = 'BGNlive'):
        # Check if channel is live, with minimal extra info

        Logger("picarto").debug(f"enter check({name})")

        try:
            details = get_channel_data(name)
            embed = get_minimal_embed(details)

            await ctx.send(embed=embed)

        except CallerError as err:
            print(err.full_message)
            await ctx.send(err.ux_message)

        finally:
            Logger("picarto").debug(f"exit check({name})")

    @picarto.command()
    async def info(self, ctx: commands.Context, name: str = 'BGNlive'):
        # Get all information about a channel

        Logger("picarto").debug(f"enter info({name})")

        try:
            details = get_channel_data(name)
            embed = get_big_embed(details)

            await ctx.send(embed=embed)

        except CallerError as err:
            print(err.full_message)
            await ctx.send(err.ux_message)

        finally:
            Logger("picarto").debug(f"exit info({name})")


def setup(bot):
    bot.add_cog(Picarto(bot))
