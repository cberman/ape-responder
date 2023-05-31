import discord
import asyncio
import config

client = discord.Client()

@client.event
async def on_message(message):
    # We don't want the bot to respond to itself or another bot
    if message.author == client.user or message.author.bot:
        return

    # If the message mentions a specific user
    if client.user in message.mentions:
        # Wait for N minutes
        await asyncio.sleep(config.SECONDS_TO_WAIT)

        # Check the channel for a message from the mentioned user in the meantime
        history = await message.channel.history(after=message).flatten()
        if not any(m.author == client.user for m in history):
            # The mentioned user did not respond in the meantime, so we reply
            await message.channel.send("Sorry, I was away. How can I assist you?")

client.run(config.TOKEN)
