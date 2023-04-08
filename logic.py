import requests
import time
import json
import datetime
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO,
    filename='home/bot/VPBot/bot.log'
)

logger = logging.getLogger(__name__)


def create_user_subscribe_boosty(email, category):
    '''
    Сохранение категории доступа пользователя из бусти.
    '''
    if category == 1: # 1$
        subscribe = 712
    elif category == 2: # 30$
        subscribe = 873
    else: # 100$
        subscribe = 874

    try:
        url = f'https://eraperemen.info/wp-admin/admin-ajax.php?action=subscribe_bot_tg'
        params = {
            "email": f"{email}",
            "subscribe": f"{subscribe}"
        }
        req = requests.post(url, data=params)
        logger.info("create_user: \nreq status: %s", req.status_code)
    except Exception as e:
        logger.info("create_user_subscribe_boosty: \nошибка: %s", e)

def create_user(email, password, telegram_id):
    '''
    Создание пользователя в бд.
    '''

    try:
        url = 'https://eraperemen.info/wp-admin/admin-ajax.php?action=create_user'
        params = {
            "email": f"{email}",
            "password": f"{password}",
            "telegram_id": f"{telegram_id}",
            "boosty_user": "да",
        }
        req = requests.post(url, params)

        logger.info("create_user: \nreq status: %s", req.status_code)
    except Exception as e:
        logger.info("create_user: \nошибка: %s", e)

    return email in req.text

def add_user_tg(email, telegram_id):
    '''
    Добавление id пользователю, если tg_id нет.
    '''
    res = ''
    try:
        url = 'https://eraperemen.info/wp-admin/admin-ajax.php?action=create_user'
        params = {
            "email": f"{email}",
            "password": f"{1}",
            "telegram_id": f"{telegram_id}",
        }
        req = requests.post(url, params)
        time.sleep(5)
        res = req.text
    except Exception as e:
        logger.info("add_user_tg: \nошибка: %s", e)

    return email in res

def check_tg_id_in_db(email):
    tg_id = ''
    try:
        url = 'https://eraperemen.info/wp-admin/admin-ajax.php?action=get_tg_id'
        params = {
            "email": f"{email}",
        }
        req = requests.get(url, params)
        tg_id = req.text

        logger.info("check_tg_id_in_db: \nreq status: %s", req.status_code)
    except Exception as e:
        logger.info("check_tg_id_in_db: \nошибка: %s", e)
    return tg_id != ''

def check_user_category_website_by_subscription(telegram_id):
    '''
    Возвращает 1 или 2 или 3 в зависимости от типа подписки.
    1 = 712
    2 = 873
    3 = 874
    '''
    email = take_user_email_by_id(telegram_id=telegram_id)
    try:
        url = 'https://eraperemen.info/wp-admin/admin-ajax.php?action=subscription_list'
        params = {
            "email": f"{email}",
        }
        req = requests.get(url, params)
        print(req.status_code)
        print(req.text)
        if '874' in req.text:
            category = 3
        elif '873' in req.text:
            category = 2
        else:
            category = 1
    except Exception as e:
        print(e)
    return category

def take_user_subscriptions(telegram_id):
    '''
    Возвращает подписку пользователя.
    '''
    email = take_user_email_by_id(telegram_id=telegram_id)
    try:
        url = 'https://eraperemen.info/wp-admin/admin-ajax.php?action=subscription_list'
        params = {
            "email": f"{email}",
        }
        req = requests.get(url, params)
        print(req.status_code)
        data_dict = json.loads(req.text)
        data = [i['meta_value'] for i in data_dict]
        print(data)
    except Exception as e:
        print(e)
    return data

def take_user_email_by_id(telegram_id):
    """
    Получает маил по tg_id.
    """
    email = ''
    try:
        url = 'https://eraperemen.info/wp-admin/admin-ajax.php?action=user_email'
        params = {
            "telegram_id": f"{telegram_id}",
        }
        req = requests.get(url, params)
        print(req.status_code)
        print(req.text)
        data_dict = json.loads(req.text)
        email = data_dict['data']["user_email"]
        print(email)
    except Exception as e:
        print(e)
    return email


def check_user(email):
    """Проверяет наличие пользователя в бд по email."""
    try:
        url = 'https://eraperemen.info/wp-admin/admin-ajax.php?action=user_exists'
        params = {
            "email": f"{email}",
        }
        req = requests.get(url, params)
        print(req.status_code)
        print(req.text)
    except Exception as e:
        print(e)
    return email in req.text

def take_all_id_boosty_category_1():
    '''Возвращает все tg_id группы 1$.'''
    try:
        url = 'https://eraperemen.info/wp-admin/admin-ajax.php?action=get_elong&subscribe=712'
        req = requests.get(url)
        print(req.status_code)
        data = req.text.split('],')
        for i in range(len(data)):
            while '[' in data[i] or ']' in data[i] or '"' in data[i]:
                data[i] = data[i].replace('[', '').replace(']', '').replace('"', '')

    except Exception as e:
        print(e)
    return data

def take_all_id_boosty_category_2():
    '''Возвращает все tg_id группы 35$.'''
    try:
        url = 'https://eraperemen.info/wp-admin/admin-ajax.php?action=get_elong&subscribe=873'
        req = requests.get(url)
        print(req.status_code)
        data = req.text.split('],')
        for i in range(len(data)):
            while '[' in data[i] or ']' in data[i] or '"' in data[i]:
                data[i] = data[i].replace('[', '').replace(']', '').replace('"', '')

    except Exception as e:
        print(e)
    return data

def take_all_id_boosty_category_3():
    '''Возвращает все tg_id группы 100$.'''
    try:
        url = 'https://eraperemen.info/wp-admin/admin-ajax.php?action=get_elong&subscribe=874'
        req = requests.get(url)
        print(req.status_code)
        data = req.text.split('],')
        for i in range(len(data)):
            while '[' in data[i] or ']' in data[i] or '"' in data[i]:
                data[i] = data[i].replace('[', '').replace(']', '').replace('"', '')

    except Exception as e:
        print(e)
    return data


def take_all_id_users_category_1():
    '''Возвращает все tg_id группы 1$.'''
    try:
        url = 'https://eraperemen.info/wp-admin/admin-ajax.php?action=get_bans&subscribe=712'
        req = requests.get(url)
        print(req.status_code)
        data = req.text.split('],')
        for i in range(len(data)):
            while '[' in data[i] or ']' in data[i] or '"' in data[i]:
                data[i] = data[i].replace('[', '').replace(']', '').replace('"', '')

    except Exception as e:
        print(e)
    return data

def take_all_id_users_category_2():
    '''Возвращает все tg_id группы 35$.'''
    try:
        url = 'https://eraperemen.info/wp-admin/admin-ajax.php?action=get_bans&subscribe=873'
        req = requests.get(url)
        print(req.status_code)
        data = req.text.split('],')
        for i in range(len(data)):
            while '[' in data[i] or ']' in data[i] or '"' in data[i]:
                data[i] = data[i].replace('[', '').replace(']', '').replace('"', '')

    except Exception as e:
        print(e)
    return data

def take_all_id_users_category_3():
    '''Возвращает все tg_id группы 100$.'''
    try:
        url = 'https://eraperemen.info/wp-admin/admin-ajax.php?action=get_bans&subscribe=874'
        req = requests.get(url)
        print(req.status_code)
        data = req.text.split('],')
        for i in range(len(data)):
            while '[' in data[i] or ']' in data[i] or '"' in data[i]:
                data[i] = data[i].replace('[', '').replace(']', '').replace('"', '')

    except Exception as e:
        print(e)
    return data

