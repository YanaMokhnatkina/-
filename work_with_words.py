from os.path import exists, abspath
from random import choice, randint, shuffle
from datetime import datetime

# Класс работы с файлом слов
# файл со словами устроен следующим образом: нечётные слова - английские, следующие чётные - их перевод.
# Знак табуляции - разные варианты перевода (синонимы)
class WordFile:
    def __init__(self, path):
        self.is_all_good = False
        self.path = abspath(path)
        if exists(self.path):
            self.is_all_good = True
            self.words = self.get_all_words()

    # Если передано слово на английском, мы получаем его на русском. Если передано на русском,
    # то получаем перевод на английский. Если слово не найдено - False
    # важный момент - файл со словами отсортирован по алфавиту, а это значит то, что можно применить бинарный поиск
    def get_word(self, word_in_english="", word_in_russian=""):
        word = word_in_english.lower() if word_in_english else word_in_russian.lower()
        # i = 0 if word_in_english else 1
        for eng_word, rus_word in self.words:
            if word in eng_word: return rus_word
            elif word in rus_word: return eng_word
        return False

        # low = 0
        # high = len(self.words) - 1
        # mid = len(self.words) // 2
        #
        # while self.words[mid][i] != word and low <= high:
        #     if word > self.words[mid][i]:
        #         low = mid + 1
        #     else:
        #         high = mid - 1
        #     mid = (low + high) // 2
        #
        # if low > high:
        #     return False
        # else:
        #     return self.words[mid][i-1] # не i+1, чтоб не было IndexOutOfRange

    # возвращает кортеж, в котором первый элемент - случайно слово на английском, а второй - его перевод
    def get_random_word(self):
        return choice(self.words)

    # получает все слова из файла со словами по пути self.path
    def get_all_words(self):
        with open(self.path, 'r') as f:
            words = []
            i = 0 # номер строки. Начинаем с нуля, так как сразу прибавляем единицу
            word = [None, None] # слово, которое будет добавлено во все слова
            for line in f:
                i += 1
                if i % 2 != 0:
                    word[0] = line.lower().strip()
                else:
                    word[1] = line.lower().strip()
                    words.append(word)
                    word = [None, None]
        return words

class Question:
    def __init__(self, word_question, correct_answer, incorrect_answers):
        self.word_question = word_question
        self.correct_answer = correct_answer
        self.incorrect_answers = incorrect_answers # список с неправильными ответами

# Формат файла с тестом:
# txt файл. * помечает верный ответ, вариантов ответа 4 (верный включительно)
# между вопросами один отступ
class Test:
    options_count = 4 # 3 неверных ответа, 1 верный
    def __init__(self, user_id, user_words, done_tests):
        self.user_id = user_id # нужен для создания временного файла с тестом
        self.user_words = user_words
        self.done_tests = done_tests + 1 # количество завершённых тестов ( len(user.done_tests) )
        # нужно для того, чтобы делать тест не из всех изученных
        # пользователем слов, а только из их количество делённое на done_tests (завершённые тесты)

    # создаёт список с объектами класса Question и возвращает его
    def create_test(self):
        questions = []
        for i in range(len(self.user_words)):
            words = [self.user_words[j] for j in range(len(self.user_words)) if j != i]
            question_word, answer = self.user_words[i]
            incorrect_answers = []
            # if len(words) < self.options_count: self.options_count = len(words)
            for _ in range(self.options_count):
                # options = [k for k in range(len(self.user_words)) if k != i]
                # index = choice(options)
                # options.remove(index)
                doesnt_matter, incorrect_answer = choice(words)
                words.remove([doesnt_matter, incorrect_answer])
                incorrect_answers.append(incorrect_answer)
            questions.append(Question(question_word, answer, incorrect_answers))
        shuffle(questions)
        return questions

# Объект завершённого теста, по которому можно посмотреть статистику
class DoneTest(Test):
    def __init__(self, user_id=0, questions_len=0, answers_len=0, day=1, month=1, mark=2):
        self.user_id = user_id
        self.questions_len = questions_len # всего вопросов в тесте
        self.answers_len = answers_len # отвечено пользователем
        self.mark = mark
        self.day = day
        self.month = month