import discord, asyncio
import config, ai_utils
import json
from langchain.llms import OpenAI
import concurrent.futures

openai = OpenAI(
    model_name="gpt-3.5-turbo",
    openai_api_key=config.OPENAI_API_KEY,
)

def get_ai_response(f, pingee, ping, chat_history):
    raw_ai_response = f(openai, ping, chat_history, '')
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

chat_history = list()
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    main_channel = client.get_channel(config.MAIN_TEXT_CHANNEL)
    ape_channel = client.get_channel(config.APE_CHANNEL)
    async for message in main_channel.history(limit=config.HISTORY_LIMIT):
        chat_history.append(message)
    async for message in ape_channel.history(limit=config.HISTORY_LIMIT):
        chat_history.append(message)
    print(f'Loaded {config.HISTORY_LIMIT} chats from general and ape-responder each')

def get_user_history(user):
    """Retrieve the user's message history in the channel."""
    user_history = []
    for message in chat_history:
        if message.author == user:
            user_history.append(message.content)
    return user_history

@client.event
async def on_message(message):
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
    history = []
    async for history_message in message.channel.history(after=message):
        history.append(history_message)

    for pingee in message.mentions:
        if pingee == client.user:
            print(message.content)
            print('responding as Gorilla')
            user_history = get_user_history(message.author)
            history_string = '\n'.join(user_history)
            loop = asyncio.get_event_loop()  # Get the current event loop
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Run the get_ape_response function in the executor
                future = loop.run_in_executor(executor, get_ai_response, ai_utils.get_ape_response, pingee, message.content, history_string)
                ape_response = await future  # This will complete once get_ape_response has completed
            await message.reply(ape_response)

        elif pingee.display_name not in config.VERIFIED_USERS:
            # make sure the user agrees to be impersonated
            continue

        elif not any(m.author == pingee for m in history):
            # The mentioned user did not respond in the meantime, so we reply
            print(message.content)
            print(f'imersponating: {pingee.name}')
            user_history = get_user_history(pingee)
            history_string = '\n'.join(user_history)
            loop = asyncio.get_event_loop()  # Get the current event loop
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Run the get_chat_response function in the executor
                future = loop.run_in_executor(executor, get_ai_response, ai_utils.get_chat_response, pingee, message.content, history_string)
                chat_response = await future  # This will complete once get_ape_response has completed
            await message.reply(f'{pingee.display_name}: {chat_response}')


client.run(config.DISCORD_TOKEN)
