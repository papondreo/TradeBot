import logging
import os
from typing import Optional, Tuple
from dotenv import load_dotenv
from telegram import Chat, ChatMember, ChatMemberUpdated, Update, ReplyKeyboardMarkup
from telegram.ext import (Application,
                          MessageHandler,
                          ChatMemberHandler,
                          CommandHandler,
                          filters,
                          ContextTypes,
                          PicklePersistence,
                          ConversationHandler)

import logic
from constants import (EMAIL, PASSWORD, ACCESS,
                       HELLO_TEXT, PASSWORD_TEXT,
                       EMAIL_TEXT, EMAIL_TEXT_CHECK,
                       HELP_TEXT, DENY_TEXT,
                       GROUP_1, GROUP_2, GROUP_3)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO,
    filename='home/bot/VPBot/bot.log'
)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Приветствует пользоателя и создаёт меня для ссылки на чаты."""
    user = update.message.from_user
    logger.info("Start: %s: %s запустил", user.first_name, update.message.text)
    reply_markup = ReplyKeyboardMarkup([['/access - Получение доступа к группам.'],
                                        ['/registration - Регистрация на сайте.'],
                                        ['/help - Помощь с ботом.'],])

    await update.message.reply_text(text=HELLO_TEXT, reply_markup=reply_markup)


async def registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the selected FIO and asks for a education."""
    user_data = context.user_data
    user = update.message.from_user
    if user.id in (GROUP_1, GROUP_2, GROUP_3):
        return ConversationHandler.END
    user_data[user.id] = {}
    logger.info("Registration: %s: %s начал регистрацию", user.first_name, update.message.text)
    await update.message.reply_text(
        text=EMAIL_TEXT,
    )
    return EMAIL


async def email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет эмейл."""
    user = update.message.from_user
    user_data = context.user_data
    user_data[user.id].update({'email': update.message.text})

    logger.info("Registration: %s-%s ввёл email", user.first_name, update.message.text)
    await update.message.reply_text(
        text=PASSWORD_TEXT,
    )

    return PASSWORD


async def password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет пароль."""
    user = update.message.from_user
    user_data = context.user_data
    password = update.message.text
    email = user_data[user.id]['email']

    # тут создание пользователя бусти
    if logic.check_user(email) or logic.check_tg_id_in_db(email):
        logger.info("Registration: %s-%s не смог зарегистрироваться", user.first_name, update.message.text)
        await update.message.reply_text(
            "Вы уже зарегистрированы на сайте и у вас есть доступ, воспользуйтесь командой /access.",
        )
        return ConversationHandler.END

    # !!! Проверка доступа пользователя !!!
    info_1 = await context.bot.get_chat_member(chat_id=GROUP_1, user_id=user.id)
    info_2 = await context.bot.get_chat_member(chat_id=GROUP_2, user_id=user.id)
    info_3 = await context.bot.get_chat_member(chat_id=GROUP_3, user_id=user.id)

    if (info_1.status not in ('member', 'restricted', 'admin') and
       info_2.status not in ('member', 'restricted', 'admin') and
       info_3.status not in ('member', 'restricted', 'admin')):
        logger.info("Registration: %s-%s не является участником групп \n Группа 1$: %s, Группа 35$: %s, Группа 100$: %s", user.first_name, update.message.text, info_1.status, info_2.status, info_3.status)
        await update.message.reply_text(
            text=DENY_TEXT,
        )
        return ConversationHandler.END

    if info_1.status in ('member', 'restricted', 'admin'): # 1$
        access = 1
    if info_2.status in ('member', 'restricted', 'admin'): # 35$
        access = 2
    if info_3.status in ('member', 'restricted', 'admin'): # 100$
        access = 3

    logic.create_user(email, password, user.id)
    # !!! Конец проверки !!!
    logic.create_user_subscribe_boosty(email, access)
    logger.info("email of %s: %s", user.first_name, update.message.text)
    await update.message.reply_text(
        f"✅ Регистрация окончена\nВаш аккаунт создан\nEmail:{email}\nPassword:{password}\nТеперь перейдите на наш сайт eraperemen.info и получите доступ к закрытому разделу.\n⭐️ Приятного пользования",)
    user_data[user.id] = {}
    logger.info("Registration: %s: %s зарегистрировался\n Группа 1$: %s, Группа 35$: %s, Группа 100$: %s", user.first_name, update.message.text, info_1.status, info_2.status, info_3.status)
    return ConversationHandler.END


def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tracks the chats the bot is in."""
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return
    was_member, is_member = result

    # Let's check who is responsible for the change
    cause_name = update.effective_user.full_name

    # Handle chat types differently:
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        if not was_member and is_member:
            logger.info("%s started the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s blocked the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).discard(chat.id)
    elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if not was_member and is_member:
            logger.info("%s added the bot to the group %s", cause_name, chat.title)
            context.bot_data.setdefault("group_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s removed the bot from the group %s", cause_name, chat.title)
            context.bot_data.setdefault("group_ids", set()).discard(chat.id)
    else:
        if not was_member and is_member:
            logger.info("%s added the bot to the channel %s", cause_name, chat.title)
            context.bot_data.setdefault("channel_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s removed the bot from the channel %s", cause_name, chat.title)
            context.bot_data.setdefault("channel_ids", set()).discard(chat.id)


async def show_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows which chats the bot is in"""
    group_ids = ", ".join(str(gid) for gid in context.bot_data.setdefault("group_ids", set()))
    text = (
        f" Moreover it is a member of the groups with IDs {group_ids} "
    )
    await update.effective_message.reply_text(text)


async def greet_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greets new users in chats and announces when someone leaves"""
    result = extract_status_change(update.chat_member)
    if result is None:
        return
    chat = update.effective_chat
    user = update.chat_member.chat.id
    # Оставить на будущее


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Действие отменено."
    )

    return ConversationHandler.END


async def access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало проверки доступа."""
    user = update.message.from_user
    if user.id in (GROUP_1, GROUP_2, GROUP_3):
        return ConversationHandler.END
    logger.info("Access: %s-%s запустил access", user.first_name, update.message.text)
    await update.message.reply_text(
        text=EMAIL_TEXT_CHECK,
    )
    return ACCESS


async def links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка email."""
    email = update.message.text
    user = update.message.from_user
    if logic.check_tg_id_in_db(email):
        access = logic.check_user_category_website_by_subscription(user.id)
    elif logic.check_user(email):
        logic.add_user_tg(email, user.id)
        access = logic.check_user_category_website_by_subscription(user.id)
    else:
        logger.info("Access: %s-%s не имеет доступа", user.first_name, update.message.text)
        await update.message.reply_text(
            "У Вас нет доступа. Обратитесь в поддержку.",
        )
        return ConversationHandler.END

    if access == 1: # 1$
        link = await context.bot.create_chat_invite_link(chat_id=GROUP_1,
                                                         member_limit=1,)
        await update.message.reply_text(text=f"Чат 1$ {link['invite_link']}")
    if access == 2: # 35$
        link = await context.bot.create_chat_invite_link(chat_id=GROUP_2,
                                                         member_limit=1,)
        await update.message.reply_text(text=f"Чат 15$ {link['invite_link']}")
    if access == 3: # 100$
        link_3 = await context.bot.create_chat_invite_link(chat_id=GROUP_3,
                                                           member_limit=1,)
        link_2 = await context.bot.create_chat_invite_link(chat_id=GROUP_2,
                                                           member_limit=1,)
        link_1 = await context.bot.create_chat_invite_link(chat_id=GROUP_1,
                                                           member_limit=1,)
        await update.message.reply_text(text=f"Чат 100$ {link_3['invite_link']}\nЧат 35$ {link_2['invite_link']}\nЧат 1$ {link_1['invite_link']}")
    logger.info("Access: %s-%s получил ссылки на группы", user.first_name, update.message.text)
    return ConversationHandler.END


async def clean_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запуск проверки пользователей и бан в случае истечения подписки."""
    logger.info("Запущена очистка групп")
    user = update.message.from_user
    context.job_queue.run_repeating(alarm, 3600, chat_id=user.id) # !!!!!!


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    chat_id = context.job.chat_id
    context.bot.send_message(chat_id=chat_id, text='Начат бан пользователей.')
    boosty_1 = logic.take_all_id_boosty_category_1()
    boosty_2 = logic.take_all_id_boosty_category_2()
    boosty_3 = logic.take_all_id_boosty_category_3()

    users_1 = logic.take_all_id_users_category_1()
    users_2 = logic.take_all_id_users_category_1()
    users_3 = logic.take_all_id_users_category_1()

    count = 0

    for i in users_1:
        if i == '':
            continue
        count += 1
        context.bot.ban_chat_member(chat_id=GROUP_1, user_id=i)
    for i in users_2:
        if i == '':
            continue
        count += 1
        context.bot.ban_chat_member(chat_id=GROUP_2, user_id=i)
    for i in users_3:
        if i == '':
            continue
        count += 1
        context.bot.ban_chat_member(chat_id=GROUP_3, user_id=i)

    for i in boosty_1:
        if i == '':
            continue
        info_1 = await context.bot.get_chat_member(chat_id=GROUP_1, user_id=i)
        if info_1.status == 'member':
            logic.create_user_subscribe_boosty(email, 1)
        else:
            count += 1
            context.bot.ban_chat_member(chat_id=GROUP_1, user_id=i)
    for i in boosty_2:
        if i == '':
            continue
        info_2 = await context.bot.get_chat_member(chat_id=GROUP_2, user_id=i)
        if info_2.status == 'member':
            logic.create_user_subscribe_boosty(email, 2)
        else:
            count += 1
            context.bot.ban_chat_member(chat_id=GROUP_2, user_id=i, until_date=1)
    for i in boosty_3:
        if i == '':
            continue
        info_3 = await context.bot.get_chat_member(chat_id=GROUP_3, user_id=i)
        if info_3.status == 'member':
            logic.create_user_subscribe_boosty(email, 3)
        else:
            count += 1
            context.bot.ban_chat_member(chat_id=GROUP_3, user_id=i, until_date=1)

    chat_id = context.job.chat_id
    context.bot.send_message(chat_id=chat_id, text=f'Забанено людей без подписок: {count}')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(text=HELP_TEXT)

async def full_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_document('home/bot/VPBot/bot.log')

def main() -> None:
    """Start the bot."""
    # just get it
    load_dotenv()
    token = os.getenv('TOKEN')
    persistence = PicklePersistence(filepath="conversationbot")
    application = Application.builder().token(token).persistence(persistence).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('start_ban_users', clean_groups))
    application.add_handler(CommandHandler('full_log_btw', full_log))
    # Keep track of which chats the bot is in
    application.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_handler(CommandHandler("show_chats", show_chats))

    # Handle members joining/leaving chats.
    application.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))

    reg_handler = ConversationHandler(
        entry_points=[CommandHandler("registration", registration)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(reg_handler)

    access_handler = ConversationHandler(
        entry_points=[CommandHandler("access", access)],
        states={
            ACCESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, links)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(access_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
