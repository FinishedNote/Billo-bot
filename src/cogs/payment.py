import discord
import stripe
from aiohttp import web
from discord.ext import commands
from src.config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

stripe.api_key = STRIPE_SECRET_KEY
ROLE_PREMIUM_ID = 1459252826080542720

class BotClient(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):

        self.web_app = web.Application()
        self.web_app.add_routes([web.post('/stripe_webhook', self.handle_stripe)])
        
        runner = web.AppRunner(self.web_app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 4242)
        await site.start()
        print("🌍 Serveur Webhook Stripe écoute sur le port 4242")

    async def handle_stripe(self, request):
        payload = await request.read()
        sig_header = request.headers.get('Stripe-Signature')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return web.Response(status=400)
        except stripe.error.SignatureVerificationError:
            return web.Response(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']

            user_id = int(session['metadata']['discord_id'])
            guild_id = int(session['metadata']['guild_id'])
            
            await self.donner_le_role(guild_id, user_id)

        return web.Response(status=200)

    async def donner_le_role(self, guild_id, user_id):
        guild = self.get_guild(guild_id)
        if guild:
            member = guild.get_member(user_id)
            role = guild.get_role(ROLE_PREMIUM_ID)
            if member and role:
                await member.add_roles(role)

                try:
                    await member.send("✅ Merci ! Tu es maintenant **Premium**.")
                except:
                    pass
                print(f"💰 Rôle donné à {member.name}")

bot = BotClient()


@bot.tree.command(name="premium", description="Devenir membre Premium (5.99€)")
async def premium(interaction: discord.Interaction):

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'product_data': {'name': 'Rôle Premium Discord'},
                'unit_amount': 599,
            },
            'quantity': 1,
        }],
        mode='payment',

        metadata={
            'discord_id': interaction.user.id,
            'guild_id': interaction.guild.id
        },
    )

    await interaction.response.send_message(f"Clique ici pour passer Premium : {session.url}", ephemeral=True)