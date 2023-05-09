"""Bot interface to use ChatSqueez for Telegram"""

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from datetime import datetime, date

import os
# No need when importing env-file while running the docker container 
# Uncomment if debugging on a local machine and using .env file
from dotenv import load_dotenv 
import connect
import topic_naming
import dataflow

#  No need when importing env-file while running the docker container 
load_dotenv()

bot = Bot(token=os.environ.get('JUICE_BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
#form_router = Router()


# States to make the login flow
class UserForm(StatesGroup):
    phone = State() 
    code = State() 
    password = State()

# Greetings from bot
@dp.message_handler(commands=['start', 'help'])
async def send_welcome(msg: types.Message):
    """Bot sends greeting and help info"""
    name = msg.from_user.username

    await msg.answer(
        f"Hi {name}, "
        "ChatJuice bot can name the Topics which were discussed in the group chats, \n\n"
        "To use it you need to login to your telegram account: /login\n")
 
@dp.message_handler(commands='peer')
async def site_msg(msg: types.Message):
    """display the list of private chats"""
    chat_list = await connect.get_priv_chats(msg.from_user.id)
    keyboard = InlineKeyboardMarkup()
    for chat in chat_list:
        btn = InlineKeyboardButton(chat[0], callback_data=f"{str(chat[1])}")
        keyboard.add(btn)
    await bot.send_message(chat_id=msg.chat.id, text='Peers 1-on-1 chats', reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith("day"))
async def process_callback_chat(callback_query: types.CallbackQuery):
    """Handle the chosen chat to show the topics. Callback for the 'day' command"""
    # Parse callback_data    
    _, user_id, chat_id, callback_chat_id = callback_query.data.split(',')
    # Get chat info 
    title = await connect.get_chat_info(int(user_id), int(chat_id))
    # Answer wich chat has been chosen
    await bot.answer_callback_query(callback_query.id, text=f"Selected chat:{title}")

    #Get the topics of the day messages 
    day = datetime.combine(date.today(), datetime.min.time())
    print(chat_id)
    topic_list, links = await connect.get_chat_topics(int(user_id), day, int(chat_id))

    link_list = []
    for topic, link in zip(topic_list,links):
        #link_text = md.link(topic_name,link)
        link_text = f"<a href='{link}'> - {topic}\n</a>"
        link_list.append(link_text)

    message_text = "\n".join(link_list)
    await bot.send_message(chat_id=callback_chat_id, 
                            text=f"Last topics from {title}:\n\n {message_text}", 
                            parse_mode='HTML')
    
    # An option to show as buttons. The drawback - text is cut
    """
    keyboard = InlineKeyboardMarkup()
    for topic_full in topic_list:
        topic_name = topic_full["choices"][0]["text"]
        btn = InlineKeyboardButton(topic_name, callback_data=f"topic_start_message")
        keyboard.add(btn) 
    await bot.send_message(chat_id=callback_chat_id, text=f'Last topics from {title}', reply_markup=keyboard)
    """
    #await bot.send_message(chat_id=callback_chat_id, text=f"Last topics from {title}:\n\n {topic_list}")


@dp.callback_query_handler(lambda c: c.data.startswith("chat"))
async def process_callback_chat(callback_query: types.CallbackQuery):
    """handle the chosen chat to show the topics"""
    #parse callback_data    
    _, chat_id, callback_chat_id = callback_query.data.split(',')
    
    title = await connect.get_chat_info(int(chat_id))
    await bot.answer_callback_query(callback_query.id, text=f"Selected super chat:{title}")

    chat = await connect.get_chat_data(int(chat_id))

    print(chat)
    await bot.send_message(chat_id=int(callback_chat_id), text=f"Chat info:\n\n {chat.title}")

@dp.callback_query_handler(lambda c: c.data.startswith("miss"))
async def process_callback_chat(callback_query: types.CallbackQuery):
    """handle the chosen chat to show the topics. Called for unread messages"""
    #parse callback_data    
    _, user_id, chat_id, callback_chat_id, unread_count = callback_query.data.split(',')
    title = await connect.get_chat_info(int(user_id), int(chat_id))
    await bot.answer_callback_query(callback_query.id, text=f"Selected chat:{title}")

    #Get the topics of the missed messages 
    topic_list, links = await connect.get_chat_missed_topics(int(user_id), int(chat_id), int(unread_count))

    #Build a list of Topics-links to the original messages
    link_list = []
    for topic, link in zip(topic_list,links):
        #link_text = md.link(topic_name,link)
        link_text = f"<a href='{link}'> - {topic}\n</a>"
        link_list.append(link_text)

    message_text = "\n".join(link_list)
    await bot.send_message(chat_id=callback_chat_id, 
                            text=f"Last topics from {title}:\n\n {message_text}", 
                            parse_mode='HTML')

@dp.message_handler(commands='day')
async def site_msg(msg: types.Message):
    """display the list of group chats"""
    day = datetime.combine(date.today(), datetime.min.time())
    chats_limit = 50
    if not await connect.user_is_authorized(msg.from_user.id):
        await msg.answer("Please login to your Telegram account befor using ChatJuice. \n Use /login command")
    else:
        # Call the method to obtain a list of latest chats  (with a 'chats_limit' limit)
        chat_list = await connect.get_chats(msg.from_user.id, chats_limit)
    
        keyboard = InlineKeyboardMarkup()
        for chat in chat_list:
            chat_title, chat_id, unread_count = chat
            btn = InlineKeyboardButton(chat_title, 
                            callback_data=f"day,"
                                          f"{str(msg.from_user.id)}," 
                                          f"{str(chat_id)},"
                                          f"{str(msg.chat.id)}"
                                          )
            keyboard.add(btn)
        await bot.send_message(chat_id=msg.chat.id, text=f'The top active channels from today', reply_markup=keyboard)


@dp.message_handler(commands='miss')
async def site_msg(msg: types.Message):
    """display the list of chats w missed messages"""
    # Call the method to obtain a list of chats with missed messages (with a 'chats_limit' limit)
    chats_limit = 50
    if not await connect.user_is_authorized(msg.from_user.id):
        await msg.answer("Please login to your Telegram account befor using ChatJuice. \n Use /login command")
    else:
        chat_list = await connect.get_missed(msg.from_user.id, chats_limit)   
        keyboard = InlineKeyboardMarkup()
        for chat in chat_list:
            chat_title, chat_id, unread_count = chat
            btn = InlineKeyboardButton(chat_title+", "+str(unread_count), 
                        callback_data=f"miss,"
                                      f"{str(msg.from_user.id)},"  
                                      f"{str(chat_id)},"
                                      f"{str(msg.chat.id)},"
                                      f"{str(unread_count)}"
                                      )
            keyboard.add(btn)
        await bot.send_message(chat_id=msg.chat.id, text=f'The channels with missed messages (Title, missed amount)', reply_markup=keyboard)


@dp.message_handler(commands='gr')
async def site_msg(msg: types.Message):
    """test grouping. Used for test"""
    if not await connect.user_is_authorized(msg.from_user.id):
        await msg.answer("Please login to your Telegram account befor using ChatJuice. \n Use /login command")
    else:
        #Get the groups of the day messages 
        day = datetime.combine(date.today(), datetime.min.time())
        file1 = open("debug_groups.txt", "w")
        #Men pohod
        #chat_id = 1608315521
        #Mindcraft_men
        #chat_id = 1479003314
        #RU IT in TLV talks
        #chat_id = 1636401531
        #Relocation Israel
        #chat_id = 1779908622
        #BCG_alumni
        chat_id = 1200358594

        groups, links = await connect.get_chat_topics(msg.from_user.id, day, chat_id)
        for i, group in enumerate(groups):
            file1.write(f"Group #{i} \n ")
            file1.write(group + "\n")
        file1.close()
    
        for group in groups:
            topic = topic_naming.get_chat_topic(group,'gpt3.5',useEng=False)
            print(topic)

        await msg.answer(f"The file is recorded. The test topic are defined")


    
# Temporary command to restore the client
@dp.message_handler(commands='client')
async def start_command(msg: types.Message):
        """
        Handle the client command
        """
        name = msg.from_user.username
        client = await connect.get_client(msg.from_user.id)
        print("client restored:", client)
        await msg.answer(f"Client for {name} is restored.")

@dp.message_handler(commands='logout')
async def site_msg(msg: types.Message, ):
    """Logout from the TG account"""
    out = await connect.logout()
    if out:
        await msg.answer("Successfully logged out") 
    else:
        await msg.answer("Problem accured when logging out")


@dp.message_handler(commands='login')
async def start_command(msg: types.Message, state: FSMContext):
        """
        Handle the login command
        """
        await msg.answer("Welcome! Let's start the login flow.")
        await UserForm.phone.set()
        await msg.answer("Enter your phone:")

@dp.message_handler(state=UserForm.phone)
async def process_phone(msg: types.Message, state: FSMContext):
        """
        Handle the phone step of the form flow
        """
        phone = msg.text
        user_id = dataflow.check_user(msg.from_user.id)

        dataflow.add_user_data(msg.from_user.id, ("phone",phone))

        await state.update_data(phone=phone)
        hash = await connect.login(phone,msg.from_user.id)

        # Update hash in the DB
        dataflow.add_user_data(msg.from_user.id, ("login_hash", hash))

        await state.set_state(UserForm.code)
        await msg.answer("Enter login code (use underscore(_) after first two digits):")

@dp.message_handler(state=UserForm.code)
async def process_code(msg: types.Message, state: FSMContext):
        """
        Handle the code step of the form flow
        """
        code = int(msg.text[:2]+msg.text[2:])
        await state.update_data(code=code)
        
        phone = dataflow.get_user_data(msg.from_user.id, "phone")
        hash = dataflow.get_user_data(msg.from_user.id, "login_hash")

        out = await connect.input_code(msg.from_user.id, phone, code, hash)
        if out == "2FA":
            await state.set_state(UserForm.password)
            await msg.answer("You are using 2FA for Telegram login. Enter password:") 
        else:
            await msg.answer(f"Great. Now you can squeeze the juice! Start with /miss command to catch up!") 
            await state.finish()

@dp.message_handler(state=UserForm.password)
async def process_code(msg: types.Message, state: FSMContext):
        """
        Handle the PASSWORD step of the form flow if 2FA enabled
        """
        password = msg.text
        await state.update_data(password=password)
        out = await connect.input_password(msg.from_user.id, password)
        await msg.answer(f"Great. Now you can squeeze the juice! Start with /miss command to catch up!") 
        await state.finish()         

if __name__ == '__main__':
   executor.start_polling(dispatcher=dp, timeout=20000)