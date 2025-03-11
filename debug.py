import asyncio
import concurrent.futures

def blocking_io():
    # File operations (such as logging) can block the
    # event loop: run them in a thread pool.
    with open('/dev/urandom', 'rb') as f:
        return f.read(100)

def cpu_bound():
    # CPU-bound operations will block the event loop:
    # in general it is preferable to run them in a
    # process pool.
    return sum(i * i for i in range(10 ** 7))

async def main():
    loop = asyncio.get_running_loop()

    ## Options:

    # 1. Run in the default loop's executor:
    result = await loop.run_in_executor(
        None, blocking_io)
    print('default thread pool', result)

    # 2. Run in a custom thread pool:
    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool, blocking_io)
        print('custom thread pool', result)

    # 3. Run in a custom process pool:
    with concurrent.futures.ProcessPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool, cpu_bound)
        print('custom process pool', result)

if __name__ == '__main__':
    asyncio.run(main())
    
    
    
from flask import Flask, request, jsonify
import logging
import os
from dotenv import load_dotenv
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import NetworkError
import asyncio
import nest_asyncio

nest_asyncio.apply()

logging.basicConfig(level=logging.INFO)
load_dotenv()

app = Flask(__name__)
bot = telegram.Bot(token=os.getenv("BOT_TOKEN"))

async def send_blocked_message(user_id, port):
    keyboard = [[InlineKeyboardButton("Разблокировать", callback_data='unlock')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.send_message(chat_id=user_id, text='Ваш ключ заблокирован из-за подозрительной активности. Если Вы считаете что это ошибка, то нажмите кнопку ниже.', reply_markup=reply_markup)
    logging.info(f"Port {port} has been blocked for user {user_id}.")

def run_async(func):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(func(*args, **kwargs))
    return wrapper

@app.route('/block_port', methods=['POST'])
@run_async
async def block_port():
    port = request.form.get('port')
    if port:
        user_id = find_user_by_port(port)
        if user_id:
            await send_blocked_message(user_id, port)      # <------ Error should be resolved here
            logging.info(f"Port {port} has been blocked")
            return jsonify({'message': f'Port {port} has been blocked for user {user_id}.'}), 200
        else:
            logging.info(f"Port {port} has been blocked, but no user found.")
            return jsonify({'message': f'Port {port} has been blocked, but no user found.'}), 200
    else:
        return jsonify({'error': 'Port not provided.'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)