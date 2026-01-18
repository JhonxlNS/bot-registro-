"""
BOT DE REGISTRO DISCORD - VERSÃO FINAL 100% FUNCIONAL
"""

import os
import sys
import json
import time

print("=" * 60)
print("🤖 BOT DE REGISTRO DISCORD - VERSÃO FINAL")
print("=" * 60)
print(f"🐍 Python: {sys.version.split()[0]}")
print("=" * 60)

# ========== IMPORT DISCORD PRIMEIRO ==========
try:
    import discord
    from discord import app_commands
    print(f"✅ Discord.py {discord.__version__} importado!")
except ImportError as e:
    print(f"❌ Erro ao importar discord: {e}")
    print("📦 Instalando dependências...")
    os.system("pip install discord.py==2.3.2 Flask==2.3.3")
    import discord
    from discord import app_commands

import datetime
import asyncio
from typing import Optional

# ========== CONFIGURAÇÃO DO BOT ==========
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
        
        # Atividade
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="sistema de registro"
            )
        )

bot = RegistrationBot()

# ========== CONFIGURAÇÕES ==========
CONFIG_FILE = "config.json"

def load_config():
    """Carrega configurações"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # Configuração padrão
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
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        print("✅ config.json criado")
    except:
        pass
    
    return default_config

def save_config(config):
    """Salva configurações"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

config = load_config()

# ========== FUNÇÕES AUXILIARES ==========
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

async def update_nickname(member, nome, user_id_num, guild_id):
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

# ========== COMANDOS SLASH ==========

@bot.tree.command(name="setup", description="Configurar sistema de registro")
@app_commands.describe(
    tag="Tag para novos membros (ex: 77K)",
    cargo="Cargo automático",
    canal_registro="Canal de registro",
    canal_aprovacao="Canal de aprovação"
)
async def setup(interaction: discord.Interaction, tag: str, cargo: discord.Role, 
                canal_registro: discord.TextChannel, canal_aprovacao: discord.TextChannel):
    
    if not is_admin(interaction):
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    
    # Salvar configurações
    config["tag_config"][guild_id] = tag
    config["auto_roles"][guild_id] = cargo.id
    config["register_channels"][guild_id] = canal_registro.id
    config["approval_channels"][guild_id] = canal_aprovacao.id
    
    if save_config(config):
        embed = discord.Embed(
            title="✅ SISTEMA CONFIGURADO",
            description="Tudo configurado com sucesso!",
            color=discord.Color.green()
        )
        
        embed.add_field(name="🏷️ Tag", value=f"`{tag}`", inline=True)
        embed.add_field(name="🎭 Cargo", value=cargo.mention, inline=True)
        embed.add_field(name="📝 Canal de Registro", value=canal_registro.mention, inline=True)
        embed.add_field(name="✅ Canal de Aprovação", value=canal_aprovacao.mention, inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Criar painéis
        await create_painel_registro(canal_registro, guild_id, tag, cargo)
        await create_painel_aprovacao(canal_aprovacao, guild_id)
    else:
        await interaction.response.send_message("❌ Erro ao salvar configuração!", ephemeral=True)

async def create_painel_registro(channel, guild_id, tag, cargo):
    """Cria painel de registro"""
    embed = discord.Embed(
        title="📝 REGISTRO NO SERVIDOR",
        description=(
            "**Clique no botão abaixo para solicitar registro!**\n\n"
            "📋 **Informações necessárias:**\n"
            "• Nome completo\n"
            "• Seu ID\n"
            "• Quem te recrutou\n\n"
            f"🏷️ **Seu nickname será:** `{tag}・NOME | ID`\n"
            f"🎭 **Cargo recebido:** {cargo.mention}"
        ),
        color=discord.Color.blue()
    )
    
    button = discord.ui.Button(
        style=discord.ButtonStyle.primary,
        label="📝 Solicitar Registro",
        custom_id=f"registrar_{guild_id}",
        emoji="📝"
    )
    
    view = discord.ui.View(timeout=None)
    view.add_item(button)
    
    await channel.send(embed=embed, view=view)

async def create_painel_aprovacao(channel, guild_id):
    """Cria painel de aprovação"""
    embed = discord.Embed(
        title="✅ PAINEL DE APROVAÇÃO",
        description=(
            "**Solicitações de registro aparecerão aqui**\n\n"
            "👨‍⚖️ **Para a staff:**\n"
            "• Use ✅ para aprovar registros\n"
            "• Use ❌ para recusar registros\n\n"
            "⚙️ **Processo automático:**\n"
            "• Tag aplicada automaticamente\n"
            "• Cargo dado automaticamente\n"
            "• Usuário notificado via DM"
        ),
        color=discord.Color.green()
    )
    
    await channel.send(embed=embed)

class RegistroModal(discord.ui.Modal, title="📝 Formulário de Registro"):
    def __init__(self, guild_id):
        super().__init__()
        self.guild_id = guild_id
    
    nome = discord.ui.TextInput(
        label="Seu nome completo",
        placeholder="Ex: João Silva",
        max_length=32,
        required=True
    )
    
    user_id = discord.ui.TextInput(
        label="Seu ID",
        placeholder="Ex: 1001, 777, 888",
        max_length=10,
        required=True
    )
    
    recrutador = discord.ui.TextInput(
        label="Quem te recrutou?",
        placeholder="Nome da pessoa que te indicou",
        max_length=32,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        member = interaction.user
        
        # Verificar canal de aprovação
        app_channel_id = config["approval_channels"].get(self.guild_id)
        if not app_channel_id:
            await interaction.followup.send("❌ Sistema não configurado! Use /setup primeiro.", ephemeral=True)
            return
        
        app_channel = guild.get_channel(app_channel_id)
        if not app_channel:
            await interaction.followup.send("❌ Canal de aprovação não encontrado!", ephemeral=True)
            return
        
        # Embed da solicitação
        embed = discord.Embed(
            title="🔄 NOVA SOLICITAÇÃO DE REGISTRO",
            description=f"Usuário: {member.mention}",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="👤 Nome", value=self.nome.value, inline=True)
        embed.add_field(name="#️⃣ ID", value=self.user_id.value, inline=True)
        embed.add_field(name="👥 Recrutador", value=self.recrutador.value, inline=True)
        embed.add_field(name="🆔 Discord ID", value=member.id, inline=True)
        embed.add_field(name="📅 Data", value=datetime.datetime.now().strftime("%d/%m %H:%M"), inline=True)
        
        # Botões de aprovação
        view = AprovacaoView(
            user_id=member.id,
            nome=self.nome.value,
            user_id_num=self.user_id.value,
            recrutador=self.recrutador.value,
            guild_id=self.guild_id
        )
        
        # Enviar para canal de aprovação
        await app_channel.send(embed=embed, view=view)
        
        await interaction.followup.send(
            "✅ **Solicitação enviada com sucesso!**\n"
            f"📋 Sua solicitação foi enviada para {app_channel.mention}\n"
            "⏳ Aguarde a aprovação da staff.",
            ephemeral=True
        )

class AprovacaoView(discord.ui.View):
    def __init__(self, user_id, nome, user_id_num, recrutador, guild_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.nome = nome
        self.user_id_num = user_id_num
        self.recrutador = recrutador
        self.guild_id = guild_id
    
    @discord.ui.button(label="✅ Aprovar", style=discord.ButtonStyle.success, custom_id="aprovar_btn")
    async def aprovar_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction):
            await interaction.response.send_message("❌ Apenas staff pode aprovar!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        guild = interaction.guild
        member = guild.get_member(self.user_id)
        
        if not member:
            # Atualizar embed se usuário não encontrado
            embed = interaction.message.embeds[0]
            embed.title = "❌ USUÁRIO NÃO ENCONTRADO"
            embed.color = discord.Color.red()
            await interaction.message.edit(embed=embed, view=None)
            await interaction.followup.send("❌ Usuário saiu do servidor!", ephemeral=True)
            return
        
        # 1. Atualizar nickname
        success_nick, nickname = await update_nickname(member, self.nome, self.user_id_num, self.guild_id)
        
        # 2. Aplicar cargo
        cargo_added = False
        cargo_id = config["auto_roles"].get(self.guild_id)
        if cargo_id:
            cargo = guild.get_role(cargo_id)
            if cargo:
                try:
                    await member.add_roles(cargo)
                    cargo_added = True
                except:
                    pass
        
        # 3. Atualizar embed da solicitação
        embed = interaction.message.embeds[0]
        embed.title = "✅ REGISTRO APROVADO"
        embed.color = discord.Color.green()
        embed.add_field(name="👤 Aprovado por", value=interaction.user.mention, inline=True)
        
        if success_nick:
            embed.add_field(name="🏷️ Nickname Atualizado", value=nickname, inline=True)
        
        if cargo_added:
            embed.add_field(name="🎭 Cargo", value="✅ Aplicado", inline=True)
        
        embed.add_field(name="⏰ Hora", value=datetime.datetime.now().strftime("%H:%M:%S"), inline=True)
        
        await interaction.message.edit(embed=embed, view=None)
        
        # 4. Notificar usuário
        try:
            notify_embed = discord.Embed(
                title="🎉 SEU REGISTRO FOI APROVADO!",
                description=f"Bem-vindo(a) ao **{guild.name}**!",
                color=discord.Color.green()
            )
            
            if success_nick:
                notify_embed.add_field(name="🏷️ Seu Nickname", value=nickname, inline=False)
            
            notify_embed.add_field(name="👤 Aprovado por", value=interaction.user.name, inline=True)
            
            await member.send(embed=notify_embed)
        except:
            pass  # Usuário tem DM bloqueada
        
        await interaction.followup.send(f"✅ {member.mention} registrado com sucesso!", ephemeral=True)
    
    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger, custom_id="recusar_btn")
    async def recusar_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin(interaction):
            await interaction.response.send_message("❌ Apenas staff pode recusar!", ephemeral=True)
            return
        
        embed = interaction.message.embeds[0]
        embed.title = "❌ REGISTRO RECUSADO"
        embed.color = discord.Color.red()
        embed.add_field(name="👤 Recusado por", value=interaction.user.mention, inline=True)
        embed.add_field(name="⏰ Hora", value=datetime.datetime.now().strftime("%H:%M:%S"), inline=True)
        
        await interaction.message.edit(embed=embed, view=None)
        
        # Notificar usuário
        try:
            member = interaction.guild.get_member(self.user_id)
            if member:
                await member.send(f"❌ Seu registro no **{interaction.guild.name}** foi recusado pela staff.")
        except:
            pass
        
        await interaction.response.send_message("❌ Registro recusado!", ephemeral=True)

@bot.tree.command(name="add_admin", description="Adicionar administrador")
@app_commands.describe(usuario="Usuário para tornar admin")
async def add_admin(interaction: discord.Interaction, usuario: discord.User):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores do servidor!", ephemeral=True)
        return
    
    if usuario.id not in config["admins"]:
        config["admins"].append(usuario.id)
        if save_config(config):
            await interaction.response.send_message(f"✅ {usuario.mention} adicionado como administrador!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Erro ao salvar!", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ {usuario.mention} já é administrador!", ephemeral=True)

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
        embed.description = admins_text or "Nenhum admin"
    else:
        embed.description = "Nenhum admin configurado"
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="limpar", description="Limpar mensagens")
@app_commands.describe(quantidade="Quantidade de mensagens (máx 100)")
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
        value="`/setup` - Configurar sistema\n`/add_admin` - Adicionar admin\n`/list_admins` - Listar admins",
        inline=False
    )
    
    embed.add_field(
        name="🛠️ FERRAMENTAS",
        value="`/limpar` - Limpar mensagens\n`/status` - Ver status\n`/ajuda` - Esta mensagem\n`/ping` - Testar latência",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ping", description="Testar latência")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! {latency}ms", ephemeral=True)

# ========== EVENTOS ==========
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como: {bot.user}")
    print(f"📊 Servidores: {len(bot.guilds)}")
    print(f"👥 Total de usuários: {sum(g.member_count for g in bot.guilds)}")
    print(f"⏰ Iniciado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Manipula interações de botões"""
    try:
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get('custom_id', '')
            
            if custom_id.startswith("registrar_"):
                guild_id = custom_id.replace("registrar_", "")
                
                # Verificar se é o canal correto
                reg_channel_id = config["register_channels"].get(guild_id)
                if not reg_channel_id or interaction.channel.id != reg_channel_id:
                    await interaction.response.send_message(
                        "❌ Use o botão no canal de registro correto!",
                        ephemeral=True
                    )
                    return
                
                modal = RegistroModal(guild_id)
                await interaction.response.send_modal(modal)
    except Exception as e:
        print(f"Erro na interação: {e}")

# ========== SERVIDOR WEB SIMPLES ==========
try:
    from flask import Flask
    from threading import Thread
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return "🤖 Bot Discord Online - Sistema de Registro"
    
    @app.route('/health')
    def health():
        return "OK", 200
    
    @app.route('/ping')
    def ping():
        return "pong", 200
    
    def run_flask():
        port = int(os.environ.get('PORT', 8080))
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    
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
    
    # Iniciar servidor web
    start_web_server()
    
except ImportError:
    print("⚠️ Flask não instalado, servidor web não iniciado")
    print("💡 Para servidor web, adicione 'Flask' no requirements.txt")

# ========== INICIALIZAÇÃO ==========
def main():
    print("🚀 Iniciando bot Discord...")
    
    # Token
    token = config.get("TOKEN")
    if not token or token == "SEU_TOKEN_AQUI":
        token = os.environ.get("DISCORD_TOKEN")
    
    if not token or token == "SEU_TOKEN_AQUI":
        print("\n❌ TOKEN NÃO CONFIGURADO!")
        print("\n📝 CONFIGURAÇÃO:")
        print("1. No painel da Discloud, vá em 'Environment'")
        print("2. Adicione: DISCORD_TOKEN")
        print("3. Cole seu token do bot")
        print("\n📍 Obtenha o token em: https://discord.com/developers/applications")
        print("=" * 60)
        return
    
    print("✅ Token configurado")
    print("🤖 Conectando ao Discord...")
    print("=" * 60)
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        print("❌ TOKEN INVÁLIDO!")
        print("Verifique se o token está correto")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    main()
