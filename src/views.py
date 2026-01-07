import discord
from discord import ui
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from src.email_utils import send_invoice_email


class FactureModal1(ui.Modal, title="Détails Client"):
    client_name = ui.TextInput(label="Nom complet", placeholder="Ex: John Doe")
    email = ui.TextInput(label="Email", placeholder="john.doe@exemple.com")
    product = ui.TextInput(label="Article", placeholder="Ex: Moncler Maya Jacket")
    size = ui.TextInput(label="Taille", placeholder="Ex: L")
    colour = ui.TextInput(label="Couleur", placeholder="Ex: noir")

    def __init__(self, template_name):
        super().__init__()
        self.template_name = template_name

    async def on_submit(self, interaction: discord.Interaction):
        view = ContinueView(
            self.template_name,
            self.client_name.value,
            self.email.value,
            self.product.value,
            self.size.value,
            self.colour.value
        )
        await interaction.response.send_message(
            "Clique sur le bouton pour continuer :",
            view=view,
            ephemeral=True
        )


class ContinueView(ui.View):
    def __init__(self, template_name, client_name, email, product, size, colour):
        super().__init__(timeout=300)
        self.template_name = template_name
        self.client_name = client_name
        self.email = email
        self.product = product
        self.size = size
        self.colour = colour

    @ui.button(label="Continuer", style=discord.ButtonStyle.primary)
    async def continue_button(self, interaction: discord.Interaction, button: ui.Button):
        modal2 = FactureModal2(
            self.template_name,
            self.client_name,
            self.email,
            self.product,
            self.size,
            self.colour
        )
        await interaction.response.send_modal(modal2)


class FactureModal2(ui.Modal, title="Détails Commande"):
    order_date = ui.TextInput(label="Date de la commande", placeholder="Ex: 20/05/18")
    estimated_delivery = ui.TextInput(label="Livraison estimée", placeholder="Ex: 27/05/18")
    order_number = ui.TextInput(label="Numéro de commande", placeholder="Ex: 3070080226406")
    price = ui.TextInput(label="Prix (€)", placeholder="1380")
    image_url = ui.TextInput(
        label="URL de l'image", 
        placeholder="https://exemple.com/image.jpg"
    )

    def __init__(self, template_name, client_name, email, product, size, colour):
        super().__init__()
        self.template_name = template_name
        self.client_name = client_name
        self.email = email
        self.product = product
        self.size = size
        self.colour = colour

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        try:
            data = {
                "client_name": self.client_name,
                "email": self.email,
                "product": self.product,
                "size": self.size,
                "colour": self.colour,
                "order_date": self.order_date.value,
                "estimated_delivery": self.estimated_delivery.value,
                "order_number": self.order_number.value,
                "price": self.price.value,
                "image_url": self.image_url.value,
                "order_total": str(int(self.price.value) + 15),
            }

            env = Environment(loader=FileSystemLoader('src/templates'))
            template = env.get_template(self.template_name)
            html_out = template.render(**data)

            sujet = f"Facture : {self.product}"
            email_envoye = send_invoice_email(self.email, sujet, html_out)

            status_msg = "**Facture envoyée par mail !**" if email_envoye else "⚠️ **Echec de l'envoi par mail.**"
            
            file_buffer = BytesIO(html_out.encode('utf-8'))
            file_buffer.seek(0)
            discord_file = discord.File(file_buffer, filename=f"Facture_{self.product}.html")

            await interaction.followup.send(
                content=f"{status_msg}\nClient: {self.client_name} | {self.price.value}€",
                file=discord_file
            )

        except Exception as e:
            await interaction.followup.send(f"Erreur : {e}")


class TemplateSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Moncler", value="moncler.html", description="Facture Moncler", emoji="✨"),
            discord.SelectOption(label="Stone Island", value="modern.html", description="Facture Stone Island", emoji="✨"),
            discord.SelectOption(label="Gérard Darel", value="black.html", description="Facture Gérard Darel", emoji="✨"),
        ]
        super().__init__(placeholder="Choisis le template de facture...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        chosen_template = self.values[0]
        await interaction.response.send_modal(FactureModal1(chosen_template))


class InvoiceView(ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(TemplateSelect())