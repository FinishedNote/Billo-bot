import discord
from discord import app_commands
from discord.ext import commands
from src.config import TOKEN
from src.views import InvoiceView


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Connecté en tant que {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Commandes synchronisées.")
    except Exception as e:
        print(e)


@bot.tree.command(name="receipt", description="Générer une nouvelle facture")
async def receipt(interaction: discord.Interaction):
    await interaction.response.send_message("Quel template veux-tu utiliser ?", view=InvoiceView(), ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)