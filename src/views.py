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
    price = ui.TextInput(label="Prix (sans symbole)", placeholder="1380")
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

            status_msg = "vient juste de générer une facture" if email_envoye else "⚠️ **Echec de l'envoi par mail.**"
            
            file_buffer = BytesIO(html_out.encode('utf-8'))
            file_buffer.seek(0)

            await interaction.followup.send(
                content=f"{interaction.user.mention} {status_msg}\n **Regarde tes mails.**",
            )

        except Exception as e:
            await interaction.followup.send(f"Erreur : {e}")

class FactureModalDior(ui.Modal, title="Détails Client"):
    client_name = ui.TextInput(label="Nom complet", placeholder="Ex: John Doe")
    email = ui.TextInput(label="Email", placeholder="john.doe@exemple.com")
    product = ui.TextInput(label="Article", placeholder="Ex: Sneaker B30 Countdown")
    size = ui.TextInput(label="Taille", placeholder="Ex: 43")
    price = ui.TextInput(label="Prix (sans symbole)", placeholder="Ex: 800")

    def __init__(self, template_name):
        super().__init__()
        self.template_name = template_name

    async def on_submit(self, interaction: discord.Interaction):
        view = ContinueView2(
            self.template_name,
            self.client_name.value,
            self.email.value,
            self.product.value,
            self.size.value,
            self.price.value
        )
        await interaction.response.send_message(
            "Clique sur le bouton pour continuer :",
            view=view,
            ephemeral=True
        )

class ContinueView2(ui.View):
    def __init__(self, template_name, client_name, email, product, size, price):
        super().__init__(timeout=300)
        self.template_name = template_name
        self.client_name = client_name
        self.email = email
        self.product = product
        self.size = size
        self.price = price

    @ui.button(label="Continuer", style=discord.ButtonStyle.primary)
    async def continue_button(self, interaction: discord.Interaction, button: ui.Button):
        modal2 = FactureModalDior2(
            self.template_name,
            self.client_name,
            self.email,
            self.product,
            self.size,
            self.price
        )
        await interaction.response.send_modal(modal2)

class FactureModalDior2(ui.Modal, title="Détails Commande"):
    order_number = ui.TextInput(label="Numéro de commande", placeholder="Ex: 3070080226406")
    image_url = ui.TextInput(
        label="URL de l'image",
        placeholder="https://exemple.com/image.jpg"
    )

    def __init__(self, template_name, client_name, email, product, size, price):
        super().__init__()
        self.template_name = template_name
        self.client_name = client_name
        self.email = email
        self.product = product
        self.size = size
        self.price = price

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        try:
            data = {
                "client_name": self.client_name,
                "email": self.email,
                "product": self.product,
                "size": self.size,
                "order_number": self.order_number.value,
                "price": self.price,
                "image_url": self.image_url.value,
                "order_total": str(int(self.price) + 15),
            }

            env = Environment(loader=FileSystemLoader('src/templates'))
            template = env.get_template(self.template_name)
            html_out = template.render(**data)

            sujet = f"Facture : {self.product}"
            email_envoye = send_invoice_email(self.email, sujet, html_out)

            status_msg = "vient juste de générer une facture" if email_envoye else "⚠️ **Echec de l'envoi par mail.**"
            
            file_buffer = BytesIO(html_out.encode('utf-8'))
            file_buffer.seek(0)

            await interaction.followup.send(
                content=f"{interaction.user.mention} {status_msg}\n **Regarde tes mails.**",
            )

        except Exception as e:
            await interaction.followup.send(f"Erreur : {e}")


class TemplateSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Moncler", value="moncler.html", description="Facture Moncler", emoji="✨"),
            discord.SelectOption(label="Dior", value="dior.html", description="Facture Dior", emoji="✨"),
            discord.SelectOption(label="Maison Margiela", value="margeilagates.html", description="Facture Maison Margiela", emoji="✨"),
        ]
        super().__init__(placeholder="Choisis le template de facture...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        chosen_template = self.values[0]
        if chosen_template == "moncler.html":
            await interaction.response.send_modal(FactureModal1(chosen_template))
        elif chosen_template == "dior.html":
            await interaction.response.send_modal(FactureModalDior(chosen_template))
        elif chosen_template == "margeilagates.html":
            print("in construction")


class InvoiceView(ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(TemplateSelect())