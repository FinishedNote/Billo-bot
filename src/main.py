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
    """Reçoit le signal de Stripe quand quelqu'un paie"""
    payload = await request.read()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        print(f"❌ Erreur Signature Stripe : {e}") # DEBUG
        return web.Response(status=400)

    # --- DEBUG : ON AFFICHE L'EVENT REÇU ---
    print(f"📩 Événement Stripe reçu : {event['type']}") 

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # --- DEBUG : ON AFFICHE LES METADATA ---
        print(f"🔍 Contenu Session : Metadata={session.get('metadata')}")

        try:
            guild_id = int(session['metadata']['guild_id'])
            user_id = int(session['metadata']['discord_id'])
            
            guild = bot.get_guild(guild_id)
            if guild:
                try:
                    member = await guild.fetch_member(user_id)
                except discord.NotFound:
                    print(f"❌ Erreur : L'utilisateur {user_id} n'est plus sur le serveur.")
                    return web.Response(status=200)

                role = guild.get_role(ROLE_PREMIUM_ID)
                
                if member and role:
                    await member.add_roles(role)
                    print(f"💰 SUCCÈS : Rôle donné à {member.name}")
                    try:
                        await member.send("Merci pour ton achat ! Tu es maintenant **Premium** 💎")
                    except:
                        pass
                else:
                    print(f"⚠️ Problème : Rôle ({ROLE_PREMIUM_ID}) introuvable sur le serveur.")
            else:
                print(f"⚠️ Serveur Discord {guild_id} introuvable (Bot exclu ?)")
                
        except KeyError:
            print("❌ ERREUR : Pas de metadata 'discord_id' ou 'guild_id' dans le paiement !")
            
    else:
        print(f"ℹ️ Événement ignoré (On attendait 'checkout.session.completed', on a reçu '{event['type']}')")

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
    
    bot.loop.create_task(start_stripe_server())

    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes synchronisées.")
    except Exception as e:
        print(e)


@bot.tree.command(name="receipt", description="Générer une nouvelle facture (Réservé Premium)")
async def receipt(interaction: discord.Interaction):
    role_premium = interaction.guild.get_role(ROLE_PREMIUM_ID)

    if role_premium not in interaction.user.roles:
        await interaction.response.send_message(
            "⛔ **Cette commande est réservée aux membres Premium.**\n"
            "Fais la commande `/premium` pour débloquer l'accès !", 
            ephemeral=True
        )
        return

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