from langchain import PromptTemplate
import json

response_template_starter = '''{
    "reasoning": "Let\'s think'''

def build_prompt_template(context, inputs, output_field, output_desc, think='step by step', ex_reason='...', ex_output='...'):
    template_skeleton = f"""{context}

Use the following format:
"""
    for input_name, input_desc in inputs.items():
        template_skeleton += f"""{input_name.capitalize()}:
```
{input_desc}
```
"""
    template_skeleton += f"""Answer:
```
json output with two fields: "reasoning" and "{output_field}". for example:
{response_template_starter} {think}. {ex_reason}",
    "{output_field}": "{ex_output}"
}}
here, the value for "{output_field}" should be {output_desc}"
that is all: only output the json without extra information outside the json object. make sure the json is valid, e.g., if using double quotes within a string they should be escaped.

"""
    for input_name in inputs.keys():
        template_skeleton += f"""{input_name.capitalize()}:
```
{{{{{input_name}}}}}
```
"""
    template_skeleton += f"""Answer:
```
{response_template_starter} {think}. """
    return PromptTemplate(
            input_variables=list(inputs.keys()),
            template=template_skeleton,
            template_format='jinja2'
            )

ape_context = 'We have a discord full of individuals with below average intelligence. They often neglect to respond to pings in a timely manner. They have a helpful gorilla assistant who can make a best effort to respond for users when they miss a ping. The gorilla is also busy so responses are fraught with inaccuracies and errors, on top of the already uninteligble gorilla noises. Despite all that, the gorilla tries to answer in the style of the user that it is replying for.'
chat_inputs = {'username': 'the display name of the user that missed the ping',
               'ping': 'the ping that "{username}" missed',
               'sample_chats': 'a list of previous chats by the user. they probably do not provide anything relevant to the ping. but they are useful for emulating the style of the user.',
               # 'sample_pings': 'a list of previous responses by the user after they are pinged',
    }
ape_inputs = {'ping': 'a dm from a user to the gorilla',
              'sample_chats': 'a list of previous chats by the user and the gorilla. they be relevant to the ping, but most are not.',
    }
chat_output_field = 'response'
ape_output_desc = 'the gorilla assistant\'s response to the user\'s ping. make sure to include a response of some sort, even if the gorilla has nothing to say. please answer as though you were a gorilla who was semi-capable of speaking english and was also famished for bananas at the time of responding.'
chat_output_desc = 'the gorilla assistant\'s response, for what it thinks the user would say to the ping. make sure to include a response of some sort, even if the gorilla has nothing to say. remember, you are trying to answer in the style of the user.'
ape_think = 'like a gorilla'
chat_think = 'like {username}'
ape_template = build_prompt_template(ape_context, ape_inputs, chat_output_field, ape_output_desc, think=ape_think)
chat_template = build_prompt_template(ape_context, chat_inputs, chat_output_field, chat_output_desc, think=chat_think)

def heal_response(raw_response, prefix=response_template_starter):
    try:
        # truncate after first }
        end_i = raw_response.index('}')
        raw_response = raw_response[:end_i+1]
    except:
        pass
    if raw_response[0] not in '{":':
        return prefix + raw_response
    elif raw_response[0] == '{':
        return raw_response
    elif raw_response[0] == ':':
        return prefix[
                :prefix.index(':')] + raw_response
    elif raw_response[0] == '"':
        for i, c in enumerate(prefix):
            if c == '"':
                test_case = prefix[:i] + raw_response
                test_case = test_function(raw_response)
                try:
                    test = json.loads(test_case)
                    return test_case
                except json.decoder.JSONDecodeError:
                    pass
    return raw_response

def get_ape_response(openai, ping, sample_chats):
    raw_response = openai(
            ape_template.format(
                    ping=ping,
                    sample_chats=sample_chats
                    #sample_pings=sample_pings
                ))
    prefix = f'{response_template_starter} {ape_think}. '
    return heal_response(raw_response, prefix)

def get_chat_response(openai, username, ping, sample_chats, sample_pings=''):
    raw_response = openai(
            chat_template.format(
                    username=username,
                    ping=ping,
                    sample_chats=sample_chats
                    #sample_pings=sample_pings
                ))
    prefix = f'{response_template_starter} the user. '
    return heal_response(raw_response, prefix)
