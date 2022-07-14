import psycopg2
from psycopg2.errorcodes import UNIQUE_VIOLATION
from psycopg2 import errors
from tabulate import tabulate

class MyException(Exception):
    pass

class UserAlreadyExistException(MyException):
    def __init__(self, reason):
        message = 'Пользователь с таким Telegram ID ' + \
                'и/или описанием уже существует.\nОшибка: '
        super().__init__(message + reason)

class UserNotFoundException(MyException):
    def __init__(self):
        message = 'Пользователь с таким ID не найден.'
        super().__init__(message)

class DataBaseController:
    def __init__(self):
        self.connection = psycopg2.connect(
                dbname = 'telegrambotdb',
                user = 'leonidpsql',
                password = 'password',
                host = 'localhost',
                port = '5432'
        )
        self.connection.autocommit = True
        self.cursor = self.connection.cursor()
    
    class User:
        def __init__(self, telegram_id, description):
            self.telegram_id = telegram_id
            self.description = description

    def user_add(self, user):
        telegram_id_value = '\'' + str(user.telegram_id) + '\''
        description_value = '\'' + str(user.description) + '\''
        
        execute = \
                '''
                INSERT INTO users (telegram_id, description)
                VALUES ({}, {})
                '''.format(telegram_id_value, description_value)
        try:
            self.cursor.execute(execute)
        except errors.lookup(UNIQUE_VIOLATION) as ex:
            reason = ex.pgerror.split('DETAIL:')[1].strip()
            raise UserAlreadyExistException(reason)

    def user_list(self):
        execute = \
                '''
                SELECT * FROM users
                '''
        self.cursor.execute(execute)
        return self.cursor.fetchall()

    def user_delete(self, id):
        execute = \
                '''
                DELETE FROM USERS WHERE id={}
                '''.format(id)
        self.cursor.execute(execute)
        if self.cursor.rowcount == 0:
            raise UserNotFoundException()

    def user_update_mark(self, telegram_id, mark):
        telegram_id_value = '\'' + str(telegram_id) + '\''
        mark_value = '\'' + str(mark) + '\''

        execute = \
                '''
                UPDATE users SET mark = {} WHERE telegram_id = {};
                '''.format(mark_value, telegram_id_value)
        self.cursor.execute(execute)
        if self.cursor.rowcount == 0:
            raise UserNotFoundException()
        

class WrongCommandException(MyException):
    def __init__(self):
        message = 'Неверная комманда или её формат. ' + \
                  'Напишите \'help\' без кавычек для ' + \
                  'просмотра мануала.'
        super().__init__(message)

class CommandProcessor:
    def __init__(self, database_controller, print_output):
        self.controller = database_controller
        self.output = print_output
    
    # add {Telegram ID} {description}
    # add 123456789 IvanUzda
    def __add(self, command_list):
        if len(command_list) != 3:
            raise WrongCommandException()
        telegram_id = command_list[1]
        description = command_list[2]
        user = DataBaseController.User(telegram_id, description)
        self.controller.user_add(user)

    def __list(self, command_list):
        if len(command_list) != 1:
            raise WrongCommandException()
        user_list = [
            entry[0:3]
                for entry in self.controller.user_list()
        ]
        if len(user_list) == 0:
            output_msg = 'Таблица пользователей пуста.'
        else:
            output_msg = tabulate(
                    user_list,
                    headers = ['ID', 'Telegram ID', 'Описание']
            )

        self.output(output_msg)

    def __delete(self, command_list):
        if len(command_list) != 2:
            raise WrongCommandException()
        id = command_list[1]
        if not id.isdigit():
            raise WrongCommandException()
        self.controller.user_delete(id)

    def __help(self, command_list):
        if len(command_list) != 1:
            raise WrongCommandException()
        man = [
            ['\'help\'',
             'Показать мануал.',
              'help'],
            ['\'add {Telegram ID} {Описание}\'',
             'Добавить пользователя в таблицу.',
             'add 1015167666 Ivan'],
            ['\'list\'',
             'Посмотреть таблицу пользователей.',
             'list'],
            ['\'delete {ID}\'',
             'Удалить пользователя с id={ID}.',
             'delete 12'],
            ['\'exit\'',
             'Выйти из приложения.',
             'exit']
        ]
        output_msg = tabulate(man, headers = ['Формат команды', 'Описание', 'Пример'])
        self.output(output_msg)

    def process(self, command):
        if not command:
            return

        command_list = command.split()
        action = command_list[0]
        
        match action:
            case 'add':
                self.__add(command_list)
            case 'list':
                self.__list(command_list)
            case 'delete':
                self.__delete(command_list)
            case 'help':
                self.__help(command_list)
            case _:
                raise WrongCommandException()

        pass


def main():
    controller = DataBaseController()
    print(controller.telegram_id_list())
    '''
    processor = CommandProcessor(controller, print)
    
    while (command := input('> ')) != 'exit':
        try:
            processor.process(command)
        except MyException as ex:
            print(ex)
    '''


if __name__ == '__main__':
    main()


