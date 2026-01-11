import discord
from discord import ui
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from src.email_utils import send_invoice_email


TEMPLATE_CONFIG = {
    "moncler.html": {
        "label": "Moncler",
        "description": "Facture Moncler",
        "emoji": "✨",
        "fields": [
            # Page 1
            [
                {"name": "client_name", "label": "Nom complet", "placeholder": "Ex: John Doe"},
                {"name": "email", "label": "Email", "placeholder": "john.doe@exemple.com"},
                {"name": "product", "label": "Article", "placeholder": "Ex: Moncler Maya Jacket"},
                {"name": "size", "label": "Taille", "placeholder": "Ex: L"},
                {"name": "colour", "label": "Couleur", "placeholder": "Ex: noir"},
            ],
            # Page 2
            [
                {"name": "order_date", "label": "Date de la commande", "placeholder": "Ex: 20/05/18"},
                {"name": "estimated_delivery", "label": "Livraison estimée", "placeholder": "Ex: 27/05/18"},
                {"name": "order_number", "label": "Numéro de commande", "placeholder": "Ex: 3070080226406"},
                {"name": "price", "label": "Prix (sans symbole)", "placeholder": "1380"},
                {"name": "image_url", "label": "URL de l'image", "placeholder": "https://exemple.com/image.jpg"},
            ]
        ]
    },
    "dior.html": {
        "label": "Dior",
        "description": "Facture Dior",
        "emoji": "✨",
        "fields": [
            [
                {"name": "client_name", "label": "Nom complet", "placeholder": "Ex: John Doe"},
                {"name": "email", "label": "Email", "placeholder": "john.doe@exemple.com"},
                {"name": "product", "label": "Article", "placeholder": "Ex: Sneaker B30 Countdown"},
                {"name": "size", "label": "Taille", "placeholder": "Ex: 43"},
                {"name": "price", "label": "Prix (sans symbole)", "placeholder": "Ex: 800"},
            ],
            [
                {"name": "order_number", "label": "Numéro de commande", "placeholder": "Ex: 3070080226406"},
                {"name": "image_url", "label": "URL de l'image", "placeholder": "https://exemple.com/image.jpg"},
            ]
        ]
    },
    # "margeilagates.html": {
    #     "label": "Maison Margiela",
    #     "description": "Facture Maison Margiela",
    #     "emoji": "✨",
    #     "fields": [
    #         [
    #             {"name": "client_name", "label": "Nom complet", "placeholder": "Ex: John Doe"},
    #             {"name": "email", "label": "Email", "placeholder": "john.doe@exemple.com"},
    #             {"name": "product", "label": "Article", "placeholder": "Ex: Tabi Boots"},
    #             {"name": "size", "label": "Taille", "placeholder": "Ex: 42"},
    #         ],
    #         [
    #             {"name": "order_number", "label": "Numéro de commande", "placeholder": "Ex: 3070080226406"},
    #             {"name": "price", "label": "Prix (sans symbole)", "placeholder": "Ex: 950"},
    #             {"name": "image_url", "label": "URL de l'image", "placeholder": "https://exemple.com/image.jpg"},
    #         ]
    #     ]
    # },
    "stockx.html": {
        "label": "Stock x",
        "description": "Facture Stock x",
        "emoji": "✨",
        "fields": [
            [
                {"name": "style_id", "label": "ID Style", "placeholder": "Ex: 5287"},
                {"name": "order_date", "label": "Date de la commande", "placeholder": "Ex: 20/05/18"},
                {"name": "email", "label": "Email", "placeholder": "john.doe@exemple.com"},
                {"name": "product", "label": "Article", "placeholder": "Ex: Golden Goose Dadstar"},
                {"name": "size", "label": "Taille", "placeholder": "Ex: 44"},
            ],
            [
                {"name": "order_number", "label": "Numéro de commande", "placeholder": "Ex: 3070080226406"},
                {"name": "price", "label": "Prix de l'article (sans symbole)", "placeholder": "Ex: 525"},
                {"name": "processing_fee", "label": "Frais de traitement (sans symbole)", "placeholder": "Ex: 31.59"},
                {"name": "shipping", "label": "Frais de livraison (sans symbole)", "placeholder": "Ex: 10.95"},
                {"name": "image_url", "label": "URL de l'image", "placeholder": "https://exemple.com/image.jpg"},
            ]
        ]
    },
}


class DynamicModal(ui.Modal):
    
    def __init__(self, template_name, page_index, data=None):
        config = TEMPLATE_CONFIG[template_name]
        page_fields = config["fields"][page_index]
        
        title = f"Détails Client" if page_index == 0 else "Détails Commande"
        super().__init__(title=title)
        
        self.template_name = template_name
        self.page_index = page_index
        self.previous_data = data or {}
        self.inputs = {}
        
        for field_config in page_fields:
            text_input = ui.TextInput(
                label=field_config["label"],
                placeholder=field_config["placeholder"],
                required=True
            )
            self.inputs[field_config["name"]] = text_input
            self.add_item(text_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        all_data = {**self.previous_data}
        for name, input_field in self.inputs.items():
            all_data[name] = input_field.value
        
        config = TEMPLATE_CONFIG[self.template_name]
        total_pages = len(config["fields"])
        
        if self.page_index < total_pages - 1:
            view = ContinueView(
                self.template_name,
                self.page_index + 1,
                all_data
            )
            await interaction.response.send_message(
                "Clique sur le bouton pour continuer :",
                view=view,
                ephemeral=True
            )
        else:
            await self.generate_invoice(interaction, all_data)
    
    async def generate_invoice(self, interaction: discord.Interaction, data):
        await interaction.response.defer(thinking=True)
        
        try:
            if self.template_name == "moncler.html" or self.template_name == "dior.html":
                data["order_total"] = str(int(data["price"]) + 15)
            elif self.template_name == "stockx.html":
                data["order_total"] = str(round(
                float(data["price"]) + 
                float(data["processing_fee"]) + 
                float(data["shipping"])
                , 2)
            )
            
            env = Environment(loader=FileSystemLoader('src/templates'))
            template = env.get_template(self.template_name)
            html_out = template.render(**data)
            
            sujet = f"Facture : {data.get('product', 'Commande')}"
            email_envoye = send_invoice_email(data["email"], sujet, html_out)
            
            status_msg = "vient juste de générer une facture" if email_envoye else "⚠️ **Echec de l'envoi par mail.**"
            
            await interaction.followup.send(
                content=f"{interaction.user.mention} {status_msg}\n **Regarde tes mails.**",
            )
        
        except Exception as e:
            await interaction.followup.send(f"Erreur : {e}")


class ContinueView(ui.View):
    
    def __init__(self, template_name, next_page_index, data):
        super().__init__(timeout=300)
        self.template_name = template_name
        self.next_page_index = next_page_index
        self.data = data
    
    @ui.button(label="Continuer", style=discord.ButtonStyle.primary)
    async def continue_button(self, interaction: discord.Interaction, button: ui.Button):
        next_modal = DynamicModal(
            self.template_name,
            self.next_page_index,
            self.data
        )
        await interaction.response.send_modal(next_modal)


class TemplateSelect(ui.Select):
    
    def __init__(self):
        options = [
            discord.SelectOption(
                label=config["label"],
                value=template_name,
                description=config["description"],
                emoji=config["emoji"]
            )
            for template_name, config in TEMPLATE_CONFIG.items()
        ]
        super().__init__(
            placeholder="Choisis le template de facture...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        chosen_template = self.values[0]
        
        first_modal = DynamicModal(chosen_template, page_index=0)
        await interaction.response.send_modal(first_modal)


class InvoiceView(ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(TemplateSelect())