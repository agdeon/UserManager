import json
import logging
import os
import shutil
import time
import copy
from typing import Union

from bot_config import BotConfig

class UserSettings:
    """
    Класс для настроек поведения класса User
    Обязателен к импорту наряду с ним
    """
    FOLDER_NAME = "users"
    LOG_FILENAME = 'user.log'
    HISTORY_FILENAME = 'history.json'
    CFG_FILENAME = 'user.cfg'

class Ranks:
    """
    Класс для настроек рангов пользователей класса User
    Обязателен к импорту наряду с ним
    """
    BASIC = 'basic'
    PLUS = 'plus'
    VIP = 'vip'
    ADMIN = 'admin'

class User:
    """
    Класс для управления записями пользователей, регистрации, сохранения истории,
    конфигурации, логов и тд.
    """
    CONSOLE_LOG_LVL = logging.DEBUG
    FILE_LOG_LVL = logging.INFO
    DEFAULT_SYS_CONTENT = {"role": "system", "content": ""}

    def __init__(self, chat_id):

        chat_id = str(chat_id)
        self.id = chat_id

        # Внутренние классы
        self.config = self.Config(self)
        self.history = self.History(self)
        self.log = self.Log(self)

        self.folder_name = chat_id # возможно в будущем изменится
        self._user_folder_path = os.path.join(UserSettings.FOLDER_NAME, self.folder_name)
        self._create_users_folder()

        if self.is_new_user():
            self._create_user_folder()
            self._create_user_cfg()
            self._create_user_log()
            self._create_user_history()
            self._set_default_history()

        # после того как файл точно создан
        self._user_logger = logging.getLogger('USER_' + self.id)
        self._configure_logger()

    # ---------------------------
    # МЕТОДЫ ЭКЗЕМПЛЯРА
    # ---------------------------

    def set_gpt_prompt(self, prompt_text):
        hst = self.get_history()
        system_content = hst[0]
        if 'role' not in system_content or  system_content['role'] != 'system':
            self.error(f"Ошибка в функции set_gpt_prompt: 'role' not in system_content or  system_content['role'] != 'system'")
        hst[0]['content'] = prompt_text
        self.save_history(hst)

    def reset(self):
        files_to_delete = [
            UserSettings.LOG_FILENAME,
            UserSettings.HISTORY_FILENAME,
            UserSettings.CFG_FILENAME
        ]
        for file_name in files_to_delete:
            if os.path.exists(file_name):
                os.remove(os.path.join(self._user_folder_path, file_name))

        self._create_user_folder()
        self._create_user_cfg()
        self._create_user_log()
        self._create_user_history()
        self._set_default_history()

    def remove(self):
        # cначала надо отвязать все handlers логгера
        for handler in self._user_logger.handlers[:]:  # Итерируем по копии списка, чтобы безопасно удалять
            if isinstance(handler, logging.FileHandler):  # Проверяем, является ли обработчик FileHandler
                self._user_logger.removeHandler(handler)
                handler.close()
        folder_path = os.path.join(UserSettings.FOLDER_NAME, self.id)
        shutil.rmtree(folder_path)
        cfg = self.get_cfg()

    # в формате массива [ {"role": "assistant", "content": reply}, ]
    def save_history(self, conv_history: list):
        managed_hist = self._manage_history_list(conv_history) # автоочистка истории c сохранением 0 элемента (system content)
        file_path = os.path.join(self._user_folder_path, UserSettings.HISTORY_FILENAME)
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(managed_hist, json_file, indent=4, ensure_ascii=False)

    def get_history(self) -> list:
        file_path = os.path.join(self._user_folder_path, UserSettings.HISTORY_FILENAME)
        if self._is_file_empty(file_path):
            return []
        with open(file_path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)

    def clear_history(self):
        file_path = os.path.join(self._user_folder_path, UserSettings.HISTORY_FILENAME)
        with open(file_path, 'w', encoding='utf-8') as json_file:
            pass

    def debug(self, text):
        self._user_logger.debug(text)

    def info(self, text):
        self._user_logger.info(text)

    def error(self, text):
        self._user_logger.error(text)

    def clear_log_file(self):
        file_path = os.path.join(self._user_folder_path, UserSettings.LOG_FILENAME)
        with open(file_path, 'w', encoding='utf-8') as json_file:
            pass

    def is_new_user(self):
        user_path = os.path.join(UserSettings.FOLDER_NAME, self.id)
        if not os.path.exists(user_path):
            return True

    # ---------------------------
    # МЕТОДЫ КЛАССА
    # ---------------------------
    @classmethod
    def _create_users_folder(cls):
        main_folder = UserSettings.FOLDER_NAME
        if not os.path.exists(main_folder):
            os.makedirs(main_folder)

    @staticmethod
    def _is_file_empty(path):
        return os.stat(path).st_size == 0

    # ---------------------------
    # ПРИВАТНЫЕ МЕТОДЫ
    # ---------------------------
    def _set_default_history(self):
        self.clear_history()
        file_path = os.path.join(self._user_folder_path, UserSettings.HISTORY_FILENAME)
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump([self.__class__.DEFAULT_SYS_CONTENT], json_file, indent=4, ensure_ascii=False)

    def _create_user_cfg(self):
        User.Config.DEFAULT_VAL["id"] = self.id
        cfg_path = os.path.join(self._user_folder_path, UserSettings.CFG_FILENAME)
        with open(cfg_path, 'w', encoding='utf-8') as config_file:
            json.dump(User.Config.DEFAULT_VAL, config_file, indent=4, ensure_ascii=False)

    def _create_user_history(self):
        hist_path = os.path.join(self._user_folder_path, UserSettings.HISTORY_FILENAME)
        with open(hist_path, 'w', encoding='utf-8') as file:
            pass  # пустой файл

    def _create_user_log(self):
        log_path = os.path.join(self._user_folder_path, UserSettings.LOG_FILENAME)
        with open(log_path, 'w', encoding='utf-8') as file:
            pass  # пустой файл

    def _create_user_folder(self):
        user_path = self._user_folder_path
        if not os.path.exists(user_path):
            os.makedirs(user_path)

    def _configure_logger(self):
        self._user_logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.__class__.CONSOLE_LOG_LVL)
        console_handler.setFormatter(formatter)

        user_log_path = os.path.join(self._user_folder_path, UserSettings.LOG_FILENAME)
        file_handler = logging.FileHandler(user_log_path, encoding='utf-8')
        file_handler.setLevel(self.__class__.FILE_LOG_LVL)
        file_handler.setFormatter(formatter)

        self._user_logger.addHandler(console_handler)
        self._user_logger.addHandler(file_handler)

    def _manage_history_list(self, history_list) -> list:
        history_list = copy.deepcopy(history_list)
        if history_list[0]['role'] != 'system':
            history_list.insert(0, self.__class__.DEFAULT_SYS_CONTENT)
        user_rank = self.config.get()["rank"]
        user_history_limit = int(BotConfig.get()["ranks"][user_rank]["history_messages_limit"])
        print(f"history limit: {user_history_limit}")
        while len(history_list) > user_history_limit and len(history_list) > 1:
            history_list.pop(1)  # Удаляем второй элемент чтобы освободить место с конца но и оставить инструкцию (0)
        return history_list

    @staticmethod
    def _read_json_from_file(path) -> Union[dict, list]:
        if not os.path.exists(path):
            raise Exception(f"Файл {path} не найден!")
        with open(path, 'r', encoding='utf-8') as file:
            json_content = json.load(file)
        return json_content

    @staticmethod
    def _write_json_to_file(path, json_content: Union[dict, list]):
        if not os.path.exists(path):
            raise Exception(f"Файл {path} не найден!")
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(json_content, file, indent=4, ensure_ascii=False)

    ############################################################
    # INNER CLASSES! #############################################
    class Log:
        FILENAME = UserSettings.LOG_FILENAME

        def __init__(self, user_instance):
            self.user_instance = user_instance

    class History:
        FILENAME = UserSettings.HISTORY_FILENAME
        DEFAULT_PROMPT = {"role": "system", "content": ""}

        def __init__(self, user_instance):
            self.user_instance = user_instance

        def get(self) -> list:
            hist_list
            return hist_list

        def write(self, history_list):
            pass

    class Config:
        FILENAME = UserSettings.CFG_FILENAME
        DEFAULT_VAL = {
            "id": None,
            "language": "ru",
            "rank": Ranks.BASIC,
            "is_admin": False,
            "is_blocked": False,
            "is_removed": False,
            "total_requests": 0,
            "total_tokens_spent": 0,
            "total_cost": 0,
            "today_requests": 0,
            "today_tokens_spent": 0,
            "today_cost": 0,
            "last_request_date": None,
            "default_preset": {"Обычный чат GPT": ""},
            "active_preset": {"Обычный чат GPT": ""},
            "instruction_presests": {
                "Обычный чат GPT": "",
                "Лаконичный чат GPT": "Отвечай коротко и по делу. Без воды, минимум текста.",
                "Точная статистика": "Твои ответы должны содержать подробную статистику и цифры. В удобном для понимания виде."
            },
        }

        def __init__(self, user_instance):
            self.user_instance = user_instance  # Сохраняем ссылку на User
            self._cfg_path = os.path.join(UserSettings.FOLDER_NAME, self.user_instance.id, self.__class__.FILENAME)

        def get(self) -> Union[dict, list]:
            return User._read_json_from_file(self._cfg_path)

        def write(self, cfg_dict: Union[dict, list]):
            return User._write_json_to_file(self._cfg_path, cfg_dict)


# для прямых тестов модуля
if __name__ == '__main__':
    test_conv_hist = [
        {"role": "user", "content": "Пример запроса пользователя"},
        {"role": "assistant", "content": "Пример ответа ИИ"}
    ]

    user = User('41242')
    user.reset()
    cfg = user.config.get()
    cfg["rank"] = Ranks.BASIC
    user.config.write(cfg)
    user.save_history(test_conv_hist*100)
    hst_len = len(user.get_history())
    print(hst_len)

