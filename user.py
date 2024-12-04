import json
import logging
import os
import re
import shutil
import time

class User:
    """
    Класс для управления записями пользователей, регистрации, сохранения истории,
    конфигурации, логов и тд.
    """
    USERS_FOLDER_NAME = "users"
    USER_LOG_FN = 'user.log'
    USER_CHAT_HISTORY_FN = 'history.json'
    USER_CFG_FN = 'user.cfg'

    CONSOLE_LOG_LVL = logging.DEBUG
    FILE_LOG_LVL = logging.INFO

    DEFAULT_SYS_CONTENT = {"role": "system", "content": ""}
    HISTORY_LIMIT = 10

    def __init__(self, chat_id):
        self.is_admin = False
        self.is_blocked = False
        self.is_removed = False
        self.is_unlimited = False
        self.is_strictly_limited = False

        self.id = chat_id
        self.user_chat_id = chat_id  # оставим для обратной совместимости
        self.user_folder_name = chat_id
        self.user_folder_path = self.__class__.USERS_FOLDER_NAME + '/' + self.user_folder_name
        self._create_users_folder()

        if self.is_new_user(self.id):
            self._create_user_folder()
            self._create_user_cfg()
            self._create_user_log()
            self._create_user_history()
            self._set_default_history()

        # после того как файл точно создан
        self._user_logger = logging.getLogger('USERLOG_' + self.user_chat_id)
        self._configure_logger()

    # ---------------------------
    # МЕТОДЫ ЭКЗЕМПЛЯРА
    # ---------------------------

    def set_gpt_prompt(self, prompt_text):
        hst = self.get_history()
        system_content = hst[0]
        if 'role' not in system_content or  system_content['role'] != 'system':
            self.error(f"Ошибка в функции {set_gpt_prompt.__name__}: 'role' not in system_content or  system_content['role'] != 'system'")
        hst[0]['content'] = prompt_text
        self.save_history(hst)

    def reset(self):
        files_to_delete = [
            self.__class__.USER_LOG_FN,
            self.__class__.USER_CHAT_HISTORY_FN,
            self.__class__.USER_CFG_FN
        ]
        for file_name in files_to_delete:
            if os.path.exists(file_name):
                os.remove(self.user_folder_path + '/' + file_name)

        self._create_user_folder()
        self._create_user_cfg()
        self._create_user_log()
        self._create_user_history()
        self._set_default_history()
        self._reset_all_flags()

    def remove(self):
        # cначала надо отвязать все handlers логгера
        for handler in self._user_logger.handlers[:]:  # Итерируем по копии списка, чтобы безопасно удалять
            if isinstance(handler, logging.FileHandler):  # Проверяем, является ли обработчик FileHandler
                self._user_logger.removeHandler(handler)
                handler.close()
        folder_path = self.__class__.USERS_FOLDER_NAME + '/' + self.id
        shutil.rmtree(folder_path)
        self.is_removed = True

    # в формате массива [ {"role": "assistant", "content": reply}, ]
    def save_history(self, conv_history: list):
        managed_hist = self._manage_history_list(conv_history) # автоочистка истории c сохранением 0 элемента (system content)
        file_path = self.user_folder_path + '/' + self.__class__.USER_CHAT_HISTORY_FN
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(managed_hist, json_file, indent=4, ensure_ascii=False)

    def get_history(self) -> list:
        file_path = self.user_folder_path + '/' + self.__class__.USER_CHAT_HISTORY_FN
        if self._is_file_empty(file_path):
            return []
        with open(file_path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)

    def clear_history(self):
        file_path = self.user_folder_path + '/' + self.__class__.USER_CHAT_HISTORY_FN
        with open(file_path, 'w', encoding='utf-8') as json_file:
            pass

    def debug(self, text):
        self._user_logger.debug(text)

    def info(self, text):
        self._user_logger.info(text)

    def error(self, text):
        self._user_logger.error(text)

    def clear_log_file(self):
        file_path = self.user_folder_path + '/' + self.__class__.USER_LOG_FN
        with open(file_path, 'w', encoding='utf-8') as json_file:
            pass

    # ---------------------------
    # МЕТОДЫ КЛАССА
    # ---------------------------
    @classmethod
    def _create_users_folder(cls):
        main_folder = cls.USERS_FOLDER_NAME
        if not os.path.exists(main_folder):
            os.makedirs(main_folder)

    @classmethod
    def is_new_user(cls, chatid: str):
        user_path = cls.USERS_FOLDER_NAME + '/' + chatid
        if not os.path.exists(user_path):
            return True

    @staticmethod
    def _is_file_empty(path):
        return os.stat(path).st_size == 0

    # ---------------------------
    # ПРИВАТНЫЕ МЕТОДЫ
    # ---------------------------
    def _set_default_history(self):
        self.clear_history()
        file_path = self.user_folder_path + '/' + self.__class__.USER_CHAT_HISTORY_FN
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump([self.__class__.DEFAULT_SYS_CONTENT], json_file, indent=4, ensure_ascii=False)

    def _create_user_cfg(self):
        def_user_cfg = {
            "user": {
                "chat_id": self.id,
                "models": ["gpt-4o-mini"],
                "preferences": {"language": "ru"},
                "gpt_instructions": ""
            }
        }
        with open(f'{User.USERS_FOLDER_NAME}/{self.user_folder_name}/{self.__class__.USER_CFG_FN}', 'w', encoding='utf-8') as config_file:
            json.dump(def_user_cfg, config_file, indent=4, ensure_ascii=False)

    def _create_user_history(self):
        user_path = User.USERS_FOLDER_NAME + '/' + self.user_chat_id
        file_path = os.path.join(user_path, self.__class__.USER_CHAT_HISTORY_FN)
        with open(file_path, 'w', encoding='utf-8') as file:
            pass  # пустой файл

    def _create_user_log(self):
        user_path = User.USERS_FOLDER_NAME + '/' + self.user_chat_id
        file_path = os.path.join(user_path, self.__class__.USER_LOG_FN)
        with open(file_path, 'w', encoding='utf-8') as file:
            pass  # пустой файл

    def _create_user_folder(self):
        user_path = self.__class__.USERS_FOLDER_NAME + '/' + self.user_chat_id
        if not os.path.exists(user_path):
            os.makedirs(user_path)

    def _configure_logger(self):
        self._user_logger.setLevel(logging.DEBUG)  # Устанавливаем уровень логирования
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.__class__.CONSOLE_LOG_LVL)
        console_handler.setFormatter(formatter)

        file_handler = logging.FileHandler(self.user_folder_path + '/' + self.__class__.USER_LOG_FN, encoding='utf-8')
        file_handler.setLevel(self.__class__.FILE_LOG_LVL)
        file_handler.setFormatter(formatter)

        self._user_logger.addHandler(console_handler)
        self._user_logger.addHandler(file_handler)

    def _manage_history_list(self, history_list) -> list:
        history_list = history_list.copy()
        system_content = self.get_history()[0]
        if 'role' not in system_content or system_content['role'] != 'system':
            history_list.insert(0, self.__class__.DEFAULT_SYS_CONTENT)
        while len(history_list) > self.__class__.HISTORY_LIMIT:
            history_list.pop(1)  # Удаляем второй элемент чтобы освободить место с конца но и оставить инструкцию (0)
        return history_list

    def _reset_all_flags(self):
        self.is_admin = False
        self.is_blocked = False
        self.is_removed = False
        self.is_unlimited = False
        self.is_strictly_limited = False

# для прямых тестов модуля
if __name__ == '__main__':
    test_conv_hist = [
        {"role": "user", "content": "Пример запроса пользователя"},
        {"role": "assistant", "content": "Пример ответа ИИ"}
    ]

    user = User('41242')
    user.reset()
    user.info("Данные пользователя сброшены")
    user.set_gpt_prompt("Отвечай лаконично и без лишнего текста.")
    time.sleep(10)
    user.remove()
