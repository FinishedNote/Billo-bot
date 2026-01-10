import discord
import stripe
from aiohttp import web
from discord.ext import commands
from discord import app_commands
from src.config import TOKEN, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from src.views import InvoiceView


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
stripe.api_key = STRIPE_SECRET_KEY
ROLE_PREMIUM_ID = 1459252826080542720
PORT_WEBHOOK = 4242

async def handle_stripe(request):
    payload = await request.read()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return web.Response(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        try:
            guild_id = int(session['metadata']['guild_id'])
            user_id = int(session['metadata']['discord_id'])
            
            guild = bot.get_guild(guild_id)
            if guild:
                member = guild.get_member(user_id)
                role = guild.get_role(ROLE_PREMIUM_ID)
                if member and role:
                    await member.add_roles(role)
                    print(f"💰 PREMIUM : Rôle donné à {member.name}")
                    try:
                        await member.send("Merci pour ton achat ! Tu es maintenant **Premium** 💎")
                    except:
                        pass
        except KeyError:
            print("⚠️ Paiement reçu mais pas de metadata Discord trouvée.")

    return web.Response(status=200)

async def start_stripe_server():
    """Lance le petit serveur web en arrière-plan"""
    app = web.Application()
    app.add_routes([web.post('/stripe_webhook', handle_stripe)])
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT_WEBHOOK)
    await site.start()
    print(f"🌍 Serveur Paiement écoute sur le port {PORT_WEBHOOK}")

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

@bot.tree.command(name="premium", description="Devenir membre Premium (5.99€)")
async def premium(interaction: discord.Interaction):

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'product_data': {'name': 'Grade Premium Discord'},
                'unit_amount': 599,
            },
            'quantity': 1,
        }],
        mode='payment',

        metadata={
            'discord_id': interaction.user.id,
            'guild_id': interaction.guild.id
        },
        success_url='https://google.com',
        cancel_url='https://google.com',
    )
    
    await interaction.response.send_message(
        f"💎 Clique ici pour activer ton Premium : {session.url}", 
        ephemeral=True
    )

if __name__ == "__main__":
    bot.run(TOKEN)