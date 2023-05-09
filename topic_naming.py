"""The topic naming logic (text complition using OpenAI API)"""

from email import message
from urllib import response
from xml.parsers.expat import model
import openai
import os
# No need when importing env-file while running the docker container 
from dotenv import load_dotenv 
load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

# A task as input prompt to the OpenAI model
topic_task = "Name in English in maximum 6 words the topic for this series of chat messages:\n\n"
openai_text_models = {
                'davinci': {'model': 'text-davinci-003', 'token_limit': 3700},
                'curie': {'model': 'text-curie-001', 'token_limit': 1600},
                'gpt3.5': {'model': 'gpt-3.5-turbo', 'token_limit': 1000}
                } 

model_basic_settings = {
            'temperature':0.7,
            'max_tokens':64,
            'top_p':1.0,
            'frequency_penalty':0.0,
            'presence_penalty':0.0
            }


def get_chat_topic(input_text: str, method='gpt3.5', useEng=False):
    """The method to get the topic for the input text. 
    Use ChatGPT models
    Sending request to OpenAI API"""
    msg = topic_task + input_text
    symbol_limit = openai_text_models[method]['token_limit']
    if not useEng:
        msg_content = (msg[:symbol_limit] + '..') if len(msg) > symbol_limit else msg
    else:
        msg_content = msg
    # Request to OpenAI API
    response = openai.ChatCompletion.create(
        model=openai_text_models[method]['model'],
        messages=[
            {"role": "system", "content": "You are an assistant that helps understand the topic of the discussion."},
            {"role": "user", "content": msg_content}
        ],
        temperature=model_basic_settings['temperature']
        )
    topic = response["choices"][0]["message"]["content"]
    return topic


# The method to get the topic for the input text
def get_topic(input_text: str, method='curie', useEng=False):
    """The method to get the topic for the input text. 
    Sending request to OpenAI API, 
    using corresponding model to derive the topic"""
    input_prompt = topic_task + input_text
    symbol_limit = openai_text_models[method]['token_limit']
    if not useEng:
        input = (input_prompt[:symbol_limit] + '..') if len(input_prompt) > symbol_limit else input_prompt
    else:
        input = input_prompt
    # Request to OpenAI API
    response = openai.Completion.create(
        model=openai_text_models[method]['model'],
        prompt=input, 
        temperature=model_basic_settings['temperature'],
        max_tokens=model_basic_settings['max_tokens'],
        top_p=model_basic_settings['top_p'],
        frequency_penalty=model_basic_settings['frequency_penalty'],
        presence_penalty=model_basic_settings['presence_penalty']
        )
    topic = response["choices"][0]["text"]
    return topic


# The translation usage of the model
def translate_toEn_curie(input_prompt):
    """The request to OpenAI API Curie model to translate"""
    # This model's maximum context length is 2049 tokens
    input_prompt = "Translate from Russian to English this text: " + input_prompt
    input = (input_prompt[:1450] + '..') if len(input_prompt) > 1450 else input_prompt
    response = openai.Completion.create(
    model="text-curie-001",
    prompt = input, 
    temperature=0.3,
    max_tokens=300,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0
    )
    return response