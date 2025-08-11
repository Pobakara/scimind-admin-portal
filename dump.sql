CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
INSERT INTO "alembic_version" VALUES('8d82f3b6d49a');
CREATE TABLE attendance (
	id SERIAL PRIMARY KEY, 
	student_id INTEGER, 
	class_id INTEGER, 
	date DATE, 
	status VARCHAR, 
	notes TEXT, 
	updated_by INTEGER, 
	updated_at TIMESTAMP, 	
	FOREIGN KEY(class_id) REFERENCES class (id), 
	FOREIGN KEY(student_id) REFERENCES student (id), 
	FOREIGN KEY(updated_by) REFERENCES user_account (id)
);
CREATE TABLE class (
	id SERIAL PRIMARY KEY, 
	class_code VARCHAR NOT NULL, 
	class_status VARCHAR, 
	class_name VARCHAR, 
	subject VARCHAR, 
	year_level VARCHAR, 
	batch VARCHAR, 
	sub_batch VARCHAR, 
	class_type VARCHAR, 
	description VARCHAR, 
	playlist_id VARCHAR, 
	class_created TIMESTAMP, 
	class_teacher INTEGER, 
	class_day VARCHAR, 
	class_time VARCHAR, 
	class_location VARCHAR, 
	updated_by INTEGER, 
	updated_at TIMESTAMP, 
	
	FOREIGN KEY(class_teacher) REFERENCES user_account (id), 
	FOREIGN KEY(updated_by) REFERENCES user_account (id), 
	UNIQUE (class_code)
);
INSERT INTO "class" VALUES(6,'BIO112024GROUP1G','active','Biology - Year 11 - 2024 - Group 1','Biology','Year 11','2024','Group 1','Group','',NULL,'2025-08-10 15:06:59.496783','Nisa Bandarayapa','Wednesday','17:30','Mulgrave',NULL,NULL);
INSERT INTO "class" VALUES(7,'BIO112024GROUP2G','active','Biology - Year 11 - 2024 - Group 2','Biology','Year 11','2024','Group 2','Group','',NULL,'2025-08-10 15:09:59.163519','Nisa Bandarayapa','Saturday','08:30','Mulgrave',NULL,NULL);
INSERT INTO "class" VALUES(8,'CHE112024GROUP1G','active','Chemistry - Year 11 - 2024 - Group 1','Chemistry','Year 11','2024','Group 1','Group','',NULL,'2025-08-10 15:10:40.598263','Nisa Bandarayapa','Friday','18:00','Mulgrave',NULL,NULL);
INSERT INTO "class" VALUES(9,'CHE122025GROUP1G','active','Chemistry - Year 12 - 2025 - Group 1','Chemistry','Year 12','2025','Group 1','Group','',NULL,'2025-08-10 15:11:21.402313','Nisa Bandarayapa','Saturday','10:00','Mulgrave',NULL,NULL);
INSERT INTO "class" VALUES(10,'SCI102024GROUP1G','active','Science - Year 10 - 2024 - Group 1','Science','Year 10','2024','Group 1','Group','',NULL,'2025-08-10 15:12:09.917604','Nisa Bandarayapa','Sunday','09:00','Mulgrave',NULL,NULL);
INSERT INTO "class" VALUES(11,'SCI92025GROUP1G','active','Science - Year 9 - 2025 - Group 1','Science','Year 9','2025','Group 1','Group','',NULL,'2025-08-10 15:12:43.877349','Nisa Bandarayapa','Thursday','18:00','Mulgrave',NULL,NULL);
INSERT INTO "class" VALUES(12,'SCI92025GROUP2G','active','Science - Year 9 - 2025 - Group 2','Science','Year 9','2025','Group 2','Group','',NULL,'2025-08-10 15:13:20.078661','Nisa Bandarayapa','Thursday','16:30','Mulgrave',NULL,NULL);
INSERT INTO "class" VALUES(13,'SCI62025GROUP1G','active','Science - Year 6 - 2025 - Group 1','Science','Year 6','2025','Group 1','Group','',NULL,'2025-08-10 15:13:47.741222','Nisa Bandarayapa','Tuesday','18:00','Mulgrave',NULL,NULL);
INSERT INTO "class" VALUES(14,'REV122025SANDAMII','active','Revision - Year 12 - 2025 - Sandami','Revision','Year 12','2025','Sandami','Individual','',NULL,'2025-08-10 15:15:37.285120','Nisa Bandarayapa','Monday','16:30','Mulgrave',NULL,NULL);
CREATE TABLE google_account_permissions (
	id SERIAL PRIMARY KEY, 
	integration_account_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	permission_level VARCHAR, 
	FOREIGN KEY(integration_account_id) REFERENCES google_integration_account (id), 
	FOREIGN KEY(user_id) REFERENCES user_account (id)
);
INSERT INTO "google_account_permissions" VALUES(1,1,1,'uploader');
CREATE TABLE google_classroom_course (
	id SERIAL PRIMARY KEY, 
	course_id VARCHAR NOT NULL, 
	name VARCHAR, 
	section VARCHAR, 
	join_code VARCHAR, 
	class_id INTEGER, 
	integration_account_id INTEGER NOT NULL, 
	created_by INTEGER, 
	created_at TIMESTAMP, 
	
	FOREIGN KEY(class_id) REFERENCES class (id), 
	FOREIGN KEY(created_by) REFERENCES user_account (id), 
	FOREIGN KEY(integration_account_id) REFERENCES google_integration_account (id), 
	UNIQUE (course_id)
);
CREATE TABLE google_integration_account (
	id SERIAL PRIMARY KEY, 
	account_name VARCHAR, 
	google_email VARCHAR NOT NULL, 
	access_token TEXT, 
	refresh_token TEXT, 
	owner_user_id INTEGER NOT NULL, 
	created_at TIMESTAMP, 
	last_synced TIMESTAMP, 
	 
	FOREIGN KEY(owner_user_id) REFERENCES user_account (id), 
	UNIQUE (google_email)
);
INSERT INTO "google_integration_account" VALUES(1,'pobakara','pobakara@gmail.com',NULL,NULL,1,'2025-08-07 11:53:48.308835',NULL);
CREATE TABLE parent (
	id SERIAL PRIMARY KEY, 
	student_id INTEGER, 
	name VARCHAR NOT NULL, 
	relationship VARCHAR, 
	contact_number VARCHAR, 
	parent_email VARCHAR, 
	FOREIGN KEY(student_id) REFERENCES student (id)
);
CREATE TABLE payment (
	id SERIAL PRIMARY KEY, 
	student_id INTEGER, 
	fee_id INTEGER, 
	amount DOUBLE PRECISION, 
	date TIMESTAMP, 
	method VARCHAR, 
	reference VARCHAR, 
	notes TEXT, 
	updated_by INTEGER, 
	updated_at TIMESTAMP, 
	FOREIGN KEY(fee_id) REFERENCES student_fee (id), 
	FOREIGN KEY(student_id) REFERENCES student (id), 
	FOREIGN KEY(updated_by) REFERENCES user_account (id)
);
CREATE TABLE student (
	id SERIAL PRIMARY KEY, 
	student_code VARCHAR NOT NULL, 
	first_name VARCHAR NOT NULL, 
	last_name VARCHAR NOT NULL, 
	dob DATE, 
	gender VARCHAR, 
	contact_number VARCHAR, 
	grade_school VARCHAR, 
	student_email VARCHAR, 
	address VARCHAR, 
	notes TEXT, 
	status VARCHAR, 
	created_at TIMESTAMP, 
	updated_by INTEGER, 
	updated_at TIMESTAMP, 
	FOREIGN KEY(updated_by) REFERENCES user_account (id), 
	UNIQUE (student_code)
);
CREATE TABLE student_class_assignment (
	id SERIAL PRIMARY KEY, 
	student_id INTEGER, 
	class_id INTEGER, 
	enrolled_from DATE, 
	enrolled_to DATE, 
	is_primary BOOLEAN, 
	FOREIGN KEY(class_id) REFERENCES class (id), 
	FOREIGN KEY(student_id) REFERENCES student (id)
);
CREATE TABLE student_fee (
	id SERIAL PRIMARY KEY, 
	student_id INTEGER, 
	class_id INTEGER, 
	fee_type VARCHAR, 
	amount_due DOUBLE PRECISION, 
	amount_paid DOUBLE PRECISION, 
	discount DOUBLE PRECISION, 
	due_date DATE, 
	payment_status VARCHAR, 
	notes TEXT, 
	updated_by INTEGER, 
	updated_at TIMESTAMP, 
	
	FOREIGN KEY(class_id) REFERENCES class (id), 
	FOREIGN KEY(student_id) REFERENCES student (id), 
	FOREIGN KEY(updated_by) REFERENCES user_account (id)
);
CREATE TABLE user_account (
	id SERIAL PRIMARY KEY, 
	username VARCHAR NOT NULL, 
	email VARCHAR NOT NULL, 
	password_hash VARCHAR NOT NULL, 
	role VARCHAR, 
	active BOOLEAN, 
	created_at TIMESTAMP, 
	google_email VARCHAR, 
	profile_picture_url TEXT, 
	
	UNIQUE (email), 
	UNIQUE (username)
);
INSERT INTO "user_account" VALUES(1,'pobakara','pobakara@gmail.com','scrypt:32768:8:1$sWOxORM3PTSpFgqS$ce0ad0fc0502d798e70116c9bfb2a606a547b6278904b3886cf0c59630f5650f40c77fdceb789fb9c6f3a68f440cd9915ac090dee21706f2c4250b067032ba22','admin',TRUE,'2025-08-07 11:23:24.003337','pobakara@gmail.com',NULL);
CREATE TABLE video (
	id SERIAL PRIMARY KEY, 
	video_id VARCHAR NOT NULL, 
	title VARCHAR, 
	class_id INTEGER, 
	youtube_playlist_id VARCHAR, 
	classroom_posted BOOLEAN, 
	integration_account_id INTEGER NOT NULL, 
	uploaded_by INTEGER, 
	published_at TIMESTAMP, 
	
	FOREIGN KEY(class_id) REFERENCES class (id), 
	FOREIGN KEY(integration_account_id) REFERENCES google_integration_account (id), 
	FOREIGN KEY(uploaded_by) REFERENCES user_account (id), 
	UNIQUE (video_id)
);
INSERT INTO "video" VALUES(1,'J5HDfDthiCs','Biology - Year 11 - 2026 - Group 1 - 08/08/2025',NULL,'PL-JUgqoHaiCEanyjKsoZ35AuqmKyWm4BA',FALSE,1,1,'2025-08-08 07:15:51.834308');
INSERT INTO "video" VALUES(2,'TwmsOxfHGak','Chemistry - Year 11 - 2025 - Group 1 - 15/08/2025',NULL,'PL-JUgqoHaiCGF24f7l7ZfJvHH7FtIuCGi',FALSE,1,1,'2025-08-08 07:15:59.566591');
INSERT INTO "video" VALUES(3,'FUFCA1slIRM','Science - Year 8 - 2025 - Group 1 - 22/08/2025',NULL,'PL-JUgqoHaiCGp-u_Dk9Fbk8IJE8LZNt3y',FALSE,1,1,'2025-08-08 07:16:07.323874');
INSERT INTO "video" VALUES(4,'qCt7stBjAzQ','Biology - Year 11 - 2026 - Group 1 - 10/08/2025',NULL,'PL-JUgqoHaiCEanyjKsoZ35AuqmKyWm4BA',FALSE,1,1,'2025-08-08 07:22:25.937747');
INSERT INTO "video" VALUES(5,'L087AyYQrMs','Chemistry - Year 11 - 2025 - Group 1 - 17/08/2025',NULL,'PL-JUgqoHaiCGF24f7l7ZfJvHH7FtIuCGi',FALSE,1,1,'2025-08-08 07:22:36.045984');
INSERT INTO "video" VALUES(6,'zfYar6Ywvz4','Science - Year 8 - 2025 - Group 1 - 24/08/2025',NULL,'PL-JUgqoHaiCGp-u_Dk9Fbk8IJE8LZNt3y',FALSE,1,1,'2025-08-08 07:22:49.592459');