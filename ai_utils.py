from langchain import PromptTemplate
import json

response_template_starter = """{
    "reasoning": "Let's think like a gorilla. """

def build_prompt_template(context, inputs, output_field, output_desc, ex_reason='...', ex_output='...'):
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
{{
    "reasoning": "Let's think like a gorilla. {ex_reason}",
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
    template_skeleton += """Answer:
```
""" 
    template_skeleton += response_template_starter
    return PromptTemplate(
            input_variables=list(inputs.keys()),
            template=template_skeleton,
            template_format='jinja2'
            )

ape_context = 'We have a discord full of individuals with below average intelligence. They often neglect to respond to pings in a timely manner. They have a helpful gorilla assistant who can make a best effort to respond for users when they miss a ping. The gorilla is also busy so responses are fraught with inaccuracies and errors, on top of the already uninteligble gorilla noises. Despite all that, the gorilla tries to answer in the style of the user.'
chat_inputs = {'ping': 'the ping that the user missed',
               'sample_chats': 'a list of previous chats by the user. they probably do not provide anything relevant to the ping. but they are useful for emulating the style of the user.',
               # 'sample_pings': 'a list of previous responses by the user after they are pinged',
    }
chat_output_field = 'response'
ape_output_desc = 'the gorilla assistant\'s response. make sure to include a response of some sort, even if the gorilla has nothing to say.'
ape_template = build_prompt_template(ape_context, chat_inputs, chat_output_field, ape_output_desc)

def get_ape_response(openai, ping, sample_chats, sample_pings=''):
    json_str_response = response_template_starter + openai(
            ape_template.format(
                    ping=ping,
                    sample_chats=sample_chats
                    #sample_pings=sample_pings
                ))
    try:
        end_i = json_str_response.index('}')
        return json_str_response[:end_i+1]
    except:
        return json_str_response
