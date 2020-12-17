"""All database inquiries."""


from sqlite3 import Error as DB_Error
from telegram.utils.helper import escape_markdown
from dbhelper import DBHelper


def db_add_message(group_id, user_id_hash, msg_type, msg_length, timestamp):
    """Add a new entry to the Message table."""
    try:
        DBHelper().sql_add_message(
            group_id, user_id_hash, msg_type, msg_length, timestamp
        )
    except ValueError as error:
        raise ValueError(error)
    except DB_Error as db_error:
        print(f"An error has occured: {db_error}")


def db_add_group(group_id, group_name):
    """Add a group to the table Telegram_Group."""
    try:
        DBHelper().sql_add_group(group_id, group_name)
    except DB_Error as db_error:
        raise ValueError(db_error)


def db_add_user(user_id_hash, user_name):
    """Add a Telegram user to the database."""
    try:
        DBHelper().sql_add_user(user_id_hash, user_name)
    except DB_Error as db_error:
        raise ValueError(db_error)


def db_get_all_messages(group_id=None, timespan=0):
    """Fetch the number of all messages from one group or from
    all groups if group_id is omitted.

    Args:
        group_id (int or None): Telegram Group ID or None
        timespan (int):

    Returns:
        First element of the tuple from the database query.

    """
    sql_timespan = {
        0: " AND date(timestamp)>=date('now', 'start of month')",
        1: " AND date(timestamp)>=date('now','-30 day')",
        2: " AND date(timestamp)=date('now')",
        3: "",
    }

    try:
        if group_id:
            total_msg = DBHelper().sql_get_all_messages_from_group(
                group_id, sql_timespan[timespan]
            )
        else:
            total_msg = DBHelper().sql_get_all_messages(sql_timespan[timespan])
    except DB_Error as db_error:
        raise ValueError(db_error)

    return total_msg[0]


def db_get_user_messages(user_id_hash, group_id=None):
    """Fetch the number of user messages from one group or if
    the group_id is omitted from all groups in which the user is.

    Args:
        user_id_hash (str)    : Hash of the Telegram User ID
        group_id (int or None): Telegram Group ID or None

    Returns:
        First element of the tuple from the database query.

    """
    try:
        if group_id:
            total_msg = DBHelper().sql_get_user_messages_from_group(
                user_id_hash, group_id
            )
        else:
            total_msg = DBHelper().sql_get_all_user_messages(user_id_hash)
    except DB_Error as db_error:
        raise ValueError(db_error)

    return total_msg[0]


def db_get_message_types(group_id=None, timespan=0):
    """Query the different message types either from one group
    or from all messages if the group_id is omitted.

    Args:
        group_id (int or None): Telegram Group ID or None
        timestamp (int):

    Returns:
        Formatted text with all types and their number.

    """
    sql_timespan = {
        0: " AND date(timestamp)>=date('now', 'start of month')",
        1: " AND date(timestamp)>=date('now','-30 day')",
        2: " AND date(timestamp)=date('now')",
        3: "",
    }

    try:
        if group_id:
            msg_types = DBHelper().sql_get_message_types_from_group(
                group_id, sql_timespan[timespan]
            )
        else:
            msg_types = DBHelper().sql_get_all_message_types(sql_timespan[timespan])
    except DB_Error as db_error:
        raise ValueError(db_error)

    #
    # Check for division by zero!!!
    #
    total_msg = db_get_all_messages(group_id, timespan)
    text = "\n\n`"
    for posts, msg_type in msg_types:
        text += f"{posts:<4} - {msg_type:>10} ({posts/total_msg*100:>4.1f}%)\n"
    text += "`\n"

    return text


def db_get_top_posters(group_id=None, timespan=0):
    """Get the top posters in a group or from all groups if group_id
    is omitted.

    Args:
        group_id (int or None): Telegram Group ID or None
        timespan (int):

    Returns:
        Formatted text with user names and their numbers.

    """
    sql_timespan = {
        0: " AND date(timestamp)>=date('now', 'start of month')",
        1: " AND date(timestamp)>=date('now','-30 day')",
        2: " AND date(timestamp)=date('now')",
        3: "",
    }

    try:
        if group_id:
            top_posters = DBHelper().sql_get_top_posters_from_group(
                group_id, sql_timespan[timespan]
            )
        else:
            top_posters = DBHelper().sql_get_top_posters_overall(sql_timespan[timespan])
    except DB_Error as db_error:
        raise ValueError(db_error)

    text = "\n*Highscore*:\n\n"
    for posts, user in top_posters:
        user = escape_markdown(user)
        text += f"{user} {posts} Nachrichten\n"

    return text
