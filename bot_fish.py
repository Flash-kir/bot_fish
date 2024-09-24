import os
import requests
import redis
import json

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Updater,
    Filters,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    CallbackQueryHandler,
)
from io import BytesIO
from functools import partial
from dotenv import load_dotenv


def create_user(user):
    strapi_token = os.environ.get('STRAPI_TOKEN')
    url = 'http://localhost:1337/api/auth/local/register'
    headers = {
        'Authorization': f'bearer {strapi_token}',
    }
    print(user)
    data = {
        "data": {
            "username": user['username'],
            "email": user['email'],
        }
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def create_client(user):
    strapi_token = os.environ.get('STRAPI_TOKEN')
    url = 'http://localhost:1337/api/clients'
    headers = {
        'Authorization': f'bearer {strapi_token}',
    }
    username = user['username']
    email = user['email']
    tm_id = user['tm_id']
    data = {
        "data": {
            "username": username,
            "email": email,
            "tm_id": str(tm_id),
        }
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def get_or_create_user_cart(user_id):
    strapi_token = os.environ.get('STRAPI_TOKEN')
    url_get = f'http://localhost:1337/api/carts?filters[tm_id][$eq]={user_id}'
    print(f'Url: { url_get }')
    headers = {
        'Authorization': f'bearer {strapi_token}',
    }
    response = requests.get(url_get, headers=headers)
    print(f'User cart: {response.json()}')
    if len(response.json()['data']) == 0:
        url_post = 'http://localhost:1337/api/carts'
        data = {
            "data": {
                "tm_id": user_id,
            }
        }
        response = requests.post(url_post, headers=headers, json=data)
    print(f'User cart 2: {response.json()}')
    response.raise_for_status()
    return response.json()['data'][0]['id']


def get_products():
    strapi_token = os.environ.get('STRAPI_TOKEN')
    url = 'http://localhost:1337/api/products'
    headers = {
        'Authorization': f'bearer {strapi_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_product(id):
    strapi_token = os.environ.get('STRAPI_TOKEN')
    url = f'http://localhost:1337/api/products/{id}'
    headers = {
        'Authorization': f'bearer {strapi_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def get_product_image(id, field):
    strapi_token = os.environ.get('STRAPI_TOKEN')
    url = f'http://localhost:1337/api/products/{id}?populate[0]={field}'
    headers = {
        'Authorization': f'bearer {strapi_token}',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_cart_products(cart_id):
    strapi_token = os.environ.get('STRAPI_TOKEN')
    url_get = f'http://localhost:1337/api/cart-products?filters[carts][$eq]={cart_id}&populate[0]=products'
    headers = {
        'Authorization': f'bearer {strapi_token}',
    }
    response = requests.get(url_get, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def create_cart_product(product_id, quantity=1):
    strapi_token = os.environ.get('STRAPI_TOKEN')
    url_post = f'http://localhost:1337/api/cart-products'
    headers = {
        'Authorization': f'bearer {strapi_token}',
    }
    data = {
        "data": {
            "products": [product_id],
            "quantity": quantity,
        }
    }
    response = requests.post(url_post, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def delete_cart_product(cart_product_id):
    strapi_token = os.environ.get('STRAPI_TOKEN')
    url = f'http://localhost:1337/api/cart-products/{cart_product_id}'
    headers = {
        'Authorization': f'bearer {strapi_token}',
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response.json()


def add_cart_product_to_cart(cart_product_id, cart_id):
    strapi_token = os.environ.get('STRAPI_TOKEN')
    url_put = f'http://localhost:1337/api/carts/{cart_id}'
    headers = {
        'Authorization': f'bearer {strapi_token}',
    }
    data = {
        "data": {
            "cart_products": {
                "connect": [cart_product_id],
            },
        }
    }
    response = requests.put(url_put, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def add_client_to_cart(client_id, cart_id):
    strapi_token = os.environ.get('STRAPI_TOKEN')
    url_put = f'http://localhost:1337/api/carts/{cart_id}'
    headers = {
        'Authorization': f'bearer {strapi_token}',
    }
    data = {
        "data": {
            "client": {
                "connect": [client_id],
            },
        }
    }
    response = requests.put(url_put, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def get_main_keyboard():
    products = get_products()['data']
    keyboard = []
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                product['attributes']['title'],
                callback_data=product['id']
            )
        ])
    keyboard.append([
        InlineKeyboardButton(
            'Моя корзина',
            callback_data='USER_CART',
        )
    ])
    return keyboard


def start(update: Update, context: CallbackContext, r) -> None:
    """Sends a message with three inline buttons attached."""
    # завести пользователя в систему, создать ему корзину
    chat_id = update.message.chat_id
    r.set(chat_id, 'HANDLE_DESCRIPTION')
    reply_markup = InlineKeyboardMarkup(get_main_keyboard())

    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return 'HANDLE_DESCRIPTION'


def hendle_menu(update: Update, context: CallbackContext, r) -> None:
    reply_markup = InlineKeyboardMarkup(get_main_keyboard())
    query = update.callback_query

    query.bot.delete_message(
        chat_id=query.from_user.id,
        message_id=query['message']['message_id']
    )
    query.bot.send_message(
        query.from_user.id, 
        text='Please choose:',
        reply_markup=reply_markup
        )
    return 'HANDLE_DESCRIPTION'


def button(update: Update, context: CallbackContext, r) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    query.answer()
    product = get_product(query.data)
    product_title = product['attributes']['title']
    product_price = product['attributes']['price']
    product_description = product['attributes']['description']
    product_info = f'{product_title}({product_price} руб. за кг.)\n\n{product_description}'
    product_image_url = get_product_image(
        query.data,
        'picture'
    )['data']['attributes']['picture']['data'][0]['attributes']['formats']['thumbnail']['url']
    response = requests.get(f'http://localhost:1337{product_image_url}')
    image_data = BytesIO(response.content)
    r.set('product_id', query.data)

    query.bot.delete_message(
        chat_id=query.from_user.id,
        message_id=query['message']['message_id']
    )
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('назад', callback_data='HANDLE_MENU')],
        [InlineKeyboardButton('добавить в корзину', callback_data='CART')],
        [InlineKeyboardButton('Моя корзина', callback_data='USER_CART')],
    ])
    query.bot.send_photo(
        query.from_user.id,
        photo=image_data,
        caption=product_info,
        reply_markup=reply_markup,
    )

    return 'HANDLE_MENU'


def cart(update: Update, context: CallbackContext, r):
    print('CART')
    query = update.callback_query
    user_id = query.from_user.id
    cart_id = int(get_or_create_user_cart(str(user_id)))
    product_id = int(r.get('product_id'))
    r.set('product_id', '')
    cart_product = create_cart_product(product_id)['data']['id']

    add_cart_product_to_cart(cart_product, cart_id)

    return 'HANDLE_MENU'


def show_user_cart(update: Update, context: CallbackContext, r):
    print('USER_CART')
    query = update.callback_query
    user_id = query.from_user.id
    cart_id = int(get_or_create_user_cart(str(user_id)))
    cart_products = get_cart_products(cart_id)
    cart_text = 'Ваша корзина:\n'
    cart_total = 0
    keyboard = []
    print(f'cart products: {cart_products}')
    for cart_product in cart_products:
        product_sum = 0
        qt = cart_product['attributes']['quantity']
        product = cart_product['attributes']['products']['data'][0]
        product_id  = product['id']
        product_title = product['attributes']['title']
        product_price = product['attributes']['price']
        product_sum = int(qt) * int(product_price)
        cart_text += f'- {product_title} - {qt}шт. итог: {product_sum}руб.\n'
        cart_total += product_sum

        keyboard.append([
            InlineKeyboardButton(
                f'Удалить {product_title} - {qt}шт. на сумму {product_sum}руб.',
                callback_data=cart_product['id']
            )
        ])
    cart_text += f'Всего к оплате: {cart_total}руб.'
    print(cart_text)
    keyboard.append([
        InlineKeyboardButton(
            'Оплата',
            callback_data='PAY'
        )
    ])
    keyboard.append([
        InlineKeyboardButton(
            'В меню',
            callback_data='HANDLE_MENU'
        )
    ])
    reply_markup = InlineKeyboardMarkup(
        keyboard
    )
    query.bot.send_message(
        query.from_user.id,
        text=cart_text,
        reply_markup=reply_markup
    )
#    r.set(query.from_user.id, 'HANDLE_MENU')
    return 'HANDLE_CART'


def delete_product_from_cart(update: Update, context: CallbackContext, r):
    query = update.callback_query
    delete_cart_product(query.data)
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('В меню', callback_data='HANDLE_MENU')],
        [InlineKeyboardButton('Моя корзина', callback_data='USER_CART')],
    ])
    query.bot.send_message(
        query.from_user.id,
        text='товар удален из корзины',
        reply_markup=reply_markup
    )
    return 'USER_CART'


def get_user_email(update: Update, context: CallbackContext, r):
    query = update.callback_query
    print(query.data)

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('В меню', callback_data='HANDLE_MENU')],
        [InlineKeyboardButton('Моя корзина', callback_data='USER_CART')],
    ])
    query.bot.send_message(
        query.from_user.id,
        text='Введите ваш email для оплаты',
        reply_markup=reply_markup
    )
    return 'EMAIL_WAIT'


def create_user_with_email(update: Update, context: CallbackContext, r, user):
    print('EMAIL_WAIT')
    users_reply = update.message.text
    print(users_reply)
    client_id = create_client(user)['data']['id']
    cart_id = get_or_create_user_cart(user['tm_id'])
    add_client_to_cart(client_id, cart_id)
    update.message.reply_text('Ваш заказ сформирован')
    return 'HANDLE_MENU'


def handle_users_reply_text(update, context, r):
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return

    print(r.get(chat_id).decode("utf-8"))
    if '@' in user_reply and not update.callback_query and r.get(chat_id).decode("utf-8") == 'EMAIL_WAIT':
        try:
            email = user_reply
            chat = update.message['chat']
            tm_id = chat['id']
            username = chat['username']
            user = {
                "tm_id": tm_id,
                "email": email,
                "username": username,
            }
            next_state = create_user_with_email(update, context, r, user)
            r.set(chat_id, next_state)
        except Exception as err:
            print(err.with_traceback())



def handle_users_reply(update, context, r):
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return

    if user_reply == '/start':
        user_state = 'START'
    elif user_reply == 'назад':
        user_state = 'HANDLE_MENU'
    elif user_reply == 'добавить в корзину':
        user_state = 'CART'
    elif user_reply == 'Моя корзина':
        user_state = 'USER_CART'
    else:
        user_state = r.get(chat_id).decode("utf-8")

    states_functions = {
        'START': start,
        'HANDLE_MENU': hendle_menu,
        'HANDLE_DESCRIPTION': button,
        'CART': cart,
        'USER_CART': show_user_cart,
        'HANDLE_CART': delete_product_from_cart,
        'EMAIL_WAIT': create_user_with_email,
        'PAY': get_user_email,
    }

    if user_reply in states_functions.keys():
        user_state = user_reply

    state_handler = states_functions[user_state]

    try:
        next_state = state_handler(update, context, r)
        r.set(chat_id, next_state)
    except Exception as err:
        print(err.with_traceback())


def main():
    load_dotenv()
    r = redis.Redis(
        host=os.environ.get('REDIS_HOST', default='localhost'),
        port=os.environ.get('REDIS_PORT', default=6379),
        db=0
    )
    telegram_token = os.environ.get('TM_BOT_TOKEN')
    updater = Updater(telegram_token)
    redis_handle_users_reply = partial(handle_users_reply, r=r)
    redis_handle_users_reply_text = partial(handle_users_reply_text, r=r)
    redis_button = partial(button, r=r)
    redis_start = partial(start, r=r)
    dp = updater.dispatcher

    dp.add_handler(CallbackQueryHandler(redis_handle_users_reply))
    dp.add_handler(MessageHandler(Filters.text, redis_handle_users_reply_text))
    dp.add_handler(CommandHandler('start', redis_start))
    dp.add_handler(CallbackQueryHandler(redis_button))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
