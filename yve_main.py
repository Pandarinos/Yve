#!/usr/bin/env python3


"""
    Yve version 0.0.2

"""

import sys

# import pprint
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    Filters,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
)
from telegram.utils.helpers import effective_message_type
from dbqueries import (
    db_get_all_messages,
    db_get_user_messages,
    db_add_message,
    db_get_message_types,
    db_get_top_posters,
)
from util import (
    init_logging,
    get_name,
    add_user,
    hash_uid,
    init_groups,
    restricted,
    group_chat_only,
    selected_groups_only,
    selected_messages_only,
)
from config import TELEGRAM_BOT_TOKEN, BOT_VERSION, PUB_IP, CERT, PRIV_KEY


# Debug Mode default Off
DEBUG = False

# Init logging
LOGGER = init_logging()


@selected_groups_only
@selected_messages_only
def process_message(update, context):
    """Process every new update."""
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(update.to_dict())

    group_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = get_name(update)
    msg_type = effective_message_type(update)
    text = update.effective_message.text
    if text:
        msg_length = len(text.split())
    else:
        msg_length = 0
    timestamp = update.effective_message.date

    if DEBUG:
        debug_msg = (
            "DEBUG: ON\n\n"
            f"Group ID: {group_id}\n"
            f"Type:{msg_type}\n"
            f"Name:{user_name}\n"
            f"ID:{user_id}\n"
            f"Length:{msg_length}\n"
            f"Date:{timestamp}\n"
        )
        context.bot.send_message(chat_id=update.effective_chat.id, text=debug_msg)

    try:
        db_add_message(group_id, hash_uid(user_id), msg_type, msg_length, timestamp)
    except ValueError as err:
        print(f"An error has occurred: {err}\nTrying to add new user.")
        add_user(hash_uid(user_id), user_name)


def user_statistic(update, context):
    """Outputs the statistics of the user either from the current group,
    or from all groups if the bot command is send in a private chat. """
    if update.effective_chat.type == "private":
        group_id = None
    else:
        group_id = update.effective_chat.id

    user_id_hash = hash_uid(update.effective_user.id)
    user_name = get_name(update)

    total_msg = db_get_all_messages(group_id)
    user_msg = db_get_user_messages(user_id_hash, group_id)

    if group_id:
        if total_msg > 0:
            text = (
                f"{user_name}:\n{user_msg}/{total_msg} Nachrichten "
                f"({user_msg/total_msg*100:.1f}%)"
            )
        else:
            text = f"{user_name}:\nKeine Nachrichten. Vielleicht ist die Gruppe nicht in der Datenbank?"
    else:
        text = f"{user_msg} Nachrichten in allen Gruppen."

    context.bot.send_message(
        chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.MARKDOWN
    )


def build_markup(button_state):
    """Build the reply_markup.

    Args:
        button_state (int): Number 0-4 for the time span that is displayed

    Returns:
        reply_markup: The Inlinekeyboard with the button(s)

    """
    fwd_button = InlineKeyboardButton(">", callback_data="forward")
    bck_button = InlineKeyboardButton("<", callback_data="backward")
    reply_markup = InlineKeyboardMarkup([[bck_button, fwd_button]])

    if button_state == 3:
        reply_markup = InlineKeyboardMarkup([[bck_button]])
    if button_state == 0:
        reply_markup = InlineKeyboardMarkup([[fwd_button]])

    return reply_markup


def get_statistic_message(group_id, timespan):
    """Build the total statistics message.

    Args:
        group_id (int|None): The Telegram group ID or None for all groups
        timespan (int):

    Returns:
        text (str): The complete message with the statistics

    """
    header = {0: "Diesen Monat", 1: "Letzte 30 Tage", 2: "Heute", 3: "Gesamt"}
    total_msg = db_get_all_messages(group_id, timespan)
    text = f"*{total_msg} Nachrichten gesamt* _({header[timespan]})_"
    text += db_get_message_types(group_id, timespan)
    text += db_get_top_posters(group_id, timespan)

    return text


def fetch_group_id(update, context, msg_id):
    """Get the Telegram group ID depending on the command that was send
    and the value stored in chat_data["nws"].

    Args:
        msg_id (int): Telegram message ID, either from Message object
                      or from the CallbackQuery object
        chat_data (dict): A dictionary to store chat related stuff
        nws (list}: Stores the message IDs of the messages that where
                    called with the /networkstats command

    Returns:
        Either the current Telegram group ID or None

    """
    nws = context.chat_data.get("nws", [])

    if msg_id in nws or "/networkstat" in update.effective_message.text:
        group_id = None
    else:
        group_id = update.effective_chat.id

    return group_id


@group_chat_only
def total_statistics(update, context):
    """Outputs the total statistics, either from the current group
    or from all groups.

    Args:
        group_id (int|None): Telegram Group ID or None if called via
                             the /networkstats command

    """
    group_id = fetch_group_id(update, context, update.message.message_id)

    reply_markup = build_markup(button_state=0)
    stat_message = get_statistic_message(group_id, timespan=0)

    send = context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=stat_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup,
    )

    # The /networkstat command calls up the statistics for all groups.
    # The message ID is then saved in chat_data["nws"] to be able to
    # identify the message again.
    if not group_id:
        nws = context.chat_data.get("nws", [])
        nws.append(send.message_id)
        context.chat_data["nws"] = nws


def button_pressed(update, context):
    """Handle the forward/backward button of the statistics message.
    Get the direction from the callback_query.data and the button state
    from the chat_data.

    Args:
        direction (str): "forward" or "backward"
        button_state (int): A number from 0 to 4

    """
    query = update.callback_query
    msg_id = query.message.message_id
    direction = query.data

    button_state = context.chat_data.get(msg_id, 0)
    group_id = fetch_group_id(update, context, msg_id)

    if direction == "forward":
        button_state += 1
    else:
        button_state -= 1

    # After the user presses an inline button, Telegram clients will display a
    # progress bar until you call answer. It is, therefore, necessary to react
    # by calling telegram.Bot.answer_callback_query even if no notification to
    # the user is needed (e.g., without specifying any of the optional
    # parameters).
    query.answer()

    reply_markup = build_markup(button_state)
    stat_message = get_statistic_message(group_id, timespan=button_state)

    context.bot.editMessageText(
        chat_id=update.effective_chat.id,
        message_id=msg_id,
        text=stat_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup,
    )

    context.chat_data[msg_id] = button_state


@restricted
def clear_statistic():  # update, context):
    """Deletes the entire statistic of the current group from the
    database!

    """
    print("This deletes the entire statistic!")


@group_chat_only
@restricted
def output_group_id(update, *args):
    """Output the current group ID. Only for admins."""
    update.message.reply_text(update.message.chat_id)


@restricted
def toggle_debug_mode(update, context):
    """Toggle the debug mode on/off."""
    global DEBUG
    DEBUG = not DEBUG
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"Debug Mode: {'On' if DEBUG else 'Off'}"
    )


def print_help(update, context):
    """Outputs a brief help text."""
    help_msg = (
        "Yve Hilfe:\n\n"
        "/help - Zeigt dir diese Hilfe an.\n"
        "/me - Na, wie viele Nachrichten hast du hier geschrieben?\n"
        "/stats - Menschen sind fasziniert von Statistiken, also "
        "erfährst du hiermit, wie viele Nachrichten hier bereits "
        "geschrieben wurden.\n"
        "/networkstats - Zeigt dir eine Gesamtstatistik aller Gruppen, "
        "in denen Yve verwendet wird.\n\n"
        "Yve Version 0.0.2 - erschaffen von @thisdudeisvegan & @cri5h\n"
        "News-Channel: @yve_news\n"
        "Meinen Code findest du auf GitHub! Bitte respektiere meine Lizenz.\n"
        "https://github.com/Pandarinos/Yve"
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=help_msg, parse_mode=ParseMode.MARKDOWN
    )


def error(update, context):
    """Log Errors caused by Updates."""
    LOGGER.warning('Update "%s" caused error "%s"', update, context.error)


def start_local(updater):
    """Start the bot on local machine."""
    updater.start_polling()  # (timeout=30)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


def start_webhook(updater):
    """Start the bot on server."""
    updater.start_webhook(
        listen=PUB_IP,
        port=8443,
        url_path=TELEGRAM_BOT_TOKEN,
        key=PRIV_KEY,
        cert=CERT,
        webhook_url=f"https://{PUB_IP}:8443/{TELEGRAM_BOT_TOKEN}",
    )
    updater.idle()


def main():
    """Start the bot."""
    print(f"{BOT_VERSION[0], BOT_VERSION[1]} starting...")
    # Transfer groups from config to db
    init_groups()

    # Create EventHandler and pass it your bot's token.
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CallbackQueryHandler(button_pressed))
    dispatcher.add_handler(CommandHandler("me", user_statistic))
    dispatcher.add_handler(CommandHandler("stats", total_statistics))
    dispatcher.add_handler(CommandHandler("networkstats", total_statistics))
    dispatcher.add_handler(CommandHandler("clear", clear_statistic))
    dispatcher.add_handler(CommandHandler("gid", output_group_id))
    dispatcher.add_handler(CommandHandler("debug", toggle_debug_mode))
    dispatcher.add_handler(CommandHandler("help", print_help))
    dispatcher.add_handler(
        MessageHandler(Filters.all & ~Filters.command, process_message)
    )

    # log all errors
    dispatcher.add_error_handler(error)

    # Start polling or webhook
    if sys.argv[-1] == "webhook":
        start_webhook(updater)
    else:
        start_local(updater)


if __name__ == "__main__":
    main()
