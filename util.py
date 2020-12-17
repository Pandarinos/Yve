"""Utility functions."""


import sys
import logging
from logging import handlers
import hashlib
from functools import wraps

from config import ADMINS, GROUPS, MESSAGE_TYPES
from dbqueries import db_add_group, db_add_user


def init_logging():
    """Create and initialize a logger."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    frmt = logging.Formatter(
        "[%(levelname)s] %(asctime)s |%(funcName)18s | %(message)s", "%m-%d %H:%M:%S"
    )

    # Make sure that there are not more than one handlers
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(frmt)
        logger.addHandler(console_handler)

        file_handler = handlers.TimedRotatingFileHandler(
            "panda.log", when="d", interval=1, backupCount=3
        )
        file_handler.setFormatter(frmt)
        logger.addHandler(file_handler)

    return logger


def get_name(update):
    """Try to get the sender name."""
    try:
        if isinstance(update, CallbackQuery):
            name = update.from_user.first_name
        elif update.effective_user:
            name = update.effective_user.first_name
        else:
            name = update.message.from_user.first_name
    except (NameError, AttributeError):
        try:
            name = update.message.from_user.username
        except (NameError, AttributeError):
            print("No username or first name... wtf")
            name = "unknown user"
    return name


def init_groups():
    """Transfer the groups from the config file to the database."""
    print("Init groups... ", end="")
    try:
        for group_id in GROUPS:
            db_add_group(group_id, None)
    except ValueError as error:
        print(f"Error during initilization: {error}")
    print("Done.")


def add_user(user_id_hash, user_name):
    """Add a Telegram user to the database."""
    try:
        db_add_user(user_id_hash, user_name)
    except ValueError as error:
        print(f"Can't add user: {error}")


def group_chat_only(func):
    """Wrapper for group chats only."""

    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        if update.effective_chat.type == "private":
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="Der Befehl funktioniert nur in Gruppen.",
            )
            return func
        return func(update, context, *args, **kwargs)

    return wrapped


def selected_groups_only(func):
    """Wrapper for selected groups."""

    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        if update.effective_chat.id not in GROUPS:
            return func
        return func(update, context, *args, **kwargs)

    return wrapped


def selected_messages_only(func):
    """Wrapper for selected message types."""

    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        if effective_message_type(update) not in MESSAGE_TYPES:
            return func
        return func(update, context, *args, **kwargs)

    return wrapped


def restricted(func):
    """Wrapper for restricted commands."""

    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in ADMINS:
            msg = f"Unauthorized access denied for {user_id}."
            print(msg)
            update.message.reply_text(msg)
            return func
        return func(update, context, *args, **kwargs)

    return wrapped


def hash_uid(user_id):
    """Create hash from the user_id."""
    return hashlib.sha512(str(user_id).encode()).hexdigest()
