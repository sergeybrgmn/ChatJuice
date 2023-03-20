"""The message grouping logic"""

import os
#from xmlrpc.client import boolean
from topic_naming import translate_toEn_curie
from typing import List, Tuple


new_group_phrases = ["коллеги", "привет", "друзья", "ребят", "дорогие",
                    "гайз", "мужики", "всем привет", "парни", "hello", "guys",
                    "добрый день", "информация", "всем", "a посоветуйте",
                    "а кстати", "есть у кого", "кто хочет", "знатоки"]


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

    # Iterate messages to add a group_id to each according to the logic
    for i,msg in enumerate(messages[1:]):
        if msg['reply_to_msg_id'] is not None:
            try:
                linked_msg = next(item for item in messages[:(i+1)] if item["id"] == msg['reply_to_msg_id'])
            except StopIteration:
                linked_msg = prev_msg
                pass
            msg['group_id'] = int(linked_msg['group_id'])
            prev_msg = msg
        elif any([msg['text'].lower().startswith(phrase) for phrase in new_group_phrases]) and (len(msg['text'])>50):
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

#Below the methods 

def trans_En(msgs: List) -> List:
    """Translation function
    The idea was to translate the text before send it to the OpenAI API"""
    en_msgs = []
    for msg in msgs:
        model_out = translate_toEn_curie(msg['text'])
        msg['text'] = model_out["choices"][0]["text"]
        en_msgs.append(msg)
    return en_msgs