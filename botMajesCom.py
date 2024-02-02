import discord
import random
from discord.ext import commands

intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)

# Diccionario para almacenar información sobre los canales temporales
temp_channels_info = {}

# Configuración de las tasas de bits
bitrate_options = {
    1202758723924140035: 16000,  # Canal de 16kbps
    1202759839462203503: 32000,  # Canal de 32kbps
    1202759861558055062: 64000   # Canal de 64kbps
}

@client.event
async def on_ready():
    print(f'Bot iniciado como {client.user.name}!')

@client.event
async def on_voice_state_update(member, before, after):
    # Verifica si el usuario se unió a un canal específico
    target_channels = bitrate_options.keys()

    if after.channel and after.channel.id in target_channels:
        # Canal específico al que se unió el usuario
        target_channel_id = after.channel.id

        # Crea un canal de voz temporal privado solo si el canal aún no existe
        existing_channel = discord.utils.get(member.guild.voice_channels, name=f'Temp - {member.display_name}')
        if not existing_channel:
            guild = member.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=False),
                guild.me: discord.PermissionOverwrite(connect=True, view_channel=True),
                member: discord.PermissionOverwrite(connect=True, view_channel=True)
            }

            # Obtiene la tasa de bits seleccionada
            selected_bitrate = bitrate_options[target_channel_id]

            # Obtiene la categoría temporal
            temp_category = discord.utils.get(guild.categories, name='TempVoiceChannels')
            if not temp_category:
                temp_category = await guild.create_category('TempVoiceChannels')

            # Crea el canal de voz temporal en la categoría temporal
            temp_channel = await temp_category.create_voice_channel(
                f'Temp - {member.display_name}',
                overwrites=overwrites,
                bitrate=selected_bitrate
            )

            # Mueve el canal a la posición deseada
            await temp_channel.edit(position=len(guild.voice_channels))

            # Mueve al usuario al canal temporal que acaba de crear
            await member.move_to(temp_channel)

            # Genera un código de invitación (puedes personalizar esto según tus necesidades)
            invite_code = f'inv_{member.id+random.randint(100,999)}'

            # Guarda la información del canal temporal
            temp_channels_info[temp_channel.id] = {'invite_code': invite_code, 'members': {member.id}}

            # Envía el código de invitación por mensaje privado al usuario
            await member.send(
                f'¡Has creado y te has unido al canal temporal privado!\n'
                f'Usa el código de invitación `{invite_code}` para que otros se unan.'
            )

            await member.send(
                f'{invite_code}'
            )

    elif before.channel and before.channel.id in temp_channels_info:
        # Verifica si el canal temporal está vacío después de que un usuario se desconecta
        temp_info = temp_channels_info[before.channel.id]
        temp_info['members'].discard(member.id)  # Elimina al usuario del conjunto de miembros

        if not temp_info['members']:
            # Borra el canal temporal si está vacío
            await before.channel.delete()
            print(f'Canal {before.channel.name} eliminado ya que no hay usuarios conectados.')
            del temp_channels_info[before.channel.id]

@client.event
async def on_message(message):
    # Verifica si el mensaje es enviado en un canal específico y contiene un código de invitación
    if message.channel.id == 1202758723924140034:  # Reemplaza con el ID de tu canal permitido
        code = message.content.strip()  # Obtén el código del mensaje

        # Verifica si el código de invitación existe en la información de canales temporales
        for channel_id, temp_info in temp_channels_info.items():
            if code == temp_info['invite_code']:
                # Obtiene al miembro del usuario que envió el mensaje
                member = message.guild.get_member(message.author.id)

                # Añade al usuario al conjunto de miembros del canal temporal
                temp_info['members'].add(member.id)

                # Borra el mensaje de invitación del chat
                await message.delete()

                # Obtiene el canal temporal
                temp_channel = client.get_channel(channel_id)

                # Da permisos al usuario para ver y hablar en el canal temporal
                await temp_channel.set_permissions(member, connect=True, view_channel=True, speak=True)

                break

    await client.process_commands(message)


# Inicia el bot con el token
client.run('Your-token')  # Reemplaza con tu token
