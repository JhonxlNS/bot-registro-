"""
main.py - Bot de Registro Discord 100% Funcional
Compatível com: Shard Cloud, Railway, Render, VPS, etc.
"""

import discord
from discord import app_commands
import os
import json
import datetime
import asyncio
import time
from typing import Optional

# ================= CONFIGURAÇÃO INICIAL =================
print("=" * 60)
print("🤖 BOT DE REGISTRO DISCORD - 100% GARANTIDO")
print("=" * 60)
print(f"🐍 Python: {os.sys.version}")
print(f"📁 Diretório: {os.getcwd()}")
print("=" * 60)

# Configurar intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

class RegistrationBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.start_time = time.time()

    async def setup_hook(self):
        try:
            synced = await self.tree.sync()
            print(f"✅ {len(synced)} comandos sincronizados")
        except Exception as e:
            print(f"⚠️ Erro ao sincronizar: {e}")
        print("✅ Bot pronto para uso!")

bot = RegistrationBot()

# ================= CONFIGURAÇÕES =================
CONFIG_FILE = "config.json"

def load_config():
    """Carrega ou cria configuração"""
    default_config = {
        "TOKEN": os.environ.get("DISCORD_TOKEN", "SEU_TOKEN_AQUI"),
        "auto_roles": {},
        "tag_config": {},
        "register_channels": {},
        "approval_channels": {},
        "admins": [],
        "super_admins": [],
        "settings": {
            "approval_enabled": True,
            "auto_nickname": True
        }
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Garantir que tem todas as chaves
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        else:
            return default_config
    except Exception:
        return default_config

def save_config(config):
    """Salva configuração"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

config = load_config()

# ================= FUNÇÕES AUXILIARES =================
def is_admin(interaction):
    """Verifica se é admin"""
    user = interaction.user
    if user.id == interaction.guild.owner_id:
        return True
    if user.id in config.get("super_admins", []):
        return True
    if user.id in config.get("admins", []):
        return True
    if user.guild_permissions.administrator:
        return True
    return False

async def update_user_nickname(member, nome, user_id_num, guild_id):
    """Atualiza nickname"""
    tag = config["tag_config"].get(str(guild_id), "")
    
    if tag:
        nickname = f"{tag}・{nome} | {user_id_num}"
    else:
        nickname = f"{nome} | {user_id_num}"
    
    if len(nickname) > 32:
        nickname = nickname[:32]
    
    try:
        await member.edit(nick=nickname)
        return True, nickname
    except:
        return False, "Erro"

# ================= COMANDOS SLASH =================

# === CONFIGURAÇÃO ===
@bot.tree.command(name="setup", description="Configurar sistema de registro")
@app_commands.describe(
    tag="Tag para novos membros",
    cargo="Cargo automático",
    canal_registro="Canal de registro",
    canal_aprovacao="Canal de aprovação"
)
async def setup(interaction: discord.Interaction, 
                tag: str, 
                cargo: discord.Role, 
                canal_registro: discord.TextChannel, 
                canal_aprovacao: discord.TextChannel):
    
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    
    config["tag_config"][guild_id] = tag
    config["auto_roles"][guild_id] = cargo.id
    config["register_channels"][guild_id] = canal_registro.id
    config["approval_channels"][guild_id] = canal_aprovacao.id
    
    if save_config(config):
        embed = discord.Embed(
            title="✅ SISTEMA CONFIGURADO",
            color=discord.Color.green()
        )
        embed.add_field(name="🏷️ Tag", value=tag, inline=True)
        embed.add_field(name="🎭 Cargo", value=cargo.mention, inline=True)
        embed.add_field(name="📝 Registro", value=canal_registro.mention, inline=True)
        embed.add_field(name="✅ Aprovação", value=canal_aprovacao.mention, inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Criar painéis
        await create_painel_registro(canal_registro, guild_id, tag, cargo)
        await create_painel_aprovacao(canal_aprovacao, guild_id)
    else:
        await interaction.response.send_message("❌ Erro ao salvar!", ephemeral=True)

async def create_painel_registro(channel, guild_id, tag, cargo):
    """Cria painel de registro"""
    embed = discord.Embed(
        title="📝 REGISTRO NO SERVIDOR",
        description="Clique no botão abaixo para se registrar!",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="🏷️ Seu nickname será", value=f"`{tag}・NOME | ID`", inline=False)
    embed.add_field(name="🎭 Cargo recebido", value=cargo.mention, inline=False)
    
    button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label="📝 Solicitar Registro",
        custom_id=f"registrar_{guild_id}"
    )
    
    view = discord.ui.View(timeout=None)
    view.add_item(button)
    
    await channel.send(embed=embed, view=view)

async def create_painel_aprovacao(channel, guild_id):
    """Cria painel de aprovação"""
    embed = discord.Embed(
        title="✅ PAINEL DE APROVAÇÃO",
        description="Solicitações aparecerão aqui para aprovação da staff.",
        color=discord.Color.green()
    )
    
    await channel.send(embed=embed)

# === REGISTRO ===
class RegistroModal(discord.ui.Modal, title="📝 Formulário de Registro"):
    def __init__(self, guild_id):
        super().__init__()
        self.guild_id = guild_id
    
    nome = discord.ui.TextInput(
        label="Nome completo",
        placeholder="Ex: João Silva",
        max_length=32,
        required=True
    )
    
    user_id = discord.ui.TextInput(
        label="Seu ID",
        placeholder="Ex: 1001, 777",
        max_length=10,
        required=True
    )
    
    recrutador = discord.ui.TextInput(
        label="Quem te recrutou?",
        placeholder="Nome do recrutador",
        max_length=32,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        app_channel_id = config["approval_channels"].get(self.guild_id)
        
        if not app_channel_id:
            await interaction.followup.send("❌ Sistema não configurado!", ephemeral=True)
            return
        
        app_channel = guild.get_channel(app_channel_id)
        if not app_channel:
            await interaction.followup.send("❌ Canal não encontrado!", ephemeral=True)
            return
        
        # Criar embed da solicitação
        embed = discord.Embed(
            title="🔄 NOVA SOLICITAÇÃO",
            description=f"Usuário: {interaction.user.mention}",
            color=discord.Color.orange()
        )
        
        embed.add_field(name="👤 Nome", value=self.nome.value, inline=True)
        embed.add_field(name="#️⃣ ID", value=self.user_id.value, inline=True)
        embed.add_field(name="👥 Recrutador", value=self.recrutador.value, inline=True)
        embed.add_field(name="🆔 Discord ID", value=interaction.user.id, inline=True)
        embed.add_field(name="📅 Data", value=datetime.datetime.now().strftime("%d/%m %H:%M"), inline=True)
        
        # Botões de aprovação
        view = AprovacaoView(
            user_id=interaction.user.id,
            nome=self.nome.value,
            user_id_num=self.user_id.value,
            recrutador=self.recrutador.value,
            guild_id=self.guild_id
        )
        
        await app_channel.send(embed=embed, view=view)
        await interaction.followup.send("✅ Solicitação enviada para aprovação!", ephemeral=True)

class AprovacaoView(discord.ui.View):
    def __init__(self, user_id, nome, user_id_num, recrutador, guild_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.nome = nome
        self.user_id_num = user_id_num
        self.recrutador = recrutador
        self.guild_id = guild_id
    
    @discord.ui.button(label="✅ Aprovar", style=discord.ButtonStyle.success)
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction):
            await interaction.response.send_message("❌ Apenas staff!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        member = interaction.guild.get_member(self.user_id)
        if not member:
            embed = interaction.message.embeds[0]
            embed.title = "❌ USUÁRIO NÃO ENCONTRADO"
            embed.color = discord.Color.red()
            await interaction.message.edit(embed=embed, view=None)
            return
        
        # Atualizar nickname
        success_nick, nickname = await update_user_nickname(member, self.nome, self.user_id_num, self.guild_id)
        
        # Aplicar cargo
        cargo_id = config["auto_roles"].get(self.guild_id)
        cargo_added = False
        if cargo_id:
            cargo = interaction.guild.get_role(cargo_id)
            if cargo:
                try:
                    await member.add_roles(cargo)
                    cargo_added = True
                except:
                    pass
        
        # Atualizar embed
        embed = interaction.message.embeds[0]
        embed.title = "✅ REGISTRO APROVADO"
        embed.color = discord.Color.green()
        embed.add_field(name="👤 Aprovado por", value=interaction.user.mention, inline=True)
        
        if success_nick:
            embed.add_field(name="🏷️ Nickname", value=nickname, inline=True)
        
        await interaction.message.edit(embed=embed, view=None)
        
        # Notificar usuário
        try:
            await member.send(f"🎉 Seu registro foi aprovado por {interaction.user.name}!")
        except:
            pass
        
        await interaction.followup.send(f"✅ {member.mention} registrado com sucesso!", ephemeral=True)
    
    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction):
            await interaction.response.send_message("❌ Apenas staff!", ephemeral=True)
            return
        
        embed = interaction.message.embeds[0]
        embed.title = "❌ REGISTRO RECUSADO"
        embed.color = discord.Color.red()
        embed.add_field(name="👤 Recusado por", value=interaction.user.mention, inline=True)
        
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("❌ Registro recusado!", ephemeral=True)

# === COMANDOS ADMIN ===
@bot.tree.command(name="add_admin", description="Adicionar administrador")
@app_commands.describe(usuario="Usuário para tornar admin")
async def add_admin(interaction: discord.Interaction, usuario: discord.User):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    if usuario.id not in config["admins"]:
        config["admins"].append(usuario.id)
        if save_config(config):
            await interaction.response.send_message(f"✅ {usuario.mention} adicionado como admin!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Erro ao salvar!", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ {usuario.mention} já é admin!", ephemeral=True)

@bot.tree.command(name="list_admins", description="Listar administradores")
async def list_admins(interaction: discord.Interaction):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    embed = discord.Embed(title="👥 ADMINISTRADORES", color=discord.Color.blue())
    
    if config["admins"]:
        admins_text = ""
        for user_id in config["admins"]:
            user = interaction.guild.get_member(user_id)
            if user:
                admins_text += f"• {user.mention}\n"
        embed.description = admins_text or "Nenhum admin configurado"
    else:
        embed.description = "Nenhum admin configurado"
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# === FERRAMENTAS ===
@bot.tree.command(name="limpar", description="Limpar mensagens")
@app_commands.describe(quantidade="Quantidade de mensagens")
async def limpar(interaction: discord.Interaction, quantidade: int = 100):
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        deleted = await interaction.channel.purge(limit=min(quantidade, 100))
        await interaction.followup.send(f"✅ {len(deleted)} mensagens limpas!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Erro: {str(e)[:100]}", ephemeral=True)

@bot.tree.command(name="status", description="Status do sistema")
async def status(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    
    embed = discord.Embed(title="📊 STATUS DO SISTEMA", color=discord.Color.blue())
    
    tag = config["tag_config"].get(guild_id, "Não configurada")
    embed.add_field(name="🏷️ Tag", value=tag, inline=True)
    
    cargo_id = config["auto_roles"].get(guild_id)
    if cargo_id:
        cargo = interaction.guild.get_role(cargo_id)
        embed.add_field(name="🎭 Cargo", value=cargo.mention if cargo else "Não encontrado", inline=True)
    else:
        embed.add_field(name="🎭 Cargo", value="Não configurado", inline=True)
    
    embed.add_field(name="🤖 Bot", value="✅ Online", inline=True)
    embed.add_field(name="👥 Membros", value=interaction.guild.member_count, inline=True)
    embed.add_field(name="📊 Servidores", value=len(bot.guilds), inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ajuda", description="Mostrar comandos")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 CENTRAL DE AJUDA",
        description="Comandos disponíveis:",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="🔧 CONFIGURAÇÃO",
        value="`/setup` - Configurar tudo\n`/add_admin` - Adicionar admin\n`/list_admins` - Listar admins",
        inline=False
    )
    
    embed.add_field(
        name="🛠️ FERRAMENTAS",
        value="`/limpar` - Limpar mensagens\n`/status` - Ver status\n`/ajuda` - Esta mensagem",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ping", description="Testar latência")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! {latency}ms", ephemeral=True)

# === EVENTOS ===
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como: {bot.user}")
    print(f"📊 Servidores: {len(bot.guilds)}")
    print(f"⏰ Iniciado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)
    
    # Definir atividade
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} servidores"
        )
    )

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get('custom_id', '')
        
        if custom_id.startswith("registrar_"):
            guild_id = custom_id.replace("registrar_", "")
            
            # Verificar canal correto
            reg_channel_id = config["register_channels"].get(guild_id)
            if not reg_channel_id or interaction.channel.id != reg_channel_id:
                await interaction.response.send_message("❌ Use no canal correto!", ephemeral=True)
                return
            
            modal = RegistroModal(guild_id)
            await interaction.response.send_modal(modal)

# ================= SERVIDOR WEB (keep_alive embutido) =================
from flask import Flask
from threading import Thread
import requests

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "🤖 Bot Discord Online - Sistema de Registro"

@flask_app.route('/health')
def health():
    return "OK", 200

@flask_app.route('/ping')
def ping():
    return "pong", 200

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

def start_web_server():
    """Inicia servidor web em thread separada"""
    try:
        server_thread = Thread(target=run_flask, daemon=True)
        server_thread.start()
        print(f"✅ Servidor web iniciado na porta {os.environ.get('PORT', 8080)}")
        return True
    except Exception as e:
        print(f"⚠️ Servidor web não iniciado: {e}")
        return False

# ================= INICIALIZAÇÃO =================
def main():
    print("=" * 60)
    print("🚀 INICIANDO BOT DE REGISTRO DISCORD")
    print("=" * 60)
    
    # Verificar token
    token = config.get("TOKEN")
    
    if not token or token == "SEU_TOKEN_AQUI":
        token = os.environ.get("DISCORD_TOKEN")
    
    if not token or token == "SEU_TOKEN_AQUI":
        print("\n❌ TOKEN NÃO CONFIGURADO!")
        print("\n📝 CONFIGURAÇÃO:")
        print("1. No painel da hospedagem, adicione:")
        print("   Variável: DISCORD_TOKEN")
        print("   Valor: Seu token do bot")
        print("\n2. Ou edite config.json e adicione seu token")
        print("=" * 60)
        return
    
    print("✅ Token encontrado")
    print("🌐 Iniciando servidor web...")
    
    # Iniciar servidor web
    start_web_server()
    
    print("🤖 Iniciando bot Discord...")
    print("=" * 60)
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        print("❌ TOKEN INVÁLIDO!")
        print("Verifique se o token está correto")
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()
