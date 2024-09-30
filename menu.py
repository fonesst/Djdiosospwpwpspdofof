from telebot import types

def get_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    item1 = types.KeyboardButton('/start')
    item2 = types.KeyboardButton('/help')
    item3 = types.KeyboardButton('/info')
    item4 = types.KeyboardButton('/settings')

    markup.add(item1, item2, item3, item4)

    return markup
