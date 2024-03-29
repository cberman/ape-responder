import discord, asyncio
import config, ai_utils
import json, re
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
        for i in range(3):
            print()
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
ape_history = defaultdict(list)
def load_message(message):
    global user_history, ape_history, client
    if len(message.content) > 1000:
        return False
    if message.author.name in config.VERIFIED_USERS:
        user_history[message.author].append(message.content)
        return True
    elif message.author == client.user:
        if ':' in message.content[:32]:
            obo = message.content.split(':')[0]
            ape_history[obo].append(message.content)
        else:
            ape_history[client.user.name].append(message.content)
    return False

def reset_history():
    global user_history, ape_history
    user_history = defaultdict(list)
    ape_history = defaultdict(list)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    reset_history()
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
    for user in user_history:
        print(f'{user}\n {user_history[user]}')

_ping_re = re.compile(r'@[a-zA-Z][-_0-9a-zA-Z]*')
@client.event
async def on_message(message):
    global user_history, _ping_re
    # await message.guild.me.edit(nick='ape responder')
    # We don't want the bot to respond to itself or another bot
    if message.author == client.user or message.author.bot:
        return

    # Add a check to see if the message is in the desired channel
    desired_channel = client.get_channel(config.APE_CHANNEL)   # ape-responder
    if message.channel != desired_channel:
        return

    celebs = _ping_re.findall(message.content)
    if celebs:
        # someone besides a discord user was pinged
        print(message.content)
        for celeb in celebs:
            print(f'imersponating: {celeb}')
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # get the llm response in a thread
                future = loop.run_in_executor(executor, get_ai_response, ai_utils.get_celeb_response, {'celebrity':celeb, 'ping':message.content})
                chat_response = await future
            await message.reply(f'{celeb}: {chat_response}')

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
            history_string = 'Gorilla\'s chat history:\n'
            # ape_self_history = ape_history[client.user.name]
            history_string += json.dumps(ape_history, indent=2)
            if message.author.name in config.VERIFIED_USERS:
                history_string += '\nUser\'s chat history:\n'
                author_history = user_history[message.author]
                history_string += '\n'.join(author_history)
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # get the llm response in a thread
                future = loop.run_in_executor(executor, get_ai_response, ai_utils.get_ape_response, {'ping':message.content, 'sample_chats':history_string})

                try:
                    ape_response = await future
                except openai.error.InvalidRequestError:
                    ape_response = 'uh oh, ape forget. try ask again.'
                    await on_read()

            await message.reply(ape_response)

        elif pingee.name not in config.VERIFIED_USERS:
            print(f'***skipping user "{pingee.name}" due to missing verification***')
            # make sure the user agrees to be impersonated
            continue

        elif not any(m.author == pingee for m in latest_history):
            # The mentioned user did not respond in the meantime, so we reply
            print(message.content)
            print(f'imersponating: {pingee.name}')
            pingee_history = user_history[pingee]
            history_string = '\n'.join(pingee_history)
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # get the llm response in a thread
                future = loop.run_in_executor(executor, get_ai_response, ai_utils.get_chat_response, {'username':pingee, 'ping':message.content, 'sample_chats':history_string})
                chat_response = await future
            await message.reply(f'{pingee.name}: {chat_response}')


client.run(config.DISCORD_TOKEN)
