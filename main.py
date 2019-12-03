import telebot
from telebot import types
from collections import defaultdict
import redis

token = '835465948:AAFptpBY6s9gyNACHCFSn7Q-tcOnM3V3BW4'

bot = telebot.TeleBot(token)
START, ADD_NAME, ADD_ADDRESS, ADD_LOCATION, CONFIRMATION = range(5)

keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
btn_yes = types.KeyboardButton('Да')
btn_no = types.KeyboardButton('Нет')
keyboard.add(btn_yes, btn_no)

location_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
location_btn = types.KeyboardButton('Указать локацию', request_location=True)
location_keyboard.add(location_btn)

USER_STATE = defaultdict(lambda: START)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Введите команду /add для добавления нового места')
    bot.send_message(message.chat.id, 'Введите команду /list для просмотра 10 последних сохранённых мест')
    bot.send_message(message.chat.id, 'Введите команду /reset для удаления всех мест')


def get_state(message):
    return USER_STATE[message.chat.id]


def update_state(message, state):
    USER_STATE[message.chat.id] = state


@bot.message_handler(func=lambda message: get_state(message) == START, commands=['add'])
def handle_name(message):
    bot.send_message(message.chat.id, 'Напишите название заведения')
    update_state(message, ADD_NAME)


@bot.message_handler(func=lambda message: get_state(message) == ADD_NAME)
def handle_address(message):
    update_restaurant(message.chat.id, 'name', message.text)
    get_restaurant(message.chat.id)
    bot.send_message(message.chat.id, 'Напишите адрес')
    update_state(message, ADD_ADDRESS)


@bot.message_handler(func=lambda message: get_state(message) == ADD_ADDRESS)
def handle_location(message):
    update_restaurant(message.chat.id, 'address', message.text)
    get_restaurant(message.chat.id)
    bot.send_message(message.chat.id, 'Укажите локацию', reply_markup=location_keyboard)
    update_state(message, ADD_LOCATION)


@bot.message_handler(func=lambda message: get_state(message) == ADD_LOCATION, content_types=['location'])
def handle_confirmation(message):
    update_restaurant(message.chat.id, 'location', message.text)
    get_location(message)
    restaurant = get_restaurant(message.chat.id)
    bot.send_message(message.chat.id, 'Создаём запись? {}'.format(restaurant), reply_markup=keyboard)
    update_state(message, CONFIRMATION)


@bot.message_handler(func=lambda message: get_state(message) == CONFIRMATION)
def handle_finish(message):
    if 'да' in message.text.lower():
        bot.send_message(message.chat.id, 'Записали! Посетим обязательно')
    update_state(message, START)


USER_RESTAURANTS = defaultdict(lambda: {})


def update_restaurant(user_id, key, value):
    USER_RESTAURANTS[user_id][key] = value


def get_restaurant(user_id):
    return USER_RESTAURANTS[user_id]


@bot.message_handler(content_types=['location'])
def get_location(message):
    return message.location


# @bot.message_handler(commands=['add'])
# def create_record(message):
#     if message.text == 'Название заведения':
#         pass
#     elif message.text == 'Адрес':
#         pass
#     elif message.text == 'Локация':
#         get_location(message)
#     elif message.text == 'Фото':
#         pass


# @bot.message_handler(commands=['list'])
# def send_message(message):
#     pass
#
#
# @bot.message_handler(commands=['reset'])
# def send_message(message):
#     pass
#

bot.polling()
