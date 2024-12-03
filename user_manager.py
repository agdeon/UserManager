import json
import logging
import os
import re
import shutil
import time

class User:
    users_folder_name = "users"
    console_log_lvl = logging.DEBUG
    file_log_lvl = logging.INFO

    def __init__(self, chat_id):
        self.user_chat_id = chat_id
        self.user_folder_name = chat_id
        self.user_log_filename = 'user.log'
        self.user_chat_history_filename = 'history.json'
        self.user_cfg_filename = 'user.cfg'
        self.user_folder_path = User.users_folder_name + '/' + self.user_folder_name
        self._create_users_folder()

        if self.is_new_user(self.user_chat_id):
            self._create_user_folder()
            self._create_user_cfg()
            self._create_user_history()
            self._create_user_log()

        self._user_logger = logging.getLogger('USERLOG_' + self.user_chat_id)
        self._configure_logger()

    def _create_user_cfg(self):
        def_user_cfg = {
            "user": {
                "chat_id": self.user_chat_id,
                "models": ["gpt-4o-mini"],
                "preferences": {
                    "language": "ru",
                }
            }
        }
        with open(f'{User.users_folder_name}/{self.user_folder_name}/{self.user_cfg_filename}', 'w', encoding='utf-8') as config_file:
            json.dump(def_user_cfg, config_file, indent=4, ensure_ascii=False)

    def _create_user_history(self):
        user_path = User.users_folder_name + '/' + self.user_chat_id
        file_path = os.path.join(user_path, self.user_chat_history_filename)
        with open(file_path, 'w', encoding='utf-8') as file:
            pass  # пустой файл

    def _create_user_log(self):
        user_path = User.users_folder_name + '/' + self.user_chat_id
        file_path = os.path.join(user_path, self.user_log_filename)
        with open(file_path, 'w', encoding='utf-8') as file:
            pass  # пустой файл

    def _create_user_folder(self):
        user_path = User.users_folder_name + '/' + self.user_chat_id
        print(user_path)
        os.makedirs(user_path)

    def _create_users_folder(self):
        main_folder = User.users_folder_name
        if not os.path.exists(main_folder):
            os.makedirs(main_folder)

    def _configure_logger(self):
        self._user_logger.setLevel(logging.DEBUG)  # Устанавливаем уровень логирования
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        console_handler = logging.StreamHandler()
        console_handler.setLevel(User.console_log_lvl)
        console_handler.setFormatter(formatter)

        file_handler = logging.FileHandler(self.user_folder_path + '/' + self.user_log_filename, encoding='utf-8')
        file_handler.setLevel(User.file_log_lvl)
        file_handler.setFormatter(formatter)

        self._user_logger.addHandler(console_handler)
        self._user_logger.addHandler(file_handler)

    def is_new_user(self, chat_id):
        user_path = User.users_folder_name + '/' + chat_id
        if not os.path.exists(user_path):
            return True

    # в формате массива [ {"role": "assistant", "content": reply}, ]
    def write_history(self, conv_history):
        file_path = self.user_folder_path + '/' + self.user_chat_history_filename
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(conv_history, json_file, indent=4, ensure_ascii=False)

    def remove_history(self):
        file_path = self.user_folder_path + '/' + self.user_chat_history_filename
        with open(file_path, 'w', encoding='utf-8') as json_file:
            pass

    def write_log(self, text):
        self._user_logger.info(text)


if __name__ == '__main__':
    test_conv_hist = [
        {"role": "user", "content": "Пример запроса пользователя"},
        {"role": "assistant", "content": "Пример ответа ИИ"}
    ]
    user = User('41242')
    user.write_log(f"Новый пользователь {user.user_chat_id} зарегистрирован.")
    user.remove_history()