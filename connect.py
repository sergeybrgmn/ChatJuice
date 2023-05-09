"""Connect to telegram via MTProto using telethone
Working with data on the telegram side"""

import datetime
from logging import NullHandler
from sqlite3 import connect
from tokenize import String
from typing import List, Tuple
from telethon import TelegramClient, errors
import pytz
import topic_naming
import topic_group

import os
# No need when importing env-file while running the docker container 
from dotenv import load_dotenv
load_dotenv()

utc=pytz.UTC


API_ID = os.getenv('TG_API_ID')
API_HASH = os.getenv('TG_API_HASH')

#The class to keep user_id (external from messanger) with client objects of the connection
class UserClients:
    def __init__(self):
        self.data = {}
    
    def get_client(self,user_id):
        return self.data.setdefault(user_id, TelegramClient(f'session_{user_id}', API_ID, API_HASH))
    
    def __repr__(self):
        return f'UserClient({self.data})'

user_clients = UserClients()


#async def check_connect(ext_user_id):
"""The function to check if the user has logged in"""
 #   client = user_clients.get_client(ext_user_id)


async def get_client(user_id):
    """create TelegramClient object and return it. Name is used for keeping the session file"""
    client = user_clients.get_client(user_id)
    return client

async def login(phone,user_id):
    """First login step: sending a code request"""
    client = user_clients.get_client(user_id)
    try:
        await client.connect()
    except OSError:
        print('Failed to connect')
    sentcode = await client.send_code_request(phone, force_sms=False)
    #sentcode = await client.sign_in(phone)
    return sentcode.phone_code_hash

async def input_code(user_id,phone,code,hash):
    """Second login step: check 2FA or signin with code """
    client = user_clients.get_client(user_id)
    try:
        await client.connect()
    except OSError:
        print('Failed to connect')
    try:
        me = await client.sign_in(phone, code, phone_code_hash=hash)
    except errors.SessionPasswordNeededError:
        me = "2FA"
        #res = await client.sign_in(phone, code, phone_code_hash=hash)
    return me

async def input_password(user_id,password):
    """Third login step: input password"""
    client = user_clients.get_client(user_id)
    try:
        await client.connect()
    except OSError:
        print('Failed to connect')
    me = await client.sign_in(password=password)
    return me

async def logout(user_id):
    """Logout from the client"""
    client = user_clients.get_client(user_id)
    try:
        await client.connect()
    except OSError:
        print('Failed to connect')
    out = await client.log_out()
    return out

async def get_chat_data(ext_user_id: int, chat_id: int):

    """Temporary method"""

    client = user_clients.get_client(ext_user_id)
    try:
        await client.connect()
    except OSError:
        print('Failed to connect')
    # Get the full chat information using the get_entity method
    # chats.append((dialog.name, dialog.is_user, dialog.is_group, dialog.is_channel, dialog.entity.id)) 
    full_chat = await client.get_entity(chat_id)
    return full_chat

async def get_priv_chats(ext_user_id: int) -> List:
    """Get the list of peer chats among the dialogs"""
    client = user_clients.get_client(ext_user_id)
    chats = []
    try:
        await client.connect()
    except OSError:
        print('Failed to connect')
    async for dialog in client.iter_dialogs():
        if dialog.is_user == True:
            chats.append((dialog.name, dialog.entity.id)) 
    return chats


async def get_chat_missed_messages(client: TelegramClient, chat_id: int, missed: int) -> Tuple:
    """The function to iterate over messages in the selected chat
    The limit of iteration by the number of missed messages

    output: a Tuple of lists: 1. message ids and 2. the message text
    """
    chat = await client.get_entity(chat_id)
            
    # Create a list to store the messages
    msgs=[]
    msgs_ids = []

    async for msg in client.iter_messages(chat, limit = missed):
        # Create a dictionary to store the message data
        msg_data={
            'id': msg.id,
            'text': msg.message,
            'reply_to_msg_id': msg.reply_to_msg_id
            }
        if isinstance(msg_data['text'], str):
            msgs_ids.append(msg.id)            
            msgs.append(msg_data)
            
    return (msgs, msgs_ids)


async def get_chat_date_messages(client: TelegramClient, chat_id: int, date: datetime) -> Tuple:
    """The function to iterate over messages in the selected chat for the date specified
    The limit of iteration by the date

    output: a Tuple of lists: 1. message ids and 2. the message text
    """
    chat = await client.get_entity(chat_id)
    tomorrow = date + datetime.timedelta(days=1)
    lowdate = date.replace(tzinfo=utc)
            
    # Create a list to store the messages
    msgs=[]
    msgs_ids = []

    async for msg in client.iter_messages(chat, offset_date=tomorrow):
        mdate = msg.date.replace(tzinfo=utc)
        if mdate <= lowdate:
            return (msgs, msgs_ids)
                
        # Create a dictionary to store the message data
        msg_data={
            'id': msg.id,
            'text': msg.message,
            'reply_to_msg_id': msg.reply_to_msg_id
        }
        if isinstance(msg_data['text'], str):
            msgs_ids.append(msg.id)            
            msgs.append(msg_data)

async def get_replied_messages(client: TelegramClient, chat_id: int, msgs: List, msg_ids: List) -> List:
    """The function to search messages related to the target list (to which the user replied to)

    output: a list of unique messages
    """
    # Get the chat entity 
    chat = await client.get_entity(chat_id)         
        
    # Empty list to get the source messages - the one's to which people replied
    source_msgs_ids = []
    # Get msgs (ids) to which there were replies in the target date. Exclude ids which are already in the target date.
    for msg_data in msgs:
        if (msg_data['reply_to_msg_id'] is not None) and (msg_data['reply_to_msg_id'] not in msg_ids):
            source_msgs_ids.append(msg_data['reply_to_msg_id'])
        
    uniq_source_msgs_ids = [*set(source_msgs_ids)]

    # An list for replies
    replies = []

    # clear the list to use it again.
    source_msgs_ids.clear()

    #Dig the chat history while there is smth to dig (=there are replies)
    while len(uniq_source_msgs_ids) > 0:
        for id in uniq_source_msgs_ids:
            msg = await client.get_messages(chat, ids=id)
            #print(type(msg.message))
            msg_data = {
            'id': msg.id,
            'text': msg.message,
            'reply_to_msg_id': msg.reply_to_msg_id
            } 
            if msg.reply_to_msg_id is not None:
                source_msgs_ids.append(msg_data['reply_to_msg_id'])
            if isinstance(msg_data['text'], str):
                replies.append(msg_data)

        uniq_source_msgs_ids = [*set(source_msgs_ids)]
        source_msgs_ids.clear()

    return replies


async def get_chat_info(ext_user_id: int, chat_id: int) -> str:
    """Need this method to get the name of the chat"""
    client = user_clients.get_client(ext_user_id)
    try:
        await client.connect()
    except OSError:
        print('Failed to connect')
    # Get the full chat information using the get_entity method
    full_chat = await client.get_entity(chat_id)
    return full_chat.title

async def get_chat_missed_topics(ext_user_id: int, chat_id: int, missed: int) -> Tuple:
    """Get the topics of the missed messages"""
    client = user_clients.get_client(ext_user_id)
    #Get all the missed msgs from a specific at the Chat + the ids of the messages to search the replies
    miss_msgs, miss_msgs_ids = await get_chat_missed_messages(client, chat_id, missed)

    repl = await get_replied_messages(client, chat_id, miss_msgs, miss_msgs_ids)

    # Add replied messages to the messages of the day
    miss_msgs.extend(repl)

    print("Number of messages:", len(miss_msgs))

    # Sort from the earliest to the last one
    miss_msgs_sorted = sorted(miss_msgs, key=lambda d: d['id'])

    # Group messages
    groups,links = topic_group.group_messages(chat_id, miss_msgs_sorted,useEng=False)

    print("The number of topics:", len(groups))

    # Find out what a topic is using OpenAI API 
    topics = []
    for group in groups:
        topic = topic_naming.get_chat_topic(input_text=group, method="gpt3.5", useEng=False)
        topics.append(topic)   
    return topics, links

async def get_chat_topics(ext_user_id: int, date: datetime, chat_id: int) -> Tuple:
    """Get the topics of the messages for date specified"""

    #print("Method 'get_chat_topics' is in DEBUG_MODE!!! Returns groups")
    
    client = user_clients.get_client(ext_user_id)

    #Get all the msgs from a specific at the Chat + the ids of the messages to search the replies
    date_msgs, date_msgs_ids = await get_chat_date_messages(client, chat_id, date)

    repl = await get_replied_messages(client, chat_id,date_msgs,date_msgs_ids)

    # Add replied messages to the messages of the day
    date_msgs.extend(repl)

    # Sort from the earliest to the last one
    date_msgs_sorted = sorted(date_msgs, key=lambda d: d['id'])


    # Group messages
    groups,links = topic_group.group_messages(chat_id, date_msgs_sorted,useEng=False)

    print("The number of topics:", len(groups))

    #To debug grouping into threads
    #return groups, links

    # Find out what a topic is using OpenAI API 
    
    topics = []
    for group in groups:
        #topic = topic_naming.get_topic(input_text=group, method='curie', useEng=False)
        topic = topic_naming.get_chat_topic(input_text=group, method="gpt3.5", useEng=False)
        topics.append(topic)   
    return topics, links
    
    
async def get_chats(ext_user_id: int,feedlen=50) -> List:
    """Get the list of peer chats among last N dialogs"""
    client = user_clients.get_client(ext_user_id)
    chats = []
    try:
        await client.connect()
    except OSError:
        print('Failed to connect')
    async for dialog in client.iter_dialogs(limit=feedlen):
        if dialog.is_channel == True:
            chats.append((dialog.name, dialog.entity.id, dialog.unread_count)) 
    return chats

async def get_missed(ext_user_id: int, feedlen=50) -> List:
    """Get the list of peer chats with missed messages"""
    client = user_clients.get_client(ext_user_id)
    try:
        await client.connect()
    except OSError:
        print('Failed to connect')
    chats = [(
            d.name, 
            d.entity.id, 
            d.unread_count
            ) async for d in client.iter_dialogs(limit=feedlen) if (d.is_channel == True and d.unread_count != 0)]
    return chats

async def user_is_authorized(ext_user_id: int):
    """Check if the user is authorized (has before passed the login flow)"""
    client = user_clients.get_client(ext_user_id)
    try:
        await client.connect()
    except OSError:
        print('Failed to connect')
    if await client.is_user_authorized():
        return True
    else:
        return False

def check_users_exist():
    """Init User client class"""
    try:
        user_clients
    except NameError:
        user_clients = UserClients()

check_users_exist()