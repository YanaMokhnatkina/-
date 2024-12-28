import json
from os.path import exists, abspath

class Database:
    def __init__(self, path):
        self.path = abspath(path)
        if not exists(self.path):
            with open(self.path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(dict(), indent=4))

    # Получить всю информацию о пользователе. Если такого нет - return False
    def get_user(self, user_id):
        with open(self.path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
        try:
            return data[user_id]
        except: return False

    # Добавить в базу нового пользователя с id user_id и данными user_dict (Который берётся из User.__dict__)
    # Если такой пользователь уже существует, то этот метод просто обновляет данные
    def add_user(self, user_id, user_dict: dict):
        data = self.get_all_data()
        updated_user_dict = dict([key, value] for key, value in user_dict.items())
        try:
            updated_user_dict["temp_test_data"] = updated_user_dict["temp_test_data"].__dict__
        except: pass
        for i, test in enumerate(updated_user_dict["done_tests"]):
            try:
                updated_user_dict["done_tests"][i] = test.__dict__
            except: pass
        with open(self.path, 'w', encoding='utf-8') as f:
            data[str(user_id)] = updated_user_dict
            f.write(json.dumps(data, indent=4))

    def get_all_data(self):
        with open(self.path, 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
        return data