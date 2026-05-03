# -*- coding: utf-8 -*-

import os
import json
import logging
from pathlib import Path
from flask import Flask, request, jsonify
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from vk_api.upload import VkUpload

# ==================================================
#  ЗАГРУЗКА НАСТРОЕК ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ (Render)
# ==================================================
GROUP_TOKEN = os.environ.get('GROUP_TOKEN')
CONFIRMATION_CODE = os.environ.get('CONFIRMATION_CODE')
SECRET_KEY = os.environ.get('SECRET_KEY')
OPERATOR_ID = int(os.environ.get('OPERATOR_ID', 0))
REVIEW_LINK = os.environ.get('REVIEW_LINK', 'https://example.com')
REVIEW_LINK2 = os.environ.get('REVIEW_LINK2', 'https://vk.com/showlandarz')

# Определяем абсолютный путь к папке с картинками
BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / 'images'

# ==================================================
#  ДАННЫЕ УСЛУГ (новая структура: images — список путей)
# ==================================================
MAIN_SERVICES = {
    'birthday_1_4': [
        {
            'images': [
                'buba1.jpg',
                'buba2.jpg',
                'buba3.jpg'
            ],
            'text': '🧀 В ГОСТИ К ДОМОВЕНКУ 🧀\n\nСамый главный пушистый хулиган и его подруга мышка знают все о веселом празднике. Похулиганим вместе?\n\nВ программе вас ждут:\n⭐️ Путешествие по тропинке домового\n⭐️ Сладости от домовенка и гигантский сыр\n⭐️ Пазл-головоломка от Мышки \n⭐️ Сырные гонки и путешествие в мультик\n⭐️ Веселые танцы и многое другое \n\nСтоимость - 6000 рублей\n(1 час программы, 2 героя, музыкальное оформление, микрофоны, тематический реквизит, вынос тортика и общее фото)'
        },
        {
            'images': [
                'kot1.jpg',
                'kot2.jpg',
                'kot3.jpg'
            ],
            'text': '❤️ МЯУ-ПУТЕШЕСТВИЕ ❤️\n\nКоржик, Карамелька и Компот попадают на праздник и не знают, как вернуться домой. И только дети смогут им помочь…\n\nВ программе их ждут:\n⭐️ Знакомство с жителями Котополиса\n⭐️ Путешествие через кото-тоннель\n⭐️ Догонялки с папой-котиком \n⭐️ Рыбалка для маленьких друзей \n⭐️ Настоящий парк аттракционов \n⭐️ Веселая кото-карусель\n⭐️ Мяу-танцы и многое другое\n\nСтоимость:\n2 героя - 6000 рублей\n3 героя - 7500 рублей\n(Коржик, Карамелька и Компот)\n(1 час программы, тематическое музыкальное оформление, микрофоны, тематический реквизит, вынос тортика и общее фото)\n\nПосмотреть видео с программы можно в нашем актуальном: \nhttps://vk.com/narrative-213072049_87260'
        },
        {
            'images': [
                'edin1.jpg',
                'edin2.jpg',
                'edin3.jpg'
            ],
            'text': '💖 ПОТЕРЯННАЯ ПРИНЦЕССА ЕДИНОРОГОВ 💖 (VIP)\n\nВолшебная страна единорогов исчезает, потому что дети по всему миру перестают верить чудеса. Сможет ли именинница и ее друзья спасти волшебство и найти пропавшую много лет назад принцессу единорогов? А быть может, потерянная принцесса это она сама? \n\nВ программе: \n⭐ Знакомство с единорожкой Искоркой \n⭐ Путешествие по радужному мосту \n⭐ Сбор разбитого зеркала чудес \n⭐ Догонялки с единорожкой Соней \n⭐ Переправа по розовым облакам \n⭐ Танцы в долине мыльных пузырей \n⭐ Волшебное озеро желаний \n⭐️ Светящаяся шкатулка с кристаллами, зажечь которую сможет лишь именинница\n\nСтоимость - 6500 рублей (1 час) \n\nВ стоимость программы входит: \n📍Работа 2-х артистов в костюмах категории VIP \n📍Мощное музыкальное оборудование (колонка, микрофоны, тематическая музыка к каждой игре) \n📍Уникальная авторская программа и реквизит в тематике праздника\n📍 Торжественный вынос тортика \n📍Выезд в пределах города Арзамас'
        },
        {
            'images': [
                'xol1.jpg',
                'xol2.jpg',
                'xol3.jpg'
            ],
            'text': '❄️ ХОЛОДНОЕ СЕРДЦЕ ❄️\n\nПринцессы Эренделла приглашены на бал в честь дня рождения, но неожиданно волшебный голос вновь зовёт Эльзу… Сказка о четырех стихиях оживает вновь, детям предстоит зажечь все четыре магических кристалла, чтобы вернуть равновесие в волшебный мир.\n\nВас ждёт:\n⭐️ Светящаяся книга легенд волшебного королевства\n⭐️ Знакомство с настоящим Олафом\n\n⭐️ Волшебный портал в Эренделл\n⭐️ Создание ледяной стены\n\n⭐️ Гонки с оленем Свеном\n⭐️ Река памяти - Ахтохаллен\n⭐️ Светящиеся кристаллы стихий, которые загораются лишь в руках именинницы\n\nСтоимость - 6000 рублей\n(1 час программы, 2 героя, музыкальное оформление, тематический реквизит, вынос тортика и общее фото)\n\nКатающий олень Свен (10 мин + фото) - 2700 рублей'
        },
        {
            'images': [
                'slad1.jpg',
                'slad2.jpg',
                'slad3.jpg'
            ],
            'text': '💖 СЛАДКАЯ СКАЗКА 💖\n\nМистер и мисс Кенди знают все о сладостях! Но в сладком королевстве случилась беда… После взрыва на сладкой фабрике все идёт не так и только дети смогут помочь все исправить.\nЮных сладкоежек ждёт:\n⭐️ Сказочный портал в сладкую страну\n⭐️ Догонялки с гигантским пончиком\n⭐️ Восстановление карты королевства\n⭐️ Гигантский пломбир\n⭐️ Знакомство с жителем сладкой страны\n⭐️ Гонки на единорогах и гигантские чупа-чупсы\n\nСтоимость - 6500 рублей\n(1 час программы, 2 героя, музыкальное оформление, тематический реквизит, вынос тортика и общее фото)'
        },
        {
            'images': [
                'lab1.jpg',
                'lab2.jpg',
                'lab3.jpg'
            ],
            'text': '✨ ЛАБУБУ-МАНИЯ ✨\n\nЯркая новинка от агентства стильных праздников «Шоуленд»👇🏻\nЮные блогеры настоящие фанаты новой трендовой игрушки\nНо найти самую редкую коллекционную лабубу совсем не просто…\n\nСтиль, эстетика, тренды и веселье - можем и любим сочетать) \n\n🌟Тематический реквизит и яркие костюмы\n🌟Самые последние трендовые челенджи\n🌟Активности от блоггеров\n🌟Зажигательные танцы\nПродолжительность 1 час \nСтоимость \nза 2 героев:\nЛабубу + блоггер(девочка) 6500 р\nЗа 3 героев:\nЛабубу+2 блоггера (мальчик и девочка) 9000 р 🥰'
        },
    ],
    'birthday_5_7': [
        {
            'images': ['birthday_5_7_1.jpg'],
            'text': '🔍 Квест "Потерянные сокровища" – поиск клада.'
        },
        {
            'images': ['birthday_5_7_2.jpg'],
            'text': '🧪 Научное шоу с опытами и жидким азотом.'
        },
        {
            'images': ['birthday_5_7_3.jpg'],
            'text': '📸 Фотозона с костюмами и моментальные фото.'
        }
    ],
    'birthday_8_12': [
        {
            'images': ['birthday_8_12_1.jpg'],
            'text': '🔫 Лазертаг – 1 час, инструктор, снаряжение.'
        },
        {
            'images': ['birthday_8_12_2.jpg'],
            'text': '🥽 VR-зона – 30 минут виртуальной реальности.'
        },
        {
            'images': ['birthday_8_12_3.jpg'],
            'text': '💃 Дискотека с ведущим и светомузыкой.'
        }
    ],
    'class_1_4': [
        {
            'images': ['class_1_4_1.jpg'],
            'text': '🧱 Мастер-класс "Лего-конструирование" – 1 час.'
        },
        {
            'images': ['class_1_4_2.jpg'],
            'text': '🏛️ Интерактивная экскурсия в музей.'
        }
    ],
    'class_5_9': [
        {
            'images': ['class_5_9_1.jpg'],
            'text': '🧠 Интеллектуальный квиз "Что? Где? Когда?"'
        },
        {
            'images': ['class_5_9_2.jpg'],
            'text': '👔 Профориентационный тренинг.'
        },
        {
            'images': ['class_5_9_3.jpg'],
            'text': '🧗‍♂️ Тимбилдинг "Верёвочный курс".'
        }
    ]
}

EXTRA_SERVICES = [
    {
        'images': ['photo_service.jpg'],
        'text': '📸 Профессиональный фотограф на весь праздник (100+ фото).'
    },
    {
        'images': ['video_service.jpg'],
        'text': '🎥 Видеосъёмка с монтажом (3-минутный ролик).'
    },
    {
        'images': ['show_service.jpg'],
        'text': '🎭 Шоу мыльных пузырей или научное шоу (30 мин).'
    },
    {
        'images': ['candy_service.jpg'],
        'text': '🍭 Кенди-бар с cupcakes и печеньем.'
    }
]

# ==================================================
#  ИНИЦИАЛИЗАЦИЯ VK API (версия 5.199)
# ==================================================
vk_session = vk_api.VkApi(token=GROUP_TOKEN, api_version='5.199')
vk = vk_session.get_api()
upload = VkUpload(vk_session)

# ==================================================
#  КЛАВИАТУРЫ (те же самые)
# ==================================================
def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('📚 Программы', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_openlink_button('⭐ Оставить отзыв', link=REVIEW_LINK)
    keyboard.add_openlink_button('🥰 Наше сообщество', link=REVIEW_LINK2)
    keyboard.add_line()
    keyboard.add_button('📞 Связь с оператором', color=VkKeyboardColor.POSITIVE)
    return keyboard

def get_programs_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('🎂 Дни рождения', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🏫 Для классов', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('🛠 Доп. услуги', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('◀ Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_birthdays_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('👶 1-4 года', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🧒 5-7 лет', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('👦 8-12 лет', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('◀ Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_classes_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('📘 1-4 класс', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('📙 5-9 класс', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('◀ Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_item_actions_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('✅ Хочу заказать', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('🛠 Доп. услуги', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('◀ Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_extra_actions_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('✅ Хочу заказать', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('◀ Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_waiting_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('◀ Отмена', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_to_main_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('🏠 В главное меню', color=VkKeyboardColor.PRIMARY)
    return keyboard

# ==================================================
#  ФУНКЦИИ ОТПРАВКИ (с поддержкой нескольких картинок)
# ==================================================
def send_message(user_id, text, keyboard=None):
    try:
        vk.messages.send(
            user_id=user_id,
            message=text,
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard() if keyboard else None
        )
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

def send_images(user_id, image_paths, caption, keyboard):
    """
    Отправляет одно сообщение с несколькими фотографиями (до 10).
    image_paths: список путей к файлам (относительно IMAGES_DIR)
    """
    if not image_paths:
        send_message(user_id, caption, keyboard)
        return
    try:
        attachments = []
        for img_path in image_paths:
            full_path = str(IMAGES_DIR / img_path)
            photo = upload.photo_messages(full_path)[0]
            attachment = f"photo{photo['owner_id']}_{photo['id']}"
            attachments.append(attachment)
            # ВКонтакте разрешает не более 10 вложений в одном сообщении
            if len(attachments) >= 10:
                break
        attachment_str = ','.join(attachments)
        vk.messages.send(
            user_id=user_id,
            attachment=attachment_str,
            message=caption,
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard() if keyboard else None
        )
    except Exception as e:
        print(f"Ошибка отправки картинок {image_paths}: {e}")
        send_message(user_id, "❌ Не удалось загрузить картинки.\n" + caption, keyboard)

def send_to_operator(text):
    try:
        vk.messages.send(
            user_id=OPERATOR_ID,
            message=text,
            random_id=get_random_id()
        )
    except Exception as e:
        print(f"Ошибка отправки оператору: {e}")

# ==================================================
#  ФУНКЦИИ ПОКАЗА УСЛУГ
# ==================================================
def show_main_services(user_id, category_key):
    services = MAIN_SERVICES.get(category_key, [])
    if not services:
        send_message(user_id, 'В этой категории пока нет программ.', get_item_actions_keyboard())
        return
    for service in services:
        send_images(user_id, service['images'], service['text'], get_item_actions_keyboard())

def show_extra_services(user_id):
    for service in EXTRA_SERVICES:
        send_images(user_id, service['images'], service['text'], get_extra_actions_keyboard())

# ==================================================
#  ОСНОВНАЯ ЛОГИКА (хранилище состояний)
# ==================================================
user_stack = {}
user_temp = {}

# ==================================================
#  FLASK — ВЕБ-СЕРВЕР ДЛЯ ПРИЁМА ЗАПРОСОВ ОТ ВК
# ==================================================
app = Flask(__name__)

@app.route('/', methods=['POST'])
def handle_webhook():
    data = request.get_json()
    if data.get('type') == 'confirmation':
        return CONFIRMATION_CODE
    if data.get('secret') != SECRET_KEY:
        return 'ok', 200
    if data.get('type') == 'message_new':
        process_event(data['object'])
    return 'ok', 200

def process_event(event):
    user_id = event['message']['from_id']
    if user_id < 0:
        return
    raw_text = event['message']['text']
    user_message = raw_text.lower().strip()

    if user_id not in user_stack:
        user_stack[user_id] = ['main']
    current_state = user_stack[user_id][-1]

    # --- ГЛОБАЛЬНЫЕ КОМАНДЫ ---
    if user_message == 'привет':
        user_stack[user_id] = ['main']
        user_temp.pop(user_id, None)
        send_message(user_id, '🤗 Добро пожаловать! Выберите раздел с помощью кнопок ниже', get_main_keyboard())
        return

    if user_message in ['📞 связь с оператором', 'связь с оператором']:
        user_link = f"https://vk.com/id{user_id}"
        send_to_operator(f"🔔 Пользователь {user_link} хочет связаться с оператором.")
        send_message(user_id, "✅ Оператор скоро свяжется с вами. Ожидайте.", get_main_keyboard())
        user_stack[user_id] = ['main']
        user_temp.pop(user_id, None)
        return

    # --- РЕЖИМ ОЖИДАНИЯ АНКЕТЫ ---
    if current_state == 'waiting_order_text':
        if user_message in ['◀ отмена', 'отмена']:
            user_stack[user_id].pop()
            user_temp.pop(user_id, None)
            send_message(user_id, 'Заказ отменён.', get_main_keyboard())
            return
        send_message(user_id, "Отлично! Направляю вашу заявку оператору, подождите совсем немного 🤗.", get_to_main_keyboard())
        user_link = f"https://vk.com/id{user_id}"
        send_to_operator(f"💰 НОВЫЙ ЗАКАЗ от {user_link}\n Сообщение: {raw_text}")
        user_stack[user_id].append('order_completed')
        user_temp.pop(user_id, None)
        return

    # --- ПОСЛЕ ЗАКАЗА ---
    if current_state == 'order_completed':
        if user_message in ['🏠 в главное меню', 'в главное меню']:
            user_stack[user_id] = ['main']
            send_message(user_id, '⭐ Главное меню', get_main_keyboard())
        else:
            send_message(user_id, 'Используйте кнопку "В главное меню".', get_to_main_keyboard())
        return

    # --- ОБРАБОТКА КНОПКИ "НАЗАД" ---
    if user_message in ['◀ назад', 'назад'] and len(user_stack[user_id]) > 1:
        user_stack[user_id].pop()
        new_state = user_stack[user_id][-1]
        if new_state == 'main':
            send_message(user_id, 'Пожалуйста, выберите, что вы хотели бы сделать', get_main_keyboard())
        elif new_state == 'programs':
            send_message(user_id, 'Какая программа вам нужна? ⚡', get_programs_keyboard())
        elif new_state == 'birthdays':
            send_message(user_id, 'Теперь давайте выберем возраст 🔥', get_birthdays_keyboard())
        elif new_state == 'classes':
            send_message(user_id, 'Теперь давайте выберем класс 🔥', get_classes_keyboard())
        elif new_state == 'viewing_main':
            send_message(user_id, 'Выберите действие', get_item_actions_keyboard())
        elif new_state == 'viewing_extra':
            send_message(user_id, 'Выберите действие', get_extra_actions_keyboard())
        return

    if user_message in ['◀ назад', 'назад'] and len(user_stack[user_id]) == 1:
        send_message(user_id, 'Вы уже в главном меню.', get_main_keyboard())
        return

    # --- НАВИГАЦИЯ ПО МЕНЮ ---
    if current_state == 'main':
        if user_message in ['📚 программы', 'программы']:
            user_stack[user_id].append('programs')
            send_message(user_id, 'Давайте выберем категорию', get_programs_keyboard())
    elif current_state == 'programs':
        if user_message in ['🎂 дни рождения', 'дни рождения']:
            user_stack[user_id].append('birthdays')
            send_message(user_id, 'Теперь давайте выберем возраст 🔥', get_birthdays_keyboard())
        elif user_message in ['🏫 для классов', 'для классов']:
            user_stack[user_id].append('classes')
            send_message(user_id, 'Теперь давайте выберем класс 🔥', get_classes_keyboard())
        elif user_message in ['🛠 доп. услуги', 'доп. услуги']:
            user_stack[user_id].append('viewing_extra')
            show_extra_services(user_id)
    elif current_state == 'birthdays':
        if user_message == '👶 1-4 года':
            user_stack[user_id].append('viewing_main')
            user_temp[user_id] = {'category': 'birthday_1_4'}
            show_main_services(user_id, 'birthday_1_4')
        elif user_message == '🧒 5-7 лет':
            user_stack[user_id].append('viewing_main')
            user_temp[user_id] = {'category': 'birthday_5_7'}
            show_main_services(user_id, 'birthday_5_7')
        elif user_message == '👦 8-12 лет':
            user_stack[user_id].append('viewing_main')
            user_temp[user_id] = {'category': 'birthday_8_12'}
            show_main_services(user_id, 'birthday_8_12')
    elif current_state == 'classes':
        if user_message == '📘 1-4 класс':
            user_stack[user_id].append('viewing_main')
            user_temp[user_id] = {'category': 'class_1_4'}
            show_main_services(user_id, 'class_1_4')
        elif user_message == '📙 5-9 класс':
            user_stack[user_id].append('viewing_main')
            user_temp[user_id] = {'category': 'class_5_9'}
            show_main_services(user_id, 'class_5_9')
    elif current_state == 'viewing_main':
        if user_message in ['✅ хочу заказать', 'хочу заказать']:
            user_temp[user_id]['prev_state'] = current_state
            user_stack[user_id].append('waiting_order_text')
            send_message(
                user_id,
                '🔥Осталось совсем чуть-чуть! Заполните небольшую анкету и пришлите её прямо сюда 📌 \n\n'
                '1) На какие даты рассчитываете проведение праздника? 📅 \n'
                '2) Для кого планируется праздник? (Имя, возраст) 🎆 \n'
                '3) Сколько гостей и какого возраста планируется на празднике? 👫\n'
                '4) Нужно ли в конце программы делать торжественный вынос тортика? 🎂 \n'
                '5) Место проведения праздника, адрес? 🙂 \n'
                '6) Ваш контактный номер телефона? 📞 \n'
                '7) Есть ли какие-либо дополнительные комментарии ? 📝\n\n',
                get_waiting_keyboard()
            )
        elif user_message in ['🛠 доп. услуги', 'доп. услуги']:
            user_temp[user_id]['prev_state'] = current_state
            user_stack[user_id].append('viewing_extra')
            show_extra_services(user_id)
    elif current_state == 'viewing_extra':
        if user_message in ['✅ хочу заказать', 'хочу заказать']:
            user_temp[user_id]['prev_state'] = current_state
            user_stack[user_id].append('waiting_order_text')
            send_message(
                user_id,
                '🔥Осталось совсем чуть-чуть! Заполните небольшую анкету и пришлите её прямо сюда 📌 \n\n'
                '1) На какие даты рассчитываете проведение праздника? 📅 \n'
                '2) Для кого планируется праздник? (Имя, возраст) 🎆 \n'
                '3) Сколько гостей и какого возраста планируется на празднике? 👫\n'
                '4) Нужно ли в конце программы делать торжественный вынос тортика? 🎂 \n'
                '5) Место проведения праздника, адрес? 🙂 \n'
                '6) Ваш контактный номер телефона? 📞 \n'
                '7) Есть ли какие-либо дополнительные комментарии ? 📝\n\n',
                get_waiting_keyboard()
            )
    # Любое другое сообщение игнорируется

@app.route('/', methods=['GET'])
def handle_health_check():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
