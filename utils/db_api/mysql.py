import mysql.connector
import json  # json ni import qiling


class Database:
    def __init__(self, host, user, password, db_name):
        self.host = host
        self.user = user
        self.password = password
        self.db_name = db_name
        self.connection = None  # Connection ni bu yerda None qilib boshlang'ich holatga keltiramiz

    def connect(self):
        # Agar connection mavjud bo'lmasa yoki yopilgan bo'lsa, yangisini ochamiz
        if self.connection is None or not self.connection.is_connected():
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.db_name
            )

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        self.connect()  # Har bir so'rovdan oldin ulanishni tekshiramiz va ochamiz
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True, buffered=True)  # buffered=True ni qo'shamiz!
            cursor.execute(sql, parameters)

            if commit:
                self.connection.commit()
                return None

            if fetchone:
                result = cursor.fetchone()
                return result

            if fetchall:
                result = cursor.fetchall()
                return result

            return None  # Agar fetchone yoki fetchall true bo'lmasa, hech narsa qaytarmaymiz

        except mysql.connector.Error as err:
            print(f"Xato yuz berdi: {err}")
            # Xato yuz berganda ham connectionni yopishga urinmaslik uchun pass
            raise  # Xatoni yuqoriga uzatish
        finally:
            if cursor:
                try:
                    # Bu yerda asosiy tuzatish: kursor yopilishidan oldin uning natijalarini to'liq iste'mol qilish
                    # Agar buffered=True bo'lsa, bu avtomatik ravishda bajariladi.
                    # Lekin xato holatlari uchun yechim
                    for _ in cursor:  # Qolgan natijalarni o'qib tugatish
                        pass
                    cursor.close()
                except mysql.connector.Error as e:
                    print(f"Kursor yopishda xato: {e}")

    # ... (qolgan metodlar o'zgarmasdan qoladi)

    def get_user(self, user_id: int):
        sql = """
              SELECT * \
              FROM users \
              WHERE user_id = %s \
              """
        user_data = self.execute(sql, parameters=(str(user_id),), fetchone=True)

        if user_data:
            # MySQL JSON ustuni ba'zida string qaytarishi mumkin, shuning uchun parse qilamiz
            if 'join_requests' in user_data and isinstance(user_data['join_requests'], str):
                try:
                    user_data['join_requests'] = json.loads(user_data['join_requests'])
                except json.JSONDecodeError:
                    user_data['join_requests'] = {}
            elif 'join_requests' not in user_data or user_data['join_requests'] is None:
                user_data['join_requests'] = {}

        print(f"DEBUG: get_user - User {user_id} fetched: {user_data}")
        return user_data

    def update_user_join_requests(self, user_id: int, join_requests: dict):
        sql = """
              UPDATE users \
              SET join_requests = %s \
              WHERE user_id = %s \
              """
        # JSON obyektini stringga aylantirib saqlaymiz
        self.execute(sql, parameters=(json.dumps(join_requests), str(user_id)), commit=True)
        print(f"DEBUG: update_user_join_requests - User {user_id} requests updated to {join_requests}")

    def add_join_request(self, user_id: int, channel_id: int):
        user = self.get_user(user_id)
        if user:
            # Agar join_requests ustuni bo'lmasa yoki None bo'lsa, bo'sh lug'at bilan boshlaymiz
            current_requests = user.get('join_requests', {})
            current_requests[str(channel_id)] = True  # Kanal ID'sini string sifatida saqlaymiz
            self.update_user_join_requests(user_id, current_requests)
        else:
            print(f"ERROR: User {user_id} not found when trying to add join request for channel {channel_id}")

    def remove_join_request(self, user_id: int, channel_id: int):
        user = self.get_user(user_id)
        if user:
            current_requests = user.get('join_requests', {})
            if str(channel_id) in current_requests:
                del current_requests[str(channel_id)]
                self.update_user_join_requests(user_id, current_requests)
        else:
            print(f"ERROR: User {user_id} not found when trying to remove join request for channel {channel_id}")

    def has_join_request(self, user_id: int, channel_id: int) -> bool:
        user = self.get_user(user_id)
        print(
            f"DEBUG: has_join_request - User {user_id}, Channel {channel_id}. Result: {bool(user and user.get('join_requests', {}).get(str(channel_id)))} , Requests: {user.get('join_requests', {}) if user else 'User not found'}")  # Debug
        return bool(user and user.get('join_requests', {}).get(str(channel_id)))

    def add_user(self, user_id, ban, sana, status):
        sql = """
              INSERT INTO users (user_id, ban, sana, status, join_requests)
              VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY \
              UPDATE \
                  ban = \
              VALUES (ban), sana = \
              VALUES (sana), status = \
              VALUES (status), join_requests = \
              VALUES (join_requests) \
              """
        # Yangi foydalanuvchi qo'shilganda bo'sh JSON obyektini saqlaymiz
        self.execute(sql, parameters=(user_id, ban, sana, status, json.dumps({})), commit=True)
        print(f"DEBUG: add_user - User {user_id} added/updated successfully.")

    def get_all_channels(self):
        sql = "SELECT * FROM kanal"
        return self.execute(sql, fetchall=True)

    def get_serial_by_title(self, title):
        sql = "SELECT * FROM serials WHERE title = %s"
        return self.execute(sql, parameters=(title,), fetchone=True)

    def get_episodes_by_serial_id(self, serial_id):
        sql = "SELECT * FROM episodes WHERE serial_id = %s ORDER BY episode_number"
        # Bu yerda ham buffered=True ni hisobga olish kerak
        return self.execute(sql, parameters=(serial_id,), fetchall=True)

    def get_all_serials_titles(self):
        sql = "SELECT title FROM serials"
        serials_titles = self.execute(sql, fetchall=True)
        return [s['title'] for s in serials_titles] if serials_titles else []

    def get_serials_by_title_part(self, title_part):
        sql = "SELECT * FROM serials WHERE title LIKE %s"
        return self.execute(sql, parameters=('%' + title_part + '%',), fetchall=True)

    def create_table_users(self):
        sql = """
              CREATE TABLE IF NOT EXISTS users \
              ( \
                  id \
                  INT \
                  AUTO_INCREMENT \
                  PRIMARY \
                  KEY, \
                  user_id \
                  VARCHAR \
              ( \
                  255 \
              ) UNIQUE,
                  ban INT DEFAULT 0,
                  sana VARCHAR \
              ( \
                  255 \
              ),
                  status VARCHAR \
              ( \
                  255 \
              ),
                  join_requests JSON DEFAULT \
              ( \
                  JSON_OBJECT \
              ( \
              ))
                  ) \
              """
        self.execute(sql, commit=True)
        print("Table 'users' checked/created successfully with join_requests JSON column.")

    def create_table_kanal(self):
        sql = """
              CREATE TABLE IF NOT EXISTS kanal \
              ( \
                  id \
                  INT \
                  AUTO_INCREMENT \
                  PRIMARY \
                  KEY, \
                  chat_id \
                  VARCHAR \
              ( \
                  255 \
              ) UNIQUE,
                  url VARCHAR \
              ( \
                  255 \
              )
                  ) \
              """
        self.execute(sql, commit=True)
        print("Table 'kanal' checked/created successfully.")

    def create_table_serials(self):
        sql = """
              CREATE TABLE IF NOT EXISTS serials \
              ( \
                  id \
                  INT \
                  AUTO_INCREMENT \
                  PRIMARY \
                  KEY, \
                  title \
                  VARCHAR \
              ( \
                  255 \
              ) UNIQUE,
                  description TEXT
                  ) \
              """
        self.execute(sql, commit=True)
        print("Table 'serials' checked/created successfully.")

    def create_table_episodes(self):
        sql = """
              CREATE TABLE IF NOT EXISTS episodes \
              ( \
                  id \
                  INT \
                  AUTO_INCREMENT \
                  PRIMARY \
                  KEY, \
                  serial_id \
                  INT, \
                  episode_number \
                  INT, \
                  file_id \
                  VARCHAR \
              ( \
                  255 \
              ),
                  FOREIGN KEY \
              ( \
                  serial_id \
              ) REFERENCES serials \
              ( \
                  id \
              ) ON DELETE CASCADE
                  ) \
              """
        self.execute(sql, commit=True)
        print("Table 'episodes' checked/created successfully.")

    def create_table_admins(self):
        sql = """
              CREATE TABLE IF NOT EXISTS admins \
              ( \
                  id \
                  INT \
                  AUTO_INCREMENT \
                  PRIMARY \
                  KEY, \
                  user_id \
                  VARCHAR \
              ( \
                  255 \
              ) UNIQUE
                  ) \
              """
        self.execute(sql, commit=True)
        print("Table 'admins' checked/created successfully.")

    def add_admin(self, user_id):
        sql = "INSERT IGNORE INTO admins (user_id) VALUES (%s)"
        self.execute(sql, parameters=(str(user_id),), commit=True)
        print(f"Admin {user_id} added.")

    def remove_admin(self, user_id):
        sql = "DELETE FROM admins WHERE user_id = %s"
        self.execute(sql, parameters=(str(user_id),), commit=True)
        print(f"Admin {user_id} removed.")

    def get_all_admins(self):
        sql = "SELECT user_id FROM admins"
        admins = self.execute(sql, fetchall=True)
        return [admin['user_id'] for admin in admins] if admins else []

    def is_user_admin(self, user_id):
        sql = "SELECT COUNT(*) FROM admins WHERE user_id = %s"
        result = self.execute(sql, parameters=(str(user_id),), fetchone=True)
        return result['COUNT(*)'] > 0

    def add_channel(self, chat_id, url):
        sql = "INSERT IGNORE INTO kanal (chat_id, url) VALUES (%s, %s)"
        self.execute(sql, parameters=(str(chat_id), url), commit=True)
        print(f"Channel {chat_id} added.")

    def remove_channel(self, chat_id):
        sql = "DELETE FROM kanal WHERE chat_id = %s"
        self.execute(sql, parameters=(str(chat_id),), commit=True)
        print(f"Channel {chat_id} removed.")

    def get_channel_by_chat_id(self, chat_id):
        sql = "SELECT * FROM kanal WHERE chat_id = %s"
        return self.execute(sql, parameters=(str(chat_id),), fetchone=True)

    def add_serial(self, title, description):
        sql = "INSERT IGNORE INTO serials (title, description) VALUES (%s, %s)"
        self.execute(sql, parameters=(title, description), commit=True)
        print(f"Serial '{title}' added.")

    def update_serial(self, serial_id, title=None, description=None):
        updates = []
        params = []
        if title:
            updates.append("title = %s")
            params.append(title)
        if description:
            updates.append("description = %s")
            params.append(description)

        if not updates:
            print("No updates provided for serial.")
            return

        sql = f"UPDATE serials SET {', '.join(updates)} WHERE id = %s"
        params.append(serial_id)
        self.execute(sql, parameters=tuple(params), commit=True)
        print(f"Serial {serial_id} updated.")

    def remove_serial(self, serial_id):
        sql = "DELETE FROM serials WHERE id = %s"
        self.execute(sql, parameters=(serial_id,), commit=True)
        print(f"Serial {serial_id} removed.")

    def add_episode(self, serial_id, episode_number, file_id):
        sql = "INSERT INTO episodes (serial_id, episode_number, file_id) VALUES (%s, %s, %s)"
        self.execute(sql, parameters=(serial_id, episode_number, file_id), commit=True)
        print(f"Episode {episode_number} for serial {serial_id} added.")

    def update_episode(self, episode_id, episode_number=None, file_id=None):
        updates = []
        params = []
        if episode_number:
            updates.append("episode_number = %s")
            params.append(episode_number)
        if file_id:
            updates.append("file_id = %s")
            params.append(file_id)

        if not updates:
            print("No updates provided for episode.")
            return

        sql = f"UPDATE episodes SET {', '.join(updates)} WHERE id = %s"
        params.append(episode_id)
        self.execute(sql, parameters=tuple(params), commit=True)
        print(f"Episode {episode_id} updated.")

    def remove_episode(self, episode_id):
        sql = "DELETE FROM episodes WHERE id = %s"
        self.execute(sql, parameters=(episode_id,), commit=True)
        print(f"Episode {episode_id} removed.")