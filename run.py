import asyncio
from datetime import datetime, timedelta
from typing import Union
from dotenv import load_dotenv

import discord
import discord.ext
from discord import Interaction

load_dotenv()

from warcraftlogs.api import APIManager, get_id_from_url, Report, APIException
from warcraftlogs.constants import *


client = discord.Bot()
ap = APIManager()

async def get_recent_logs(ctx: discord.AutocompleteContext) -> list:
    return []


async def get_nickname(ctx, user_id) -> str:
    user = ctx.guild.get_member(user_id)
    if not user:
        user = await ctx.guild.fetch_member(user_id)
    return user.display_name if user else "UKJENT"


class ReportButton(discord.ui.Button["Report"]):
    def __init__(self, id: str, name: str):
        self.id = id
        super().__init__(style=discord.ButtonStyle.success, label=name)

    async def callback(self, interaction: Interaction):
        assert self.view is not None
        view: ReportsView = self.view
        view.stop()
        if view.message != None:
            await view.message.delete()
        if self.id in ap.reports:
            try:
                report = await ap.get_report(self.id)
            except APIException as e:
                print(e)
                await interaction.response.send_message(
                    "Fikk problem med å hente fra Warcraft Logs, prøv igjen senere.", ephemeral=True
                )
            else:
                e = await get_report_embed(report)
                v = ReportView(report)
                await interaction.response.send_message(embed=e, view=v)
        else:
            await interaction.response.send_message(f"Noe gikk galt, rapporten ble ikke hentet", ephemeral=True)


class ReportsView(discord.ui.View):
    async def build(self, reports: list):
        for i, l in enumerate(reports[:5]):
            b = ReportButton(l.id, f"{i+1}. {l.title}")
            b.row = i
            self.add_item(b)


class ReportView(discord.ui.View):
    def __init__(self, report: Report):
        b1 = discord.ui.Button(
            label="Sammendrag",
            url=f"https://vanilla.warcraftlogs.com/reports/{report.id}",
            style=discord.ButtonStyle.link
        )
        b2 = discord.ui.Button(
            label="Ranking",
            url=f"https://vanilla.warcraftlogs.com/reports/{report.id}#boss=-2&wipes=2&view=rankings",
            style=discord.ButtonStyle.link
        )
        super().__init__()
        self.add_item(b1)
        self.add_item(b2)


async def get_report_embed(report: Report) -> discord.Embed:
    def round_up(arg):
        if arg > round(arg):
            return round(arg) + 1
        else:
            return round(arg)
    # msg += "Karakterer: **"
    # msg += ", ".join([p.name for p in report.characters])
    # msg += "**"
    e = discord.Embed(
        title=report.title,
        description=":calendar: " + report.start_time.strftime("%d.%m.%Y"),
        color=0xb47aff
    )
    msg = f"Raid: **{report.raid}**\n" if len(report.raid) else ""
    msg += f"Tid brukt: **{report.duration_str}**\n"
    msg += f"Kills: **{len(report.fights)}**\n"
    if report.speed_rank > 0:
        msg += f"Deaths: **{report.deaths}**\n\n"
    else:
        msg += f"*Limited report, only kills*\n"
    if report.speed_rank > 0:
        msg += f"Speed %: **{report.speed_rank}**\n"
    if report.execution_rank > 0:
        msg += f"Execution %: **{report.execution_rank}**\n"

    e.add_field(name="Info", value=msg, inline=True)
    msg = ""
    for i in range(len(report.characters)):
    # for i in range(round_up(len(report.characters) / 5)):
        # for y in range(i * 5, i * 5 + 5):
        #     if y < len(report.characters):
        c = report.characters[i]
        msg += f"**{c.name}** ({c.player_class})\n"
    e.add_field(name="Karakterer", value=msg, inline=True)
    e.set_thumbnail(url="https://assets.rpglogs.com/img/warcraft/favicon.png")
    return e


@client.slash_command(name="log", description="Post nylig opplastet logg") #, guild_ids=SERVER_IDS)
async def post_log(ctx: discord.ApplicationContext, optional_url: discord.Option(str, required=False, description="URL for rapporten, la stå blank for å vise liste")):
    if optional_url != None:
        url = optional_url.lstrip().rstrip()
        log_id = get_id_from_url(url)
    else:
        log_id = None

    if log_id != None:
        try:
            report: Union[Report, None] = await ap.get_report(log_id)
            if report != None:
                e = await get_report_embed(report)
                v = ReportView(report)
                await ctx.send_response(embed=e, view=v)
            else:
                await ctx.respond("List list", ephemeral=True)
        except APIException as e:
            print(e)
            await ctx.send_response("Fikk en feil når jeg prøvde å hente rapport...", ephemeral=True)

    else:
        v = ReportsView()
        try:
            await ap.get_reports()
        except APIException as e:
            print(e)
            await ctx.send_response("Fikk en feil når jeg prøvde å hente rapporter...", ephemeral=True)
        except Exception as e:
            print(e)
            await ctx.send_response("Fikk udefinert feil når jeg prøvde hente den rapporten... Spør \"Hjelp\"", ephemeral=True)
        else:
            if len(ap.reports) > 0:
                await v.build([r for k, r in ap.reports.items()])
                e: discord.Embed = discord.Embed(
                    title="Velg en rapport",
                    description="Fem siste opplastede rapporter for guilden",
                    color=0x32a852
                )
                i = 1
                for _k, r in ap.reports.items():
                    msg = f"*{r.title}*\n"
                    msg += f"{r.raid}\n"
                    msg += "Startet: " + r.start_time.strftime("%d.%m, %H:%M")
                    e.add_field(name=f"**{i}**.", value=msg, inline=True)
                    i += 1
                await ctx.respond(view=v, ephemeral=True, embed=e)
            else:
                await ctx.respond("Fikk ikke hentet logger...", ephemeral=True)
#

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return


async def main():
    await ap.auth_user()


if __name__ == "__main__":
    asyncio.run(main())
    client.run(BOT_TOKEN)

