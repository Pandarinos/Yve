BEGIN TRANSACTION;
	CREATE TABLE IF NOT EXISTS `Telegram_User` (
		`id`		INTEGER PRIMARY KEY AUTOINCREMENT,
		`user_id`	TEXT,
		`user_name`	TEXT,
		UNIQUE(user_id)
	);
	CREATE TABLE IF NOT EXISTS `Telegram_Group` (
		`id`		INTEGER PRIMARY KEY AUTOINCREMENT,
		`group_id`	INTEGER NOT NULL UNIQUE,
		`group_name`	TEXT,
		`debug`		INTEGER DEFAULT 0
	);
	CREATE TABLE IF NOT EXISTS `Telegram_Type` (
		`id`		INTEGER PRIMARY KEY AUTOINCREMENT,
		`message_type`	TEXT NOT NULL UNIQUE,
		`msg_type_ger`	TEXT
	);
	CREATE TABLE IF NOT EXISTS `Message` (
		`id`		INTEGER PRIMARY KEY AUTOINCREMENT,
		`group_id`	INTEGER NOT NULL,
		`user_id`	INTEGER NOT NULL,
		`msg_type`	INTEGER,
		`msg_length`	INTEGER,
		`timestamp`	TEXT,
		FOREIGN KEY(`group_id`) REFERENCES `Telegram_Group`(`id`),
		FOREIGN KEY(`user_id`) REFERENCES `Telegram_User`(`id`),
		FOREIGN KEY(`msg_type`) REFERENCES `Telegram_Type`(`id`)
	);
	INSERT INTO Telegram_Type (message_type,msg_type_ger) VALUES
		('audio','Audio'), ('game','Spiel'), ('document','Dokument'), ('photo','Foto'),
		('animation','Animation'), ('sticker','Sticker'), ('video','Video'),
		('voice','Sprache'), ('video_note','Videonachricht'), ('contact','Kontakt'),
		('location','Standort'), ('venue','Treffpunkt'), ('invoice','Rechnung'),
		('successful_payment','Erfolgreiche Zahlung'), ('text','Text'),
		('new_chat_members','Neue Chat-Mitglieder'), ('new_chat_title','Neuer Chat-Titel'),
		('new_chat_photo','Neues Chat-Foto'), ('delete_chat_photo','Chatfoto löschen'),
		('group_chat_created','Gruppenchat erstellt'), ('supergroup_chat_created','Supergruppenchat erstellt'),
		('channel_chat_created','Channelchat erstellt'), ('migrate_to_chat_id','Zu Chat ID migriert'),
		('migrate_from_chat_id','Von Chat ID migriert'), ('pinned_message','Angepinnte Nachricht');
	COMMIT;
