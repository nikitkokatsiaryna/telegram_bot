import telebot
from telebot import types
from collections import defaultdict
import redis
import os

from redis import StrictRedis

token = '835465948:AAFptpBY6s9gyNACHCFSn7Q-tcOnM3V3BW4'

bot = telebot.TeleBot(token)

r = StrictRedis('localhost', 6379, decode_responses=True)

START, ADD_NAME, ADD_LOCATION, ADD_PHOTO, CONFIRMATION = range(5)

keyboard_answer = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
btn_yes = types.KeyboardButton('Да')
btn_no = types.KeyboardButton('Нет')
keyboard_answer.add(btn_yes, btn_no)

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


def write_title_to_redis(message):
    user_id = message.chat.id
    location_title = message.text
    r.lpush(user_id, location_title)


def write_coords_to_redis(user_id, location):
    lat, lon = location.latitude, location.longitude
    title = r.lpop(user_id)
    full_location_data = f'{title};{lat};{lon}'
    r.lpush(user_id, full_location_data)


def delete_location(user_id):
    r.lpop(user_id)


@bot.message_handler(func=lambda x: True, commands=['start'])
def handle_confirmation(message):
    bot.send_message(message.chat.id, 'Введите команду /add для добавления локации')
    bot.send_message(message.chat.id,
                     'Введите команду /list для просмотра 10 последних локаций')
    bot.send_message(message.chat.id,
                     'Введите команду /reset для удаления всех локаций')


@bot.message_handler(func=lambda message: get_state(message) == START, commands=['add'])
def handle_name(message):
    bot.send_message(message.chat.id, 'Напишите название заведения')
    update_state(message, ADD_NAME)


@bot.message_handler(
    func=lambda message: get_state(message) == ADD_NAME)
def handle_location(message):
    if message.text in ('/add', '/list', '/reset'):
        bot.send_message(message.chat.id, 'Добавление прервано')
        update_state(message, START)
    else:
        write_title_to_redis(message)
        bot.send_message(message.chat.id, 'Отправь локацию', reply_markup=location_keyboard)
        update_state(message, ADD_LOCATION)


@bot.message_handler(func=lambda message: get_state(message) == ADD_LOCATION, content_types=['location'])
def handle_confirmation(message):
    write_coords_to_redis(message.chat.id, message.location)
    bot.send_message(message.chat.id, 'Добавить запись?', reply_markup=keyboard_answer)
    update_state(message, CONFIRMATION)


@bot.message_handler(func=lambda message: get_state(message) == CONFIRMATION)
def handle_finish(message):
    if message.text in ('/add', '/list', '/reset'):
        update_state(message, START)
        delete_location(message.chat.id)
        bot.send_message(message.chat.id, 'Добавление прервано')
    else:
        if 'да' in message.text.lower():
            bot.send_message(
                message.chat.id,
                f'Локация добавлена'
            )
            update_state(message, START)
        if 'нет' in message.text.lower():
            bot.send_message(
                message.chat.id,
                f'Локация не добавлена'
            )
            update_state(message, START)
            delete_location(message.chat.id)


@bot.message_handler(func=lambda x: True, commands=['list'])
def handle_list(message):
    if get_state(message) != START:
        update_state(message, START)
        r.lpop(message.chat.id)
    else:
        last_locations = r.lrange(message.chat.id, 0, 10)
        if not last_locations:
            bot.send_message(message.chat.id, 'Список пуст!')
        else:
            bot.send_message(message.chat.id, 'Последние локации:')
            for location in last_locations:
                if ';' in location:
                    title, lat, lon = location.split(';')
                    bot.send_message(message.chat.id, str(title))
                    bot.send_location(message.chat.id, lat, lon)
                else:
                    bot.send_message(message.chat.id, location)


@bot.message_handler(func=lambda x: True, commands=['reset'])
def handle_confirmation(message):
    r.flushdb()
    bot.send_message(message.chat.id, 'Все локации удалены')


bot.polling()
