import discord, asyncio
import config, ai_utils
import json
from langchain.llms import OpenAI
import concurrent.futures
from collections import defaultdict

openai = OpenAI(
    model_name=config.OPENAI_MODEL_NAME,
    openai_api_key=config.OPENAI_API_KEY,
)

def get_ai_response(f, kwargs):
    raw_ai_response = f(openai, **kwargs)
    try:
        parsed_ai_response = json.loads(raw_ai_response)
        print(json.dumps(parsed_ai_response, indent=2))
        return parsed_ai_response.get('response', 'no response')
    except Exception as e:
        print(str(e))
        print(raw_ai_response)
        return 'error'

intents = discord.Intents.default()  # Create a new Intents object with all flags enabled
intents.typing = False  # We don't need the typing intent, so we disable it
intents.presences = False  # We don't need the presences intent, so we disable it
intents.message_content = True  # needed to view the content of messages

client = discord.Client(intents=intents)

user_history = defaultdict(list)
def load_message(message):
    global user_history
    if message.author.name in config.VERIFIED_USERS:
        user_history[message.author].append(message.content)
        return True
    return False

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    for channel_name, channel_num in {
            'main': config.MAIN_TEXT_CHANNEL,
            'ape': config.APE_CHANNEL
            }.items():
        loaded = 0
        channel = client.get_channel(channel_num)
        async for message in channel.history(limit=config.HISTORY_LIMIT):
            if load_message(message):
                loaded += 1
        print(f'Loaded {loaded} chats from the {channel_name} channel')

@client.event
async def on_message(message):
    global user_history
    await message.guild.me.edit(nick='ape responder')
    # We don't want the bot to respond to itself or another bot
    if message.author == client.user or message.author.bot:
        return

    # Add a check to see if the message is in the desired channel
    desired_channel = client.get_channel(config.APE_CHANNEL)   # ape-responder
    if message.channel != desired_channel:
        return

    # If the message mentions a specific user
    if not message.mentions:
        return

    # Wait for N seconds
    await asyncio.sleep(config.SECONDS_TO_WAIT)

    # Check the channel for a message from the mentioned user in the meantime
    latest_history = []
    async for history_message in message.channel.history(after=message):
        latest_history.append(history_message)
        load_message(history_message)

    for pingee in message.mentions:
        if pingee == client.user:
            # ape was pinged directly
            print(message.content)
            print('responding as Gorilla')
            history_string = str()
            if message.author.name in config.VERIFIED_USERS:
                author_history = user_history[message.author]
                history_string = '\n'.join(author_history)
            loop = asyncio.get_event_loop()  # Get the current event loop
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Run the get_ape_response function in the executor
                future = loop.run_in_executor(executor, get_ai_response, ai_utils.get_ape_response, {'ping':message.content, 'sample_chats':history_string})

                ape_response = await future  # This will complete once get_ape_response has completed
            await message.reply(ape_response)

        elif pingee.name not in config.VERIFIED_USERS:
            # make sure the user agrees to be impersonated
            continue

        elif not any(m.author == pingee for m in latest_history):
            # The mentioned user did not respond in the meantime, so we reply
            print(message.content)
            print(f'imersponating: {pingee.name}')
            pingee_history = user_history[pingee]
            history_string = '\n'.join(pingee_history)
            loop = asyncio.get_event_loop()  # Get the current event loop
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Run the get_chat_response function in the executor
                future = loop.run_in_executor(executor, get_ai_response, ai_utils.get_chat_response, {'username':pingee, 'ping':message.content, 'sample_chats':history_string})
                chat_response = await future  # This will complete once get_ape_response has completed
            await message.reply(f'{pingee.name}: {chat_response}')


client.run(config.DISCORD_TOKEN)
