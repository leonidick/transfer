import os
import gc
import shutil
import telebot
import zipfile
import magic
import glob
from PIL import Image
from tools.image import ImageProcessor
from tools.database import DataBaseController, UserNotFoundException

token = '5577792621:AAEkVhfKReVZIzJl7j0YXU55kCeuOOKzz3c'
bot = telebot.TeleBot(token)
DEFAULT_MARK = 'BELARUSIAN COSMETIKS'

root = os.path.dirname(os.path.abspath(__file__))
tmp = os.path.join(root, 'tmp')
nouser = os.path.join(root, 'tools', 'nouser.tgs')
work = os.path.join(root, 'tools', 'work.tgs')

INSERT_BUTTON_TEXT = 'Добавить метку'
DETECT_BUTTON_TEXT = 'Распознать метку'

def check_user(message):
    controller = DataBaseController()
    telegram_id = message.from_user.id
    telegram_id_list = [
            entry[1]
                for entry in controller.user_list()
    ]
    user_exist = str(telegram_id) in telegram_id_list
    
    if not user_exist:
        with open(nouser, 'rb') as sticker:
            bot.send_sticker(
                message.chat.id,
                sticker
            )
        bot.send_message(
                message.chat.id,
                'Вас нет в базе данных.\n' + \
                'Обратитесь к системному администратору.\n' + \
                'Ваш Telegram ID: {}\n'.format(telegram_id) + \
                'После того как Вас добавят в базу данных, напишите /help ' + \
                'для просмотра мануала.'
        )
    return user_exist

def get_mark(message):
    controller = DataBaseController()
    telegram_id = message.from_user.id
    id_mark_list = [
        (entry[1], entry[3])
            for entry in controller.user_list()
    ]
    for entry in id_mark_list:
        if entry[0] == str(telegram_id):
            mark = entry[1]
            if mark == None:
                return DEFAULT_MARK
            return mark
            



@bot.message_handler(commands = ['start'])
def start(message):
    if not check_user(message):
        return
    
    bot.reply_to(
        message,
        'Привет! Вы есть в базе данных! Для просмотра манула напишите /help.'
    )

@bot.message_handler(commands = ['help'])
def help(message):
    if not check_user(message):
        return

    answer = 'Я - Бот. Я добавляю скрытый водяной знак в изображения.\n' + \
             'Отправь мне архив и я добавлю метку во все изображения в нём.\n' + \
             'Отправь мне изображение документом и я смогу добавить в него метку ' + \
             'либо распознать её там.\n\n' + \
             'Команды:\n' + \
             '/help - показать мануал\n' + \
             '/info - показать текущую метку\n' + \
             '/set - установить новую метку (не влияет на других пользователей)\n' + \
             '/reset - установить метку по умолчанию (не влияет на других пользователей)'
    bot.reply_to(
        message,
        answer
    )

@bot.message_handler(content_types = ['photo'])
def photo(message):
    if not check_user(message):
        return

    answer = \
        'Чтобы я добавил метку в изображение или попытался её там распознать, ' + \
        'нужно скинуть его без сжатия. Если вы пользуетесь мной с телефона, ' + \
        'то загрузите фото документом. Если вы пользуетесь мной с компьютера, ' + \
        'то перед загрузкой изображения уберите галочку напротив "Сжать изображение".'
    bot.reply_to(
        message,
        answer
    )

def image_next_step_handler(message, file_path, mark, mime_type):
    if message.text != INSERT_BUTTON_TEXT and message.text != DETECT_BUTTON_TEXT:
        bot.reply_to(
            message,
            text = 'Неизвестная команда.',
            reply_markup = telebot.types.ReplyKeyboardRemove()
        )
        return

    bot.reply_to(
        message,
        text = 'Принято!',
        reply_markup = telebot.types.ReplyKeyboardRemove()
    )
    with open(work, 'rb') as sticker:
        bot.send_sticker(
            message.chat.id,
            sticker
        )
    
    with Image.open(file_path) as image:
        os.remove(file_path)

        if message.text == INSERT_BUTTON_TEXT:
            image = ImageProcessor.insert_mark(image, mark)
            image.save(
                file_path,
                format = mime_type.split('/')[-1],
                quality = 100,
                subsampling = 0
            )
            
            with open(file_path, 'rb') as response:
                bot.send_document(
                    message.chat.id,
                    response,
                    caption = 'Метка \'{}\' добавлена.'.format(mark)
                )
            os.remove(file_path)
            return

        if message.text == DETECT_BUTTON_TEXT:
            has_mark = ImageProcessor.detect_mark(image, mark)
            image.save(
                file_path,
                format = mime_type.split('/')[-1],
                quality = 100,
                subsampling = 0
            )

            with open(file_path, 'rb') as response:
                bot.send_photo(
                    message.chat.id,
                    response,
                    caption = 'Метка \'{}\' {}.' \
                        .format(mark, 'обнаружена' if has_mark else 'НЕ обнаружена')
                )
            os.remove(file_path)
            return

def document_processing(message):
    userdir = os.path.join(tmp, str(message.from_user.id))
    make_clear_dir(userdir)
    mark = get_mark(message)
 
    def download_file(file_id):
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        return file

    mime_type = message.document.mime_type
    if mime_type == 'image/jpeg' or mime_type == 'image/png':
        # download file
        telegram_file = download_file(message.document.file_id)
        telegram_file_name = message.document.file_name
        
        # write downloaded file to disk
        file_path = os.path.join(userdir, telegram_file_name)
        with open(file_path, 'wb') as file:
            file.write(telegram_file)
        
        def make_keyboard():
            insert_button = telebot.types.KeyboardButton(text = INSERT_BUTTON_TEXT)
            detect_button = telebot.types.KeyboardButton(text = DETECT_BUTTON_TEXT)
            keyboard = telebot.types.ReplyKeyboardMarkup(
                one_time_keyboard = True,
                resize_keyboard = True
            )
            keyboard.add(insert_button)
            keyboard.add(detect_button)
            return keyboard
             
        bot_message = bot.reply_to(
            message,
            'Выберите действие.',
            reply_markup = make_keyboard()
        )
               
        bot.register_next_step_handler(
            bot_message,
            image_next_step_handler,
            file_path,
            mark,
            mime_type
        )

        return

    if mime_type == 'application/zip':
        with open(work, 'rb') as sticker:
            bot.send_sticker(
                message.chat.id,
                sticker
            )

        # downlaod file
        telegram_file = download_file(message.document.file_id)
        telegram_file_name = message.document.file_name

        file_path = os.path.join(userdir, telegram_file_name)
        with open(file_path, 'wb') as file:
            file.write(telegram_file)

        with zipfile.ZipFile(file_path, mode = 'r') as zip_file:
            os.remove(file_path)
            zip_file.extractall(userdir)
            exctract_namelist = glob.iglob(
                os.path.join(userdir, '**/*'),
                recursive = True)
            for name in exctract_namelist:
                if os.path.isdir(name):
                    continue
                mime = lambda path: magic.from_file(path, mime = True)
                if mime(name) != 'image/jpeg' and mime(name) != 'image/png':
                    continue

                with Image.open(name) as image:
                    image_format = mime(name).split('/')[-1]
                    os.remove(name)
                    image = ImageProcessor.insert_mark(image, mark)
                    image.save(
                        name,
                        image_format,
                        quality = 100,
                        subsampling = 0
                    )

        with zipfile.ZipFile(file_path, mode = 'w') as zip_file:
            namelist = glob.iglob(
                os.path.join(userdir, '**/*'),
                recursive = True
            )
            for name in namelist:
                if os.path.isdir(name):
                    continue
                mime = lambda path: magic.from_file(path, mime = True)
                if mime(name) != 'image/jpeg' and mime(name) != 'image/png':
                    continue
                arcname = str(name).replace(userdir, '')
                zip_file.write(name, arcname = arcname)

        with open(file_path, 'rb') as response:
            bot.send_document(
                message.chat.id,
                response,
            )

        return
    
    bot.reply_to(
        message,
        'Неизвестный формат файла.\n' + \
        'Я работаю только с zip архивами и .jpg .jpeg .png изображениями.'
    )

@bot.message_handler(content_types = ['document'])
def document(message):
    if not check_user(message):
        return

    try:
        document_processing(message)
    except Exception as ex:
        bot.send_message(
            message.chat.id,
            str(ex)
        )
    # gc.collect()

def set_mark(message, mark):
    controller = DataBaseController()
    controller.user_update_mark(message.from_user.id, mark)

def set_mark_next_step_handler(message):
    try:
        set_mark(message, message.text)
        bot.reply_to(
            message,
            'Метка \'{}\' установлена.'.format(get_mark(message))
        )
    except UserNotFoundException as ex:
        bot.reply_to(
            message,
            str(ex)
        )

@bot.message_handler(commands = ['set'])
def set(message):
    bot_message = bot.reply_to(
        message,
        'Введите метку'
    )
    bot.register_next_step_handler(
        bot_message,
        set_mark_next_step_handler
    )

@bot.message_handler(commands = ['reset'])
def reset(message):
    set_mark(message, DEFAULT_MARK)
    bot.reply_to(
        message,
        'Метка сброшена. Ваша метка: \'{}\'.'.format(get_mark(message))
    )

@bot.message_handler(commands = ['info'])
def info(message):
    bot.reply_to(
        message,
        'Ваша текущая метка: \'{}\'.'.format(get_mark(message))
    )

def make_clear_dir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.mkdir(path)

def main():
    # create clear './tmp' dir
    gc.set_threshold(10, 1, 1)
    make_clear_dir(tmp)

    bot.polling(non_stop = True, interval = 0)

if __name__ == '__main__':
    main()

