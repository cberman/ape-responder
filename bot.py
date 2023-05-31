import discord
import asyncio
import config

intents = discord.Intents.default()  # Create a new Intents object with all flags enabled
intents.typing = False  # We don't need the typing intent, so we disable it
intents.presences = False  # We don't need the presences intent, so we disable it

client = discord.Client(intents=intents)

@client.event
async def on_message(message):
    # We don't want the bot to respond to itself or another bot
    if message.author == client.user or message.author.bot:
        return

    # Add a check to see if the message is in the desired channel
    desired_channel = client.get_channel(1113303109754687608)
    if message.channel != desired_channel:
        return

    # If the message mentions a specific user
    if message.mentions:
        # Wait for N minutes
        await asyncio.sleep(config.SECONDS_TO_WAIT)

        # Check the channel for a message from the mentioned user in the meantime
        history = []
        async for message in message.channel.history(after=message):
            history.append(message)
        for member in message.mentions:
            if not any(m.author == member for m in history):
                # The mentioned user did not respond in the meantime, so we reply
                await message.channel.send(f"{member}: Sorry, I was away. How can I assist you?")

client.run(config.TOKEN)
