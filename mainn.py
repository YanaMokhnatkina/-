import json
import base64
from os.path import exists, abspath
from os import getenv, remove
from dotenv import load_dotenv
import telebot
from fontTools.merge.util import first
from telebot import types
from work_with_stats import StatsManager
from work_with_words import WordFile, Test, Question, DoneTest
from work_with_database import Database
from threading import Thread
from datetime import datetime as dt
from time import sleep
from random import shuffle
from datetime import datetime


class User:
    def __init__(self, id, tag, name, words=[], done_tests=[], hour=9, minute=0, is_finding_rus_word = False, is_finding_eng_word = False, is_setting_time = False, task_check=0, temp_test_data=DoneTest(), is_doing_test=False, temp_questions=None):
        self.id = id
        self.tag = tag
        self.name = name
        self.words = words
        self.done_tests = done_tests
        for i, test in enumerate(self.done_tests):
            self.done_tests[i] = DoneTest(**test)

        self.hour = hour
        self.minute = minute

        self.is_finding_rus_word = is_finding_rus_word
        self.is_finding_eng_word = is_finding_eng_word
        self.is_setting_time = is_setting_time
        self.is_doing_test = is_doing_test

        self.temp_questions = temp_questions

        self.temp_test_data = temp_test_data
        if isinstance(self.temp_test_data, dict):
            self.temp_test_data = DoneTest(**self.temp_test_data)

        self.task_check = task_check


        Thread(target=self.send_day_word, daemon=True).start()

    def send_day_word(self):
        while True:
            current_time = dt.now()
            current_hour = int(current_time.hour)
            current_minute = int(current_time.minute)
            # print(current_hour)
            # print(current_minute)
            # print(user.hour)
            # print(user.minute)
            if self.hour <= current_hour and self.minute <= current_minute:
                if self.done_tests and len(self.done_tests) % 7 == 0:
                    show_stat(self)
                elif self.task_check >= 7:
                    start_test(self)
                else:
                    get_word(self, daily=True)
                    sleep(86390)  # ждём день
            else:
                # formula = abs((user.hour - current_hour)*3600) + abs((user.minute - current_minute)*60)
                # print(formula)
                # print("ждём")
                sleep(10)

load_dotenv(abspath("token.env"))
TOKEN = getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)
db = Database("database.json")
file_worker = WordFile("WORDS.txt")

def get_word(user: User, daily=False):
    eng_word, rus_word = file_worker.get_random_word()
    if [eng_word, rus_word] in user.words:
        get_word(user, daily)
        return
    user.words.append([eng_word, rus_word])
    user.task_check += 1
    db.add_user(user.id, user.__dict__) # обновляем данные о словах пользователя в "базе данных"
    if not daily:
        bot.send_message(user.id, f"Твоё слово: {eng_word}\nЕго перевод: {rus_word}")
    else:
        bot.send_message(user.id, f"Твоё ежедневное слово: {eng_word}\nЕго перевод: {rus_word}")

def show_stat(user: User):
    stat_manager = StatsManager(user.id, user.done_tests)
    data = stat_manager.create_and_save_plot()
    if not data:
        bot.send_message(user.id, "К сожалению, у вас недостаточно пройденных тестов для того, чтобы смотреть статистику...")
        main_buttons(user.id)
        return
    path, marks = data

    text = ("Вот результаты по всем вашим тестам!\n"
            f"Тестов на 5: {marks[5]}\n"
            f"Тестов на 4: {marks[4]}\n"
            f"Тестов на 3: {marks[3]}\n"
            f"Тестов на 2: {marks[2]}")

    bot.send_photo(user.id, photo=open(path, 'rb'), caption=text)

    remove(path)

@bot.message_handler(commands=["start", "help"])
def start(message):
    bot.send_message(message.chat.id, text=f"Привет {message.chat.first_name} 👋\nЯ бот, благодаря которому твои навыки английского"
                               f" языка станут в 100 раз лучше 😉\nПосмотри команды в меню, или следуй кнопкам для того, "
                               f"чтобы начать качать уровень языка 💪")
    main_buttons(message.chat.id)

def main_buttons(id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    check_stat_btn = types.KeyboardButton(text="Посмотреть статистику")
    start_task_btn = types.KeyboardButton(text="Начать тест")
    get_word_btn = types.KeyboardButton(text="Изучить новое слово")
    set_time_btn = types.KeyboardButton(text="Поставить время")
    find_eng_word_btn = types.KeyboardButton(text="Найти перевод с русского")
    find_rus_word_btn = types.KeyboardButton(text="Найти перевод с английского")
    keyboard.add(get_word_btn, set_time_btn, start_task_btn, find_eng_word_btn, find_rus_word_btn, check_stat_btn)
    bot.send_message(id, text="Выберите варианты:", reply_markup=keyboard)

@bot.message_handler(content_types=["text"])
def get_messages(message):
    user = get_user(message.chat.id, message.chat.username, message.chat.first_name)
    if user.is_doing_test:
        bot.send_message(user.id, "Пожалуйста, сначала закончите тест!")
        return
    match message.text:
        case "Посмотреть статистику":
            show_stat(user)
        case "Начать тест":
            if user.task_check >= 7:
                start_test(user)
            else:
                bot.send_message(user.id, text="У тебя недостаточно слов в запасе для того, чтобы их повторить :(\nДавай это исправим!")
                get_word(user)
        case "Изучить новое слово":
            get_word(user)
        case "Поставить время":
            user.is_setting_time = True
            bot.send_message(user.id, text='Введите время в формате "часы:минуты"')
        case "Найти перевод с английского":
            user.is_finding_rus_word = True
            bot.send_message(user.id, "Введите слово на английском языке:")
        case "Найти перевод с русского":
            user.is_finding_eng_word = True
            bot.send_message(user.id, "Введите слово на русском языке:")
        case _:
            if user.is_finding_eng_word:
                user.is_finding_eng_word = False
                find_eng_word(user, message.text)
            elif user.is_finding_rus_word:
                user.is_finding_rus_word = False
                find_rus_word(user, message.text)
            elif user.is_setting_time:
                try:
                    hour, minute = tuple(map(int, message.text.split(':')))
                    user.is_setting_time = True
                    set_time(user, hour, minute)
                    bot.send_message(user.id, text="Время успешно изменено!")
                except:
                    bot.send_message(user.id,"Пожалуйста, введите корректный формат времени!")
            else:
                bot.send_message(user.id, "Такой команды не найдено 😢\nПожалуйста, попробуйте что-то из меню или кнопок ниже.")
                main_buttons(user.id)

def get_user(id, username, first_name):
    user = find_active_user(id)

    if not user: user = db.get_user(id)
    else: return user
    if not user:
        user = User(id, username, first_name)
        users.append(user)
        db.add_user(id, user.__dict__)
        return user
    else:
        user = User(**user)
        users.append(user)
        return user

def find_active_user(id: int):
    for user in users:
        if user.id == id: return user
    return False

users = db.get_all_data()
users = [User(**users[key]) for key in users]

def set_time(user: User, hour: int, minute: int):
    user.hour = hour
    user.minute = minute
    user.is_setting_time = False
    db.add_user(user.id, user.__dict__)

def find_rus_word(user: User, word: str):
    rus_word = file_worker.get_word(word_in_english=word)
    if rus_word:
        bot.send_message(user.id, f"Ваш перевод: {rus_word}")
    else:
        bot.send_message(user.id, f"К сожалению, такого слова не найдено...\nУбедитесь, что вы всё правильно ввели!")

def find_eng_word(user: User, word: str):
    eng_word = file_worker.get_word(word_in_russian=word)
    if eng_word:
        bot.send_message(user.id, f"Ваш перевод: {eng_word}")
    else:
        bot.send_message(user.id, f"К сожалению, такого слова не найдено...\nУбедитесь, что вы всё правильно ввели!")

def start_test(user: User):
    user.task_check = 0
    user.is_doing_test = True
    db.add_user(user.id, user.__dict__)
    test = Test(user.id, user.words, len(user.done_tests))
    questions = test.create_test()
    questions = list(set(questions))
    user.temp_test_data = DoneTest(user.id, len(questions))
    # user.temp_test_data[0] = len(questions)
    user.temp_questions = questions

    keyboard = types.InlineKeyboardMarkup()
    # создаём кнопки с неправильными переводами
    # types.InlineKeyboardButton(text=incorrect_answer, callback_data=incorrect_answer.split()[0]) for incorrect_answer in questions[0].incorrect_answers

    buttons = []
    for incorrect_answer in questions[0].incorrect_answers:
        if len(incorrect_answer) < 21:
            buttons.append(types.InlineKeyboardButton(text=incorrect_answer, callback_data=incorrect_answer.split()[0]))
        else:
            buttons.append(types.InlineKeyboardButton(text=f"{incorrect_answer[:18]}...",
                                                      callback_data=incorrect_answer.split()[0]))
    # добавляем в этот список кнопку с правильным ответом
    if len(user.temp_questions[0].correct_answer) >= 21: user.temp_questions[
        0].correct_answer = f"{user.temp_questions[0].correct_answer[:18]}..."
    buttons.append(types.InlineKeyboardButton(text=user.temp_questions[0].correct_answer,
                                              callback_data=user.temp_questions[0].correct_answer))

    shuffle(buttons) # делаем это, чтобы кнопки высвечивались в случайном порядке, а не чтобы всегда правильный ответ
    # был последним вариантом
    keyboard.add(*buttons)

    bot.send_message(user.id, text=f"Выберите верный перевод слова: {questions[0].word_question}", reply_markup=keyboard)

    # # мы сразу передаём все вопросы и данные о них обработчику инлайн-кнопок
    # callback_data = ""
    # for question in questions:
    #     callback_data += f"{question.word_question.strip()}:{question.correct_answer.strip()}"
    #     for incorrect_answer in question.incorrect_answers:
    #         callback_data += f":{incorrect_answer.strip()}"
    #     callback_data += "/"
    # first_callback_data = callback_data.split('/')[0].split(':')
    # print("первый коллбэк", first_callback_data)

    # # закодированный список со всеми вопросами в base64
    # encoded_callback = encode_json(get_json_from_callback(callback_data))
    #
    # keyboard = types.InlineKeyboardMarkup()
    # # types.InlineKeyboardButton(text=answer, callback_data=f"{answer}*{callback_data}") for answer in first_callback_data[2:]
    # buttons = []
    # for incorrect_answer in first_callback_data[2:]:
    #     print(incorrect_answer.strip())
    #     callback = encode_json(get_json_from_callback(f"{incorrect_answer}*{callback_data}"))
    #     buttons.append(types.InlineKeyboardButton(text=incorrect_answer, callback_data=callback))
    #
    # callback = encode_json(get_json_from_callback(f"{first_callback_data[1]}*{callback_data}"))
    # buttons.append(types.InlineKeyboardButton(text=first_callback_data[1], callback_data=callback))
    # shuffle(buttons)
    # keyboard.add(*buttons)

@bot.callback_query_handler(func=lambda call: True)
def check_answer(call: types.CallbackQuery):
    # находим пользователя по id из активных для того, чтобы изменять его результаты теста
    user = get_user(call.message.chat.id, call.message.chat.username, call.message.chat.first_name)

    if not user.temp_questions: return

    if call.data == user.temp_questions[0].correct_answer:
        bot.answer_callback_query(call.id, text="Правильно!")
        user.temp_test_data.answers_len += 1
    else:
        bot.answer_callback_query(call.id, text="Неправильно!")

    if len(user.temp_questions) == 1:
        user_score = (100 * user.temp_test_data.answers_len) / user.temp_test_data.questions_len
        if user_score <= 35: user_score = 2
        elif user_score <= 50: user_score = 3
        elif user_score <= 75: user_score = 4
        elif user_score <= 100: user_score = 5
        user.temp_test_data.mark = user_score
        date = datetime.now()
        user.temp_test_data.day = date.day
        user.temp_test_data.month = date.month

        user.done_tests.append(user.temp_test_data)
        bot.send_message(user.id, f"Тест окончен! Ваши результаты:\nВсего вопросов было - {user.temp_test_data.questions_len}\n"
                                  f"Вы ответили на - {user.temp_test_data.answers_len}\n"
                                  f"Ваша оценка - {user.temp_test_data.mark}!")
        user.temp_test_data = DoneTest(user.id)
        user.is_doing_test = False
        user.temp_questions = None
        db.add_user(user.id, user.__dict__)
        main_buttons(user.id)
        return

    user.temp_questions = user.temp_questions[1:] # на первый вопрос ответили, убираем его

    keyboard = types.InlineKeyboardMarkup()
    # создаём кнопки с неправильными переводами
    # buttons = [types.InlineKeyboardButton(text=incorrect_answer, callback_data=incorrect_answer.split()[0]) for incorrect_answer in
    #            user.temp_questions[0].incorrect_answers if len(incorrect_answer) < 21 else types.InlineKeyboardButton(text=f"{incorrect_answer[18]}...", callback_data=incorrect_answer.split()[0])]
    buttons = []
    for incorrect_answer in user.temp_questions[0].incorrect_answers:
        if len(incorrect_answer) < 21:
            buttons.append(types.InlineKeyboardButton(text=incorrect_answer, callback_data=incorrect_answer.split()[0]))
        else:
            buttons.append(types.InlineKeyboardButton(text=f"{incorrect_answer[:18]}...", callback_data=incorrect_answer.split()[0]))
    if len(user.temp_questions[0].correct_answer) >= 21: user.temp_questions[0].correct_answer = f"{user.temp_questions[0].correct_answer[:18]}..."
    buttons.append(types.InlineKeyboardButton(text=user.temp_questions[0].correct_answer, callback_data=user.temp_questions[0].correct_answer))
    shuffle(buttons)  
    keyboard.add(*buttons)  # добавляем варианты на клавиатуру

    bot.edit_message_text(text=f"Выберите верный перевод слова: {user.temp_questions[0].word_question}", chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=keyboard)

    # callback = decode_json(call.data)
    #
    # # answer_by_user = call.data.split('*')[0]
    # # questions = call.data.split('*')[1].split('/')
    # # question = questions[0].split(':')
    # # correct_answer = question[1]
    #
    # answer_by_user = callback[0].split('*')[0]
    # question = callback[0].split('*')[1].split(':')
    # correct_answer = question[1]
    #
    # if answer_by_user == correct_answer:
    #     bot.answer_callback_query(call.id, text="Правильно!")
    #     user.temp_test_data[1] += 1
    # else:
    #     bot.answer_callback_query(call.id, text="Неправильно!")
    #
    # # Мы закончили тест. Это был последний вопрос
    # if len(callback) == 1:
    #     user.temp_test_data[2] = user.temp_test_data[1]//user.temp_test_data[0]
    #     user.done_tests.append(user.temp_test_data)
    #     bot.send_message(user.id, f"Тест окончен! Ваши результаты:\nВсего вопросов было - {user.temp_test_data[0]}\n"
    #                               f"Вы ответили на - {user.temp_test_data[1]}\n"
    #                               f"Ваша оценка - {user.temp_test_data[2]}!")
    #     user.temp_test_data = [0, 0, 0]
    #     user.is_doing_test = False
    #     db.add_user(user.id, user.__dict__)
    #     main_buttons(user.id)
    #     return
    #
    # callback_data = "/".join(questions[1:]) # Пропускаем первый вопрос, так как на него пользователь уже дал ответ
    # next_question = questions[1].split(':')
    # nq_word = next_question[0]
    # nq_answer = next_question[1]
    # nq_incorrect_answers = next_question[2:]
    # keyboard = types.InlineKeyboardMarkup()
    # buttons = [types.InlineKeyboardButton(text=answer, callback_data=f"/{answer}*{callback_data}") for answer in
    #            nq_incorrect_answers[2:]]
    # buttons.append(types.InlineKeyboardButton(text=nq_answer,
    #                                           callback_data=nq_answer))
    # shuffle(buttons)
    # keyboard.add(*buttons)
    # bot.edit_message_text(text=f"Выберите верный перевод слова: {nq_word}", chat_id=call.message.chat.id, message_id=call.message.id, reply_markup=keyboard)
    # # bot.edit_message_reply_markup(call.message.chat.id, message_id=call.message.id, reply_markup=keyboard)

bot.infinity_polling()