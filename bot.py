import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# ================== CONFIG ==================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
ROL_AUTORIZADO = 1463765341158244389

ARCHIVO = "facturas.json"

COLOR_OK = 0x2ecc71      # Verde
COLOR_ERROR = 0xe74c3c   # Rojo
COLOR_INFO = 0x3498db    # Azul

# ============================================


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ---------- Cargar datos ----------

def cargar_datos():
    if not os.path.exists(ARCHIVO):
        return {}

    with open(ARCHIVO, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_datos(data):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


datos = cargar_datos()


# ---------- Crear embed base ----------

def crear_embed(titulo, descripcion, color, interaction):
    embed = discord.Embed(
        title=titulo,
        description=descripcion,
        color=color,
        timestamp=datetime.now(timezone.utc)
    )

    embed.set_footer(
        text=f"Solicitado por {interaction.user}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )

    return embed


# ---------- Verificar rol ----------

def tiene_rol(interaction: discord.Interaction):
    return any(role.id == ROL_AUTORIZADO for role in interaction.user.roles)


# ---------- Sync ----------

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot conectado como {bot.user}")


# ---------- /factura ----------

@bot.tree.command(name="factura", description="Crear una factura")
@app_commands.describe(monto="Monto de la factura")
async def factura(interaction: discord.Interaction, monto: int):

    if not tiene_rol(interaction):

        embed = crear_embed(
            "❌ Sin permiso",
            "No tenés permiso para usar este comando.",
            COLOR_ERROR,
            interaction
        )

        await interaction.response.send_message(embed=embed)
        return


    user_id = str(interaction.user.id)

    if user_id not in datos:
        datos[user_id] = {
            "contador": 0,
            "total": 0,
            "facturas": []
        }


    datos[user_id]["contador"] += 1
    numero = datos[user_id]["contador"]

    datos[user_id]["total"] += monto

    datos[user_id]["facturas"].append({
        "num": numero,
        "monto": monto,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
    })

    guardar_datos(datos)


    embed = crear_embed(
        "✅ Factura creada",
        f"📄 **Número:** {numero}\n💰 **Monto:** ${monto}",
        COLOR_OK,
        interaction
    )

    await interaction.response.send_message(embed=embed)


# ---------- /verfactura ----------

@bot.tree.command(name="verfactura", description="Ver total facturado")
async def verfactura(interaction: discord.Interaction):

    if not tiene_rol(interaction):

        embed = crear_embed(
            "❌ Sin permiso",
            "No tenés permiso para usar este comando.",
            COLOR_ERROR,
            interaction
        )

        await interaction.response.send_message(embed=embed)
        return


    user_id = str(interaction.user.id)

    if user_id not in datos:

        embed = crear_embed(
            "📭 Sin facturas",
            "Todavía no tenés facturas registradas.",
            COLOR_INFO,
            interaction
        )

        await interaction.response.send_message(embed=embed)
        return


    total = datos[user_id]["total"]
    cantidad = datos[user_id]["contador"]


    embed = crear_embed(
        "📊 Resumen de facturación",
        f"📄 **Facturas:** {cantidad}\n💰 **Total:** ${total}",
        COLOR_INFO,
        interaction
    )

    await interaction.response.send_message(embed=embed)


# ---------- /resetfacturas ----------

@bot.tree.command(name="resetfacturas", description="Resetear tus facturas")
async def resetfacturas(interaction: discord.Interaction):

    if not tiene_rol(interaction):

        embed = crear_embed(
            "❌ Sin permiso",
            "No tenés permiso para usar este comando.",
            COLOR_ERROR,
            interaction
        )

        await interaction.response.send_message(embed=embed)
        return


    user_id = str(interaction.user.id)


    if user_id in datos:

        datos[user_id] = {
            "contador": 0,
            "total": 0,
            "facturas": []
        }

        guardar_datos(datos)


        embed = crear_embed(
            "🔄 Facturas reiniciadas",
            "Tu historial fue borrado correctamente.",
            COLOR_OK,
            interaction
        )

    else:

        embed = crear_embed(
            "📭 Sin datos",
            "No tenías facturas registradas.",
            COLOR_INFO,
            interaction
        )


    await interaction.response.send_message(embed=embed)


# ---------- /historial ----------

@bot.tree.command(name="historial", description="Ver historial de facturas")
async def historial(interaction: discord.Interaction):

    if not tiene_rol(interaction):

        embed = crear_embed(
            "❌ Sin permiso",
            "No tenés permiso para usar este comando.",
            COLOR_ERROR,
            interaction
        )

        await interaction.response.send_message(embed=embed)
        return


    user_id = str(interaction.user.id)


    if user_id not in datos or not datos[user_id]["facturas"]:

        embed = crear_embed(
            "📭 Sin historial",
            "No hay facturas registradas.",
            COLOR_INFO,
            interaction
        )

        await interaction.response.send_message(embed=embed)
        return


    embed = discord.Embed(
        title="📁 Historial de facturas",
        color=COLOR_INFO,
        timestamp=datetime.now(timezone.utc)
    )

    embed.set_footer(
        text=f"Solicitado por {interaction.user}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )


    for f in datos[user_id]["facturas"][-10:]:

        embed.add_field(
            name=f"Factura #{f['num']}",
            value=f"💰 ${f['monto']}\n📅 {f['fecha']}",
            inline=False
        )


    await interaction.response.send_message(embed=embed)


# ---------- /editarfactura ----------

@bot.tree.command(name="editarfactura", description="Editar una factura existente")
@app_commands.describe(
    numero="Número de la factura",
    nuevo_monto="Nuevo monto"
)
async def editarfactura(
    interaction: discord.Interaction,
    numero: int,
    nuevo_monto: int
):

    if not tiene_rol(interaction):

        embed = crear_embed(
            "❌ Sin permiso",
            "No tenés permiso para usar este comando.",
            COLOR_ERROR,
            interaction
        )

        await interaction.response.send_message(embed=embed)
        return


    user_id = str(interaction.user.id)

    if user_id not in datos or not datos[user_id]["facturas"]:

        embed = crear_embed(
            "📭 Sin facturas",
            "No tenés facturas para editar.",
            COLOR_INFO,
            interaction
        )

        await interaction.response.send_message(embed=embed)
        return


    factura_encontrada = None

    for f in datos[user_id]["facturas"]:
        if f["num"] == numero:
            factura_encontrada = f
            break


    if not factura_encontrada:

        embed = crear_embed(
            "❌ No encontrada",
            f"No existe la factura #{numero}.",
            COLOR_ERROR,
            interaction
        )

        await interaction.response.send_message(embed=embed)
        return


    monto_viejo = factura_encontrada["monto"]

    factura_encontrada["monto"] = nuevo_monto


    # Recalcular total
    nuevo_total = sum(f["monto"] for f in datos[user_id]["facturas"])
    datos[user_id]["total"] = nuevo_total

    guardar_datos(datos)


    descripcion = (
        f"📄 **Factura:** #{numero}\n"
        f"💰 **Antes:** ${monto_viejo}\n"
        f"💵 **Ahora:** ${nuevo_monto}\n"
        f"📊 **Total actualizado:** ${nuevo_total}"
    )


    embed = crear_embed(
        "✏️ Factura editada",
        descripcion,
        COLOR_OK,
        interaction
    )

    await interaction.response.send_message(embed=embed)

# ---------- Iniciar bot ----------

bot.run(TOKEN)
