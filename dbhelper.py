"""DB helper functions."""


import sqlite3
from sqlite3 import Error as DB_Error
from config import SQLITE3_DB


class DBHelper:
    """DB helper class."""

    dbpath = SQLITE3_DB

    def __init__(self):
        try:
            self.db = sqlite3.connect(self.dbpath)
            self.cursor = self.db.cursor()
            self.db.execute("PRAGMA foreign_keys=on")
        except DB_Error as db_error:
            print(db_error)

    def sql_add_group(self, group_id, group_name):
        """Add a group to the Telegram_Group table.

        Args:
            group_id (int)  : Telegram group ID
            group_name (str): Telegram group name (optional)

        Return:
            None.

        """
        stmt = (
            "INSERT OR IGNORE INTO Telegram_Group (group_id, group_name) VALUES (?, ?)"
        )
        arg = (group_id, group_name)
        self.db.execute(stmt, arg)
        self.db.commit()

    def sql_add_user(self, user_id_hash, user_name):
        """Add a user to the Telegram_User table.

        Args:
            user_id_hash (str): Hashed Telegram user ID
            user_name    (str): Telegram user name

        Return:
            None.

        """
        stmt = "INSERT OR IGNORE INTO Telegram_User (user_id, user_name) VALUES (?, ?)"
        arg = (user_id_hash, user_name)
        self.db.execute(stmt, arg)
        self.db.commit()

    def sql_add_message(self, group_id, user_id_hash, msg_type, length, timestamp):
        """Add an entry to the message table.

        Args:
            group (int)         : Telegram Group ID
            user_id_hash (str)  : Hash value of the user ID (foreign key -> User(id))
            type (str)          : Type of the message (foreign key -> Type(id))
            length (int)        : Length of the message (words)
            timestamp (datetime): Date and time as sent by Telegram

        Return:
            None.

        Raises ValueError if user(/group/type) does not exist in db.

        """
        try:
            stmt = (
                "INSERT INTO Message "
                "   (group_id, user_id, msg_type, msg_length, timestamp) "
                "VALUES "
                "   ((SELECT id FROM Telegram_Group WHERE group_id=(?)), "
                "    (SELECT id FROM Telegram_User WHERE user_id=(?)), "
                "    (SELECT id FROM Telegram_Type WHERE message_type=(?)), "
                "    ?, ?)"
            )
            arg = (group_id, user_id_hash, msg_type, length, timestamp)
            self.db.execute(stmt, arg)
            self.db.commit()
        except sqlite3.IntegrityError:
            raise ValueError("IntegrityError")
        except DB_Error as db_error:
            raise Exception(db_error)
        finally:
            if self.db:
                self.db.close()

    def sql_get_all_messages_from_group(self, group_id, sql_timespan):
        """Get all messages from a group.

        Args:
            group_id (int): Telegram Group ID from the group from which
            sql_timespan (str):

        Returns:
            Number of all messages in this group (tuple).

        """
        stmt = (
            "SELECT COUNT(*) FROM Message "
            "WHERE group_id=(SELECT id FROM Telegram_Group WHERE group_id=(?))"
            f"{sql_timespan}"
        )
        arg = (group_id,)
        cur = self.db.execute(stmt, arg)
        return cur.fetchone()

    def sql_get_all_messages(self, sql_timespan):
        """Get the number of messages from all groups.

        Args:
            sql_timespan (str):

        Returns:
            Number of all messages (tuple).

        """
        stmt = f"SELECT COUNT(*) FROM Message WHERE 1=1 {sql_timespan}"
        cur = self.db.execute(stmt)
        return cur.fetchone()

    def sql_get_user_messages_from_group(self, user_id_hash, group_id):
        """Query the statistics for users in groups.

        Args:
            user_id_hash (str) : The hashed Telegram User ID
            group_id (int)     : Telegram Group ID from the group from which
                                 the user started the command.

        Returns:
            Number of user messages in this group (tuple).

        """
        stmt = (
            "SELECT COUNT(*) FROM Message WHERE "
            "user_id=(SELECT id FROM Telegram_User WHERE user_id=(?)) "
            "AND group_id=(SELECT id FROM Telegram_Group WHERE group_id=(?))"
        )
        arg = (user_id_hash, group_id)
        cur = self.db.execute(stmt, arg)
        return cur.fetchone()

    def sql_get_all_user_messages(self, user_id_hash):
        """Query the statistics for user in all groups.

        Args:
            user_id_hash (str): The hashed Telegram User ID

        Returns:
            Number of user messages in all groups (tuple).

        """
        stmt = (
            "SELECT COUNT(*) FROM Message WHERE "
            "user_id=(SELECT id FROM Telegram_User WHERE user_id=(?))"
        )
        arg = (user_id_hash,)
        cur = self.db.execute(stmt, arg)
        return cur.fetchone()

    def sql_get_message_types_from_group(self, group_id, sql_timespan):
        """Query the message types in a group, sorted and by number
        in descending order.

        Args:
            group_id (int): Telegram Group ID
            sql_timespan (str):

        Returns:
            Number of messages with message types (Tuple or list of tuples).

        """
        stmt = (
            "SELECT count(m.id) AS mCount, t.msg_type_ger "
            "FROM Message m, Telegram_Type t "
            "WHERE t.id=m.msg_type "
            "AND m.group_id=(SELECT id FROM Telegram_Group WHERE group_id=(?)) "
            f" {sql_timespan} "
            "GROUP BY t.id ORDER BY mCount DESC"
        )
        arg = (group_id,)
        cur = self.db.execute(stmt, arg)
        return cur.fetchall()

    def sql_get_all_message_types(self, sql_timespan):
        """Query all message types of all groups, sorted and by number
        in descending order.

        Args:
            sql_timespan (str):

        Returns:
            Number of messages with message types (Tuple or list of tuples).

        """
        stmt = (
            "SELECT count(m.id) AS mCount, t.msg_type_ger "
            "FROM Message m, Telegram_Type t "
            f"WHERE t.id=m.msg_type {sql_timespan} "
            "GROUP BY t.id ORDER BY mCount DESC"
        )
        return self.db.execute(stmt)

    def sql_get_top_posters_from_group(self, group_id, sql_timespan, limit=10):
        """Get the top posters in a group.

        Args:
            sql_timespan (str):
            limit (int): Number of results (default 5)

        Returns:

        """
        stmt = (
            "SELECT count(m.id) AS mCount, u.user_name "
            "FROM Message m, Telegram_User u "
            "WHERE u.id=m.user_id "
            "AND m.group_id=(SELECT id FROM Telegram_Group WHERE group_id=(?))"
            f"{sql_timespan} "
            "GROUP BY u.user_name ORDER BY mCount DESC LIMIT ?"
        )
        arg = (group_id, limit)
        cur = self.db.execute(stmt, arg)
        return cur.fetchall()

    def sql_get_top_posters_overall(self, sql_timespan, limit=10):
        """Get the top posters from all groups.

        Args:
            sql_timespan (str):
            limit (int): Number of results (default 5)

        Returns:

        """
        stmt = (
            "SELECT count(m.id) AS mCount, u.user_name "
            "FROM Message m, Telegram_User u "
            "WHERE u.id=m.user_id"
            f"{sql_timespan} "
            "GROUP BY u.user_name ORDER BY mCount DESC LIMIT ?"
        )
        arg = (limit,)
        cur = self.db.execute(stmt, arg)
        return cur.fetchall()
