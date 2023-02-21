"""The message grouping and topic extraction logic"""

import os
from xmlrpc.client import boolean
import openai
import secret
from typing import List, Tuple



new_group_phrases = ["коллеги", "привет", "друзья", "ребят", "дорогие",
                    "гайз", "мужики", "всем привет", "парни", "hello", "guys",
                    "добрый день", "информация", "всем", "a посоветуйте",
                    "а кстати", "есть у кого", "кто хочет", "знатоки"]
openai.api_key = secret.OPENAI_API_KEY
topic_task = "Name in English in maximum 4 words the topic for this series of chat messages:\n\n"

#test case for the grouping
test_1 = [
    {'id': 1, 'text': 'Hello, how are you?', 'reply_to_msg_id': None},
    {'id': 2, 'text': 'I am good, thanks for asking.', 'reply_to_msg_id': 1},
    {'id': 3, 'text': 'That is great to hear', 'reply_to_msg_id': None},
    {'id': 4, 'text': 'Guys, what do you think about the meeting today?', 'reply_to_msg_id': None},
    {'id': 5, 'text': 'I thought it was productive.', 'reply_to_msg_id': 4},
    {'id': 6, 'text': 'I agree.', 'reply_to_msg_id': 1}
]

def group_messages(chat_id: int, messages: List, useEng=False) -> Tuple:
    """The method to group the messages according to the logic:
    - if a special key word new_group_phrases - we consider this as a beginning of the new Topic
    - if there is a reply - we connect to the message to which as a reply
    - if the message just follow the previous without special words - we connect to the previous
    """

    links = []
    groups = []
    current_group = []
    msg_w_topics = []
    messages[0]['group_id'] = messages[0]['id']
    
    link = f"https://t.me/c/{chat_id}/{messages[0]['id']}"
    links.append(link)

    msg_w_topics = [messages[0]]
    prev_msg = messages[0]

    for i,msg in enumerate(messages[1:]):
        if msg['reply_to_msg_id'] is not None:
            try:
                linked_msg = next(item for item in messages[:(i+1)] if item["id"] == msg['reply_to_msg_id'])
            except StopIteration:
                linked_msg = prev_msg
                pass
            msg['group_id'] = int(linked_msg['group_id'])
            prev_msg = msg
        elif (any(msg['text'].lower().startswith(phrase)) and (len(msg["text"])>50) for phrase in new_group_phrases):
            msg['group_id'] = int(msg['id'])
            link = f"https://t.me/c/{chat_id}/{msg['id']}"
            links.append(link) 
            prev_msg = msg
        else:
            msg['group_id'] = prev_msg['group_id']
            prev_msg = msg
        msg_w_topics.append(msg)

    msg_w_topics_sorted_local = sorted(msg_w_topics, key=lambda d: d['group_id'])

    #translate each message to English to reduce number of tokens
    if useEng:
        msg_w_topics_sorted = trans_En(msg_w_topics_sorted_local)
        print("messages were translated to En")
    else:
        msg_w_topics_sorted = msg_w_topics_sorted_local

    msg_i = msg_w_topics_sorted[0]
    current_group = msg_i['text'] + '\n' 
    for msg in msg_w_topics_sorted[1:]:
        if msg['group_id'] != msg_i['group_id']:
            groups.append(current_group)
            current_group = ''
            current_group = msg['text'] + '\n'
        else: 
            current_group = current_group + msg['text'] + '\n'
        msg_i = msg

    # Don't forget to add the final group to the list of groups
    groups.append(current_group)
    return groups, links

#Below the methonds 

def trans_En(msgs: List) -> List:
    """Translation function
    The idea was to translate the text before send it to the OpenAI API"""
    en_msgs = []
    for msg in msgs:
        model_out = translate_toEn_curie(msg['text'])
        msg['text'] = model_out["choices"][0]["text"]
        en_msgs.append(msg)
    return en_msgs

def get_topic_openai_davinchi(input_prompt, useEng=False):
    """The request to OpenAI API Davinchi model to derive the Topic"""
    input_prompt = topic_task + input_prompt
    if not useEng:
        input = (input_prompt[:3700] + '..') if len(input_prompt) > 3700 else input_prompt
    else:
        input = input_prompt
    response = openai.Completion.create(
    model="text-davinci-003",
    prompt=input, 
    temperature=0.1,
    max_tokens=64,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0
    )
    return response

def get_topic_openai_curie(input_prompt, useEng=False):
    """The request to OpenAI API Curie model to derive the Topic"""
    # This model's maximum context length is 2049 tokens
    input_prompt = topic_task + input_prompt
    if not useEng:
        input = (input_prompt[:1600] + '..') if len(input_prompt) > 1600 else input_prompt
    else:
        input = input_prompt
    response = openai.Completion.create(
    model="text-curie-001",
    prompt = input, 
    temperature=0.1,
    max_tokens=64,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0
    )
    return response

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