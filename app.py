# -*- coding: utf-8 -*-

import os
import json
import time
import logging
from pathlib import Path
from flask import Flask, request
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

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / 'images'
SERVICES_FILE = BASE_DIR / 'services.json'

# ==================================================
#  ЗАГРУЗКА ДАННЫХ ИЗ JSON
# ==================================================
def load_services():
    try:
        with open(SERVICES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['main'], data['extra']
    except FileNotFoundError:
        logging.error(f"Файл {SERVICES_FILE} не найден! Бот не может работать.")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка парсинга JSON: {e}")
        raise

MAIN_SERVICES, EXTRA_SERVICES = load_services()

# ==================================================
#  ИНИЦИАЛИЗАЦИЯ VK API (с таймаутом)
# ==================================================
vk_session = vk_api.VkApi(
    token=GROUP_TOKEN,
    api_version='5.199',
    timeout=10  # таймаут 10 секунд на каждый запрос
)
vk = vk_session.get_api()
upload = VkUpload(vk_session)

# ==================================================
#  ПРЕДЗАГРУЗКА КАРТИНОК
# ==================================================
def preload_attachments(data):
    if isinstance(data, dict):
        if 'images' in data:
            attachments = []
            for img in data['images']:
                full_path = IMAGES_DIR / img
                if not full_path.exists():
                    logging.warning(f"Файл не найден: {full_path}")
                    continue
                try:
                    photo = upload.photo_messages(str(full_path))[0]
                    attachments.append(f"photo{photo['owner_id']}_{photo['id']}")
                except Exception as e:
                    logging.error(f"Ошибка загрузки {img}: {e}", exc_info=True)
            data['attachments'] = attachments
            del data['images']
        else:
            for v in data.values():
                preload_attachments(v)
    elif isinstance(data, list):
        for item in data:
            preload_attachments(item)

print("🖼️ Предзагрузка картинок...")
preload_attachments(MAIN_SERVICES)
preload_attachments(EXTRA_SERVICES)
print("✅ Все картинки загружены.")

# ==================================================
#  КЛАВИАТУРЫ (без изменений)
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
    keyboard.add_button('❓ У меня индивидуальный запрос', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('◀ Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_item_actions_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('✅ Хочу заказать', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('🛠 Доп. услуги', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('📞 Связь с оператором', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('◀ Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_extra_categories_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('🎨 Мастер-классы', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('💃 Дискотека', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('➕ Ещё', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('◀ Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_extra_actions_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('✅ Хочу заказать', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('📞 Связь с оператором', color=VkKeyboardColor.PRIMARY)
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

def get_programs_choice_keyboard(services):
    """Динамическая клавиатура из названий программ (3 кнопки в строке)"""
    keyboard = VkKeyboard(one_time=True)
    for i, service in enumerate(services):
        title = service.get('title')
        if not title:
            text = service.get('text', '')
            if text:
                title = text[:30] + '…'
            else:
                title = "Без названия"
        keyboard.add_button(title, color=VkKeyboardColor.PRIMARY)
        if (i + 1) % 3 == 0 and i != len(services) - 1:
            keyboard.add_line()
    keyboard.add_line()
    keyboard.add_button('◀ Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_extra_choice_keyboard(services):
    keyboard = VkKeyboard(one_time=True)
    for i, service in enumerate(services):
        title = service.get('title')
        if not title:
            title = "Услуга"
        keyboard.add_button(title, color=VkKeyboardColor.PRIMARY)
        if (i + 1) % 3 == 0 and i != len(services) - 1:
            keyboard.add_line()
    keyboard.add_line()
    keyboard.add_button('◀ Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

# ==================================================
#  ФУНКЦИИ ОТПРАВКИ С ПОВТОРНЫМИ ПОПЫТКАМИ
# ==================================================
def send_message(user_id, text, keyboard=None, retries=3):
    for attempt in range(retries):
        try:
            vk.messages.send(
                user_id=user_id,
                message=text,
                random_id=get_random_id(),
                keyboard=keyboard.get_keyboard() if keyboard else None
            )
            return
        except Exception as e:
            logging.error(f"Ошибка отправки сообщения (попытка {attempt+1}): {e}", exc_info=True)
            if attempt < retries - 1:
                time.sleep(1)
            else:
                logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {text[:50]}...")

def send_attachments(user_id, attachments, caption, keyboard, retries=3):
    if not attachments:
        send_message(user_id, caption, keyboard)
        return
    attachment_str = ','.join(attachments)
    for attempt in range(retries):
        try:
            vk.messages.send(
                user_id=user_id,
                attachment=attachment_str,
                message=caption,
                random_id=get_random_id(),
                keyboard=keyboard.get_keyboard() if keyboard else None
            )
            return
        except Exception as e:
            logging.error(f"Ошибка отправки альбома (попытка {attempt+1}): {e}", exc_info=True)
            if attempt < retries - 1:
                time.sleep(1)
            else:
                logging.error(f"Не удалось отправить альбом пользователю {user_id}: {caption[:50]}...")
                send_message(user_id, caption, keyboard)

def send_to_operator(text, retries=3):
    for attempt in range(retries):
        try:
            vk.messages.send(user_id=OPERATOR_ID, message=text, random_id=get_random_id())
            return
        except Exception as e:
            logging.error(f"Ошибка отправки оператору (попытка {attempt+1}): {e}", exc_info=True)
            if attempt < retries - 1:
                time.sleep(1)
            else:
                logging.error(f"Не удалось отправить сообщение оператору: {text[:50]}...")

# ==================================================
#  ЛОГИКА ПОКАЗА УСЛУГ (без изменений)
# ==================================================
def show_program_choice(user_id, category_key, back_state):
    services = MAIN_SERVICES.get(category_key, [])
    if not services:
        send_message(user_id, 'В этой категории пока нет программ.', get_item_actions_keyboard())
        return
    user_temp[user_id] = {'category': category_key, 'back_state': back_state}
    keyboard = get_programs_choice_keyboard(services)
    send_message(user_id, '❓ Выберите программу', keyboard)

def show_program_details(user_id, service):
    send_attachments(user_id, service.get('attachments', []), service['text'], get_item_actions_keyboard())

def show_extra_choice(user_id, category_key, back_state):
    services = EXTRA_SERVICES.get(category_key, [])
    if not services:
        send_message(user_id, 'В этой категории пока нет услуг.', get_extra_actions_keyboard())
        return
    user_temp[user_id] = {'extra_category': category_key, 'back_state': back_state}
    keyboard = get_extra_choice_keyboard(services)
    send_message(user_id, '❓ Выберите услугу', keyboard)

def show_extra_details(user_id, service):
    send_attachments(user_id, service.get('attachments', []), service['text'], get_extra_actions_keyboard())

# ==================================================
#  ОСНОВНАЯ ЛОГИКА (состояния)
# ==================================================
user_stack = {}
user_temp = {}
user_last_active = {}
processed_events = set()  # для дедупликации (хранит event_id)

# Очистка старых состояний (вызывается каждый раз в process_event)
def cleanup_old_users(max_inactive_seconds=7200):
    now = time.time()
    to_delete = []
    for uid, last_active in user_last_active.items():
        if now - last_active > max_inactive_seconds:
            to_delete.append(uid)
    for uid in to_delete:
        user_stack.pop(uid, None)
        user_temp.pop(uid, None)
        user_last_active.pop(uid, None)
    # также ограничиваем размер processed_events
    if len(processed_events) > 1000:
        processed_events.clear()

app = Flask(__name__)

@app.route('/', methods=['POST'])
def handle_webhook():
    data = request.get_json()
    if data.get('type') == 'confirmation':
        return CONFIRMATION_CODE
    if data.get('secret') != SECRET_KEY:
        return 'ok', 200
    if data.get('type') == 'message_new':
        # Дедупликация по event_id
        event_id = data.get('event_id')
        if event_id:
            if event_id in processed_events:
                return 'ok', 200
            processed_events.add(event_id)
        process_event(data['object'])
    return 'ok', 200

def process_event(event):
    user_id = event['message']['from_id']
    if user_id < 0:
        return
    raw_text = event['message']['text']
    user_message = raw_text.lower().strip()

    # Обновляем время последней активности и очищаем старые записи
    user_last_active[user_id] = time.time()
    cleanup_old_users()

    # Инициализация нового пользователя
    if user_id not in user_stack:
        user_stack[user_id] = ['main']
        user_temp.pop(user_id, None)
        send_message(user_id, '🤗 Здравствуйте! Мы очень рады, что Вы решили выбрать именно нас! \n🤖У нас есть очень удобный бот, который подскажет Вам всё, что захотите!\n🙂Но если он не сможет помочь, то всегда можно вызвать оператора', get_main_keyboard())
        return

    current_state = user_stack[user_id][-1]

    # --- ГЛОБАЛЬНЫЕ КОМАНДЫ (всегда работают) ---
    if user_message in ['привет', 'начать', 'старт', 'меню', 'start', 'бот']:
        user_stack[user_id] = ['main']
        user_temp.pop(user_id, None)
        send_message(user_id, '😊 Добро пожаловать!', get_main_keyboard())
        return

    if user_message in ['📞 связь с оператором', 'связь с оператором']:
        user_link = f"https://vk.com/id{user_id}"
        send_to_operator(f"Пользователь {user_link} хочет связаться с оператором.")
        send_message(user_id, "📞 Оператор совсем скоро свяжется с вами!", get_main_keyboard())
        user_stack[user_id] = ['main']
        user_temp.pop(user_id, None)
        return

    if user_message in ['❓ у меня индивидуальный запрос', 'у меня индивидуальный запрос']:
        user_link = f"https://vk.com/id{user_id}"
        send_to_operator(f"ИНДИВИДУАЛЬНЫЙ ЗАПРОС от {user_link}.")
        send_message(user_id, "📞 Отлично! Ваш запрос уже передан администратору, осталось подождать совсем чуть-чуть!", get_main_keyboard())
        user_stack[user_id] = ['main']
        user_temp.pop(user_id, None)
        return

    # --- КНОПКА "НАЗАД" (работает везде) ---
    if user_message in ['◀ назад', 'назад']:
        if len(user_stack[user_id]) > 1:
            user_stack[user_id].pop()
            new_state = user_stack[user_id][-1]

            if new_state == 'main':
                send_message(user_id, '🔥 Главное меню', get_main_keyboard())
            elif new_state == 'programs':
                send_message(user_id, '❓ Какая программа вам нужна?', get_programs_keyboard())
            elif new_state == 'birthdays':
                send_message(user_id, '✅ Выберите возраст', get_birthdays_keyboard())
            elif new_state == 'choosing_program':
                cat = user_temp.get(user_id, {}).get('category')
                back = user_temp.get(user_id, {}).get('back_state')
                if cat and back:
                    show_program_choice(user_id, cat, back)
                else:
                    send_message(user_id, 'Главное меню', get_main_keyboard())
            elif new_state == 'viewing_program':
                cat = user_temp.get(user_id, {}).get('category')
                back = user_temp.get(user_id, {}).get('back_state')
                if cat and back:
                    show_program_choice(user_id, cat, back)
                else:
                    send_message(user_id, 'Главное меню', get_main_keyboard())
            elif new_state == 'extra_categories':
                send_message(user_id, '❓ Выберите категорию доп. услуг', get_extra_categories_keyboard())
            elif new_state == 'choosing_extra':
                extra_cat = user_temp.get(user_id, {}).get('extra_category')
                if extra_cat:
                    show_extra_choice(user_id, extra_cat, 'extra_categories')
                else:
                    send_message(user_id, '❓ Выберите категорию', get_extra_categories_keyboard())
            elif new_state == 'viewing_extra_detail':
                extra_cat = user_temp.get(user_id, {}).get('extra_category')
                if extra_cat:
                    show_extra_choice(user_id, extra_cat, 'extra_categories')
                else:
                    send_message(user_id, '❓ Выберите категорию', get_extra_categories_keyboard())
        else:
            send_message(user_id, '🔥 Вжух! И вы уже в главном меню!', get_main_keyboard())
        return

    # --- РЕЖИМ ОЖИДАНИЯ АНКЕТЫ ---
    if current_state == 'waiting_order_text':
        if user_message in ['◀ отмена', 'отмена']:
            # отмена заказа: возвращаемся к предыдущему состоянию
            user_stack[user_id].pop()  # убираем waiting_order_text
            prev_state = user_stack[user_id][-1] if user_stack[user_id] else 'main'
            if prev_state == 'viewing_program':
                last_program = user_temp.get(user_id, {}).get('last_viewed_program')
                if last_program:
                    show_program_details(user_id, last_program)
                else:
                    send_message(user_id, '☹ Заказ отменён.', get_main_keyboard())
            elif prev_state == 'viewing_extra_detail':
                last_extra = user_temp.get(user_id, {}).get('last_viewed_extra')
                if last_extra:
                    show_extra_details(user_id, last_extra)
                else:
                    send_message(user_id, '☹ Заказ отменён.', get_main_keyboard())
            elif prev_state == 'choosing_program':
                cat = user_temp.get(user_id, {}).get('category')
                back = user_temp.get(user_id, {}).get('back_state')
                if cat and back:
                    show_program_choice(user_id, cat, back)
                else:
                    send_message(user_id, '☹ Заказ отменён.', get_main_keyboard())
            elif prev_state == 'choosing_extra':
                extra_cat = user_temp.get(user_id, {}).get('extra_category')
                if extra_cat:
                    show_extra_choice(user_id, extra_cat, 'extra_categories')
                else:
                    send_message(user_id, '☹ Заказ отменён.', get_main_keyboard())
            else:
                send_message(user_id, '☹ Заказ отменён.', get_main_keyboard())
            user_temp.pop(user_id, None)
            return
        # не отмена – отправляем заказ оператору
        send_message(user_id, "📞 Отлично! Вызываю оператора, нужно совсем немного подождать!", get_to_main_keyboard())
        user_link = f"https://vk.com/id{user_id}"
        send_to_operator(f"НОВЫЙ ЗАКАЗ от {user_link}\nСообщение: {raw_text}")
        user_stack[user_id].append('order_completed')
        user_temp.pop(user_id, None)
        return

    # --- ПОСЛЕ ЗАКАЗА (кнопка "В главное меню") ---
    if current_state == 'order_completed':
        if user_message in ['🏠 в главное меню', 'в главное меню']:
            user_stack[user_id] = ['main']
            send_message(user_id, '🔥 Главное меню', get_main_keyboard())
        else:
            send_message(user_id, '👀 Используйте кнопку "В главное меню".', get_to_main_keyboard())
        return

    # --- ОСНОВНАЯ НАВИГАЦИЯ ---
    if current_state == 'main':
        if user_message in ['📚 программы', 'программы']:
            user_stack[user_id].append('programs')
            send_message(user_id, '🤗 Давайте выберем категорию', get_programs_keyboard())

    elif current_state == 'programs':
        if user_message in ['🎂 дни рождения', 'дни рождения']:
            user_stack[user_id].append('birthdays')
            send_message(user_id, 'Выберите возраст', get_birthdays_keyboard())
        elif user_message in ['🏫 для классов', 'для классов']:
            user_stack[user_id].append('choosing_program')
            show_program_choice(user_id, 'class_all', 'programs')
        elif user_message in ['🛠 доп. услуги', 'доп. услуги']:
            user_stack[user_id].append('extra_categories')
            send_message(user_id, '🤗 Давайте выберем категорию', get_extra_categories_keyboard())

    elif current_state == 'birthdays':
        if user_message == '👶 1-4 года':
            user_stack[user_id].append('choosing_program')
            show_program_choice(user_id, 'birthday_1_4', 'birthdays')
        elif user_message == '🧒 5-7 лет':
            user_stack[user_id].append('choosing_program')
            show_program_choice(user_id, 'birthday_5_7', 'birthdays')
        elif user_message == '👦 8-12 лет':
            user_stack[user_id].append('choosing_program')
            show_program_choice(user_id, 'birthday_8_12', 'birthdays')

    elif current_state == 'choosing_program':
        if user_message in ['🛠 доп. услуги', 'доп. услуги']:
            user_stack[user_id].append('extra_categories')
            send_message(user_id, '🤗 Давайте выберем категорию', get_extra_categories_keyboard())
            return

        category = user_temp.get(user_id, {}).get('category')
        if not category:
            send_message(user_id, 'Ошибка, попробуйте снова.', get_main_keyboard())
            user_stack[user_id] = ['main']
            return
        services = MAIN_SERVICES.get(category, [])
        selected_service = None
        for service in services:
            title = service.get('title', '')
            if title and user_message == title.lower():
                selected_service = service
                break
        if selected_service:
            if selected_service.get('special'):
                send_message(user_id, "✅ Мы обязательно подберем для вас индивидуальную программу! Наш оператор очень скоро свяжется с вами)", get_main_keyboard())
                user_link = f"https://vk.com/id{user_id}"
                send_to_operator(f"❓ ПОЛЬЗОВАТЕЛЬ НЕ НАШЕЛ ПРОГРАММУ. Ссылка: {user_link}")
                user_stack[user_id] = ['main']
                user_temp.pop(user_id, None)
                return
            else:
                user_stack[user_id].append('viewing_program')
                user_temp[user_id]['last_viewed_program'] = selected_service
                show_program_details(user_id, selected_service)
        else:
            send_message(user_id, '🤗 Пожалуйста, выберите программу из списка', get_programs_choice_keyboard(services))

    elif current_state == 'viewing_program':
        if user_message in ['✅ хочу заказать', 'хочу заказать']:
            user_stack[user_id].append('waiting_order_text')
            send_message(user_id, '🔥 Осталось совсем чуть-чуть! Заполните небольшую анкету и пришлите её прямо сюда 📌 \n\n1) Какая программа вам приглянулась? (+ доп.услуги, если требуется) ✅ \n2) На какие даты рассчитываете проведение праздника? 📅 \n3) Для кого планируется праздник? (Имя, возраст) 🎆 \n4) Сколько гостей и какого возраста планируется на празднике? 👫\n5) Нужно ли в конце программы делать торжественный вынос тортика/сладостей? 🎂 \n6) Место проведения праздника, адрес? 🙂 \n7) Ваш контактный номер телефона? 📞 \n8) Есть ли какие-либо дополнительные комментарии ? 📝\n\n', get_waiting_keyboard())
        elif user_message in ['🛠 доп. услуги', 'доп. услуги']:
            user_stack[user_id].append('extra_categories')
            send_message(user_id, '🤗 Выберите категорию доп. услуг', get_extra_categories_keyboard())

    elif current_state == 'extra_categories':
        if user_message in ['🎨 мастер-классы', 'мастер-классы']:
            user_stack[user_id].append('choosing_extra')
            show_extra_choice(user_id, 'master_classes', 'extra_categories')
        elif user_message in ['💃 дискотека', 'дискотека']:
            user_stack[user_id].append('choosing_extra')
            show_extra_choice(user_id, 'disco', 'extra_categories')
        elif user_message in ['➕ ещё', 'ещё']:
            user_stack[user_id].append('choosing_extra')
            show_extra_choice(user_id, 'more', 'extra_categories')
        elif user_message == '◀ назад':
            user_stack[user_id].pop()
            send_message(user_id, '❓ Какая программа вам нужна?', get_programs_keyboard())
        else:
            send_message(user_id, 'Пожалуйста, выберите категорию', get_extra_categories_keyboard())

    elif current_state == 'choosing_extra':
        extra_category = user_temp.get(user_id, {}).get('extra_category')
        if not extra_category:
            send_message(user_id, 'Ошибка, попробуйте снова.', get_main_keyboard())
            user_stack[user_id] = ['main']
            return
        services = EXTRA_SERVICES.get(extra_category, [])
        selected_service = None
        for service in services:
            title = service.get('title', '')
            if title and user_message == title.lower():
                selected_service = service
                break
        if selected_service:
            if selected_service.get('special'):
                send_message(user_id, "Мы свяжемся с вами!", get_main_keyboard())
                user_link = f"https://vk.com/id{user_id}"
                send_to_operator(f"❓ ПОЛЬЗОВАТЕЛЬ НЕ НАШЕЛ УСЛУГУ. Ссылка: {user_link}")
                user_stack[user_id] = ['main']
                user_temp.pop(user_id, None)
                return
            else:
                user_stack[user_id].append('viewing_extra_detail')
                user_temp[user_id]['last_viewed_extra'] = selected_service
                show_extra_details(user_id, selected_service)
        else:
            send_message(user_id, 'Пожалуйста, выберите услугу из списка', get_extra_choice_keyboard(services))

    elif current_state == 'viewing_extra_detail':
        if user_message in ['✅ хочу заказать', 'хочу заказать']:
            user_stack[user_id].append('waiting_order_text')
            send_message(user_id, '🔥 Осталось совсем чуть-чуть! Заполните небольшую анкету и пришлите её прямо сюда 📌 \n\n1) Какая программа вам приглянулась? (+ доп.услуги, если требуется) ✅ \n2) На какие даты рассчитываете проведение праздника? 📅 \n3) Для кого планируется праздник? (Имя, возраст) 🎆 \n4) Сколько гостей и какого возраста планируется на празднике? 👫\n5) Нужно ли в конце программы делать торжественный вынос тортика/сладостей? 🎂 \n6) Место проведения праздника, адрес? 🙂 \n7) Ваш контактный номер телефона? 📞 \n8) Есть ли какие-либо дополнительные комментарии ? 📝\n\n', get_waiting_keyboard())

@app.route('/', methods=['GET'])
def handle_health_check():
    return 'OK', 200

@app.route('/ping', methods=['GET'])
def ping():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
