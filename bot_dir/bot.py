import telebot
import sqlite3
import configparser
from dotenv import load_dotenv
from telebot import types
import os
load_dotenv()

config = configparser.ConfigParser()
config.read('config.ini')
db_name = config['db_name']['db_name']
connection = sqlite3.connect(db_name)
cursor = connection.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS Tasks(
id INTEGER PRIMARY KEY AUTOINCREMENT,
task TEXT NOT NULL,
completed INTEGER NOT NULL
)
''')
connection.commit()
connection.close()

bot = telebot.TeleBot(os.getenv("TOKEN"))

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id == config.getint('tg_id', 'admin'):
        admin_name = config['tg_id']['admin_name']
        bot.reply_to(message, f"Приветствую {admin_name}")
    bot.reply_to(message, config['phrases']['greeting'])

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, config['phrases']['available_commands'])

@bot.message_handler(commands=['add_task'])
def add_task_input(message):
    bot.reply_to(message, config['phrases']['add_task_prompt'])
    bot.register_next_step_handler(message, add_task_adder)
                                   
def add_task_adder(message):
    task_text = message.text
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Tasks (task, completed) VALUES (?, ?)', (task_text, 0))
    bot.reply_to(message, config['phrases']['task_added'])
    connection.commit()
    connection.close()

@bot.message_handler(commands=['get_tasks'])
def get_tasks(message):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Tasks')
    tasks = list(cursor.fetchall())
    for row in range(len(tasks)):
        for column in range(len(tasks[row])):
            if column != 0 and column != 1:
                if tasks[row][column] == 0:
                    tasks[row] = list(tasks[row])
                    tasks[row][column] = 'Не сделано!'
                else:
                    tasks[row] = list(tasks[row])
                    tasks[row][column] = 'Сделано!'
        tasks[row][0] = str(tasks[row][0])
        tasks[row] = " ".join(tasks[row])
    bot.reply_to(message, '\n'.join(tasks))
    connection.commit()
    connection.close()

@bot.message_handler(commands=['close_task'])
def close_task_input(message):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    bot.reply_to(message, config['phrases']['specify_task'])
    bot.register_next_step_handler(message, close_task_db)

def close_task_db(message):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    task_num = int(message.text)
    cursor.execute('SELECT completed FROM Tasks WHERE ID = ?', (task_num,))
    results = cursor.fetchall()
    if results == []:
        bot.reply_to(message, config['phrases']['task_not_found'])
        return
    else:
        cursor.execute('UPDATE Tasks SET completed = ? WHERE id = ?', (1, task_num))
        bot.reply_to(message, config['phrases']['task_closed'])
    connection.commit()
    connection.close()

bot.polling()