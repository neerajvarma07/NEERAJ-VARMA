import telebot
import json, os, threading, time, random
from collections import defaultdict
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired

bot = telebot.TeleBot(
    "8037278866:AAH3RfXVy0wQkImq_5A08uOhuwBcfj26rB0"
)

PASSWORD = "neeraj_20k"
AUTHORIZED_USERS = set()
spam_duration = 10000
SAVE_PATH = "saved_accounts.json"

default_msgs = [
    "𝙉𝙀𝙀𝙍𝘼𝙅",
    "𓆰𝙉𝙀𝙀𝙍𝘼𝙅𓆩⃟🩸⃟𓆪𓆪𓆱",
    "𝗡𝗘𝗘𝗥𝗔𝗝𝗥𝗔𝗜𝗗 ",
]

user_data = defaultdict(lambda: {
    "clients": {},
    "pending": {},
    "thread_id": None,
    "custom_msgs": [],
    "stop": False,
    "pause": False
})

def save_accounts():
    data = {}
    for uid, d in user_data.items():
        data[str(uid)] = {
            "accounts": list(d["clients"].keys())
        }
    with open(SAVE_PATH, "w") as f:
        json.dump(data, f)

if os.path.exists(SAVE_PATH):
    with open(SAVE_PATH, "r") as f:
        loaded = json.load(f)
    for uid_str, d in loaded.items():
        uid = int(uid_str)
        for uname in d.get("accounts", []):
            user_data[uid]["clients"][uname] = None

def try_login(user_id, username, password):
    cl = Client()
    try:
        cl.login(username, password)
        user_data[user_id]["clients"][username] = cl
        save_accounts()
        return "✅ Login success"
    except ChallengeRequired:
        user_data[user_id]["pending"][username] = (cl, password)
        return f"⚠️ Verification needed for @{username}"
    except Exception as e:
        return f"❌ Login failed: {e}"

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message,
        "🔐 Send password:\n`pass:- your_password`",
        parse_mode="Markdown")

@bot.message_handler(func=lambda m:
    m.text and m.text.startswith("pass:-"))
def password_handler(message):
    if message.text.split("pass:-")[-1].strip() == PASSWORD:
        AUTHORIZED_USERS.add(message.from_user.id)
        bot.reply_to(message, "✅ Access granted.\nUse /help")
    else:
        bot.reply_to(message, "❌ Wrong password.")

@bot.message_handler(commands=["addacc"])
def add_account(message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return bot.reply_to(message, "❌ Unauthorized.")
    try:
        _, username, password = message.text.strip().split()
        result = try_login(message.from_user.id, username, password)
        bot.reply_to(message, result)
        bot.send_message(message.chat.id,
            f"📩 If login not success,\ncheck Gmail.\nSend: /code {username} 123456")
    except:
        bot.reply_to(message, "❌ Use: /addacc <username> <password>")

@bot.message_handler(commands=["code"])
def send_code(message):
    uid = message.from_user.id
    if uid not in AUTHORIZED_USERS:
        return bot.reply_to(message, "❌ Unauthorized.")
    try:
        _, username, code = message.text.strip().split()
        if username not in user_data[uid]["pending"]:
            return bot.reply_to(message, "⚠️ No verification pending.")
        cl, pwd = user_data[uid]["pending"].pop(username)
        cl.challenge_resolve(code)
        cl.login(username, pwd)
        user_data[uid]["clients"][username] = cl
        save_accounts()
        bot.reply_to(message, f"✅ Code verified, @{username} added.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=["setthread"])
def set_thread(message):
    uid = message.from_user.id
    if uid not in AUTHORIZED_USERS:
        return bot.reply_to(message, "❌ Unauthorized.")
    try:
        thread_id = message.text.strip().split()[1]
        user_data[uid]["thread_id"] = thread_id
        bot.reply_to(message, f"✅ Thread ID set:\n{thread_id}")
    except:
        bot.reply_to(message, "❌ Use: /setthread <thread_id>")

@bot.message_handler(commands=["setmsg"])
def set_custom_msg(message):
    uid = message.from_user.id
    if uid not in AUTHORIZED_USERS:
        return bot.reply_to(message, "❌ Unauthorized.")
    try:
        msg = message.text.split(" ", 1)[1]
        user_data[uid]["custom_msgs"].append(msg)
        bot.reply_to(message, "✅ Message added.")
    except:
        bot.reply_to(message, "❌ Use: /setmsg <your message>")

@bot.message_handler(commands=["delmsg"])
def delete_messages(message):
    uid = message.from_user.id
    if uid not in AUTHORIZED_USERS:
        return bot.reply_to(message, "❌ Unauthorized.")
    user_data[uid]["custom_msgs"] = []
    bot.reply_to(message, "🗑️ Messages cleared.")

@bot.message_handler(commands=["delacc"])
def delete_account(message):
    uid = message.from_user.id
    if uid not in AUTHORIZED_USERS:
        return bot.reply_to(message, "❌ Unauthorized.")
    try:
        _, username = message.text.strip().split()
        if username in user_data[uid]["clients"]:
            del user_data[uid]["clients"][username]
            save_accounts()
            bot.reply_to(message, f"✅ Removed @{username}")
        else:
            bot.reply_to(message, f"⚠️ Not found.")
    except:
        bot.reply_to(message, "❌ Use: /delacc <username>")

@bot.message_handler(commands=["startspam"])
def start_spam(message):
    uid = message.from_user.id
    if uid not in AUTHORIZED_USERS:
        return bot.reply_to(message, "❌ Unauthorized.")
    data = user_data[uid]
    if not data["thread_id"]:
        return bot.reply_to(message, "❌ Set thread ID first.")
    data["stop"] = False
    data["pause"] = False
    bot.send_message(message.chat.id, "🚀 Spam started...")

    def spam_loop(cl, label):
        count = 0
        start_time = time.time()
        while time.time() - start_time < spam_duration:
            if data["stop"]: break
            if data["pause"]:
                time.sleep(1)
                continue
            try:
                msgs = data["custom_msgs"] or default_msgs
                msg = random.choice(msgs)
                repeat = 20
                spam_text = (msg + "\n") * repeat
                cl.direct_send(
                    text=spam_text.strip(),
                    thread_ids=[data["thread_id"]]
                )
                count += 1
                print(f"{label} ✅ Sent #{count}")
                time.sleep(0.5)
            except Exception as e:
                print(f"{label} ❌ {e}")
                break

    for uname, cl in data["clients"].items():
        if cl:
            for i in range(3):
                threading.Thread(
                    target=spam_loop,
                    args=(cl, f"{uname}-T{i+1}")
                ).start()

@bot.message_handler(commands=["pause"])
def pause(message):
    uid = message.from_user.id
    if uid in AUTHORIZED_USERS:
        user_data[uid]["pause"] = True
        bot.reply_to(message, "⏸️ Paused.")

@bot.message_handler(commands=["resume"])
def resume(message):
    uid = message.from_user.id
    if uid in AUTHORIZED_USERS:
        user_data[uid]["pause"] = False
        bot.reply_to(message, "▶️ Resumed.")

@bot.message_handler(commands=["stopspam"])
def stop(message):
    uid = message.from_user.id
    if uid in AUTHORIZED_USERS:
        user_data[uid]["stop"] = True
        bot.reply_to(message, "🛑 Stopped.")

@bot.message_handler(commands=["status"])
def status(message):
    uid = message.from_user.id
    if uid not in AUTHORIZED_USERS: return
    d = user_data[uid]
    msgs_text = "\n".join(d["custom_msgs"]) or 'None'
    msg = f"""
✅ Accounts: {len(d['clients'])}
🧵 Thread ID: {d['thread_id'] or 'Not set'}
⏹️ Stop: {d['stop']}
⏸️ Pause: {d['pause']}
📝 Msgs:
{msgs_text}
🔐 Pending: {', '.join(d['pending'].keys()) or 'None'}
"""
    bot.reply_to(message, msg)

@bot.message_handler(commands=["help"])
def help_msg(message):
    bot.reply_to(message, """
🛠️ Commands:
/addacc <username> <password>
/code <username> <123456>
/setthread <thread_id>
/setmsg <your message>
/delmsg
/delacc <username>
/startspam
/pause
/resume
/stopspam
/status
""")

if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling()
import telebot
import json, os, threading, time, random
from collections import defaultdict
from instagrapi import Client
from instagrapi.exceptions import ChallengeRequired

bot = telebot.TeleBot(
    "8037278866:AAH3RfXVy0wQkImq_5A08uOhuwBcfj26rB0"
)

PASSWORD = "neeraj_20k"
AUTHORIZED_USERS = set()
spam_duration = 300
SAVE_PATH = "saved_accounts.json"

default_msgs = [
    "𝙉𝙀𝙀𝙍𝘼𝙅",
    "𓆰𝙉𝙀𝙀𝙍𝘼𝙅𓆩⃟🩸⃟𓆪𓆪𓆱",
    "𝗡𝗘𝗘𝗥𝗔𝗝𝗥𝗔𝗜𝗗 ",
]

user_data = defaultdict(lambda: {
    "clients": {},
    "pending": {},
    "thread_id": None,
    "custom_msgs": [],
    "stop": False,
    "pause": False
})

def save_accounts():
    data = {}
    for uid, d in user_data.items():
        data[str(uid)] = {
            "accounts": list(d["clients"].keys())
        }
    with open(SAVE_PATH, "w") as f:
        json.dump(data, f)

if os.path.exists(SAVE_PATH):
    with open(SAVE_PATH, "r") as f:
        loaded = json.load(f)
    for uid_str, d in loaded.items():
        uid = int(uid_str)
        for uname in d.get("accounts", []):
            user_data[uid]["clients"][uname] = None

def try_login(user_id, username, password):
    cl = Client()
    try:
        cl.login(username, password)
        user_data[user_id]["clients"][username] = cl
        save_accounts()
        return "✅ Login success"
    except ChallengeRequired:
        user_data[user_id]["pending"][username] = (cl, password)
        return f"⚠️ Verification needed for @{username}"
    except Exception as e:
        return f"❌ Login failed: {e}"

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message,
        "🔐 Send password:\n`pass:- your_password`",
        parse_mode="Markdown")

@bot.message_handler(func=lambda m:
    m.text and m.text.startswith("pass:-"))
def password_handler(message):
    if message.text.split("pass:-")[-1].strip() == PASSWORD:
        AUTHORIZED_USERS.add(message.from_user.id)
        bot.reply_to(message, "✅ Access granted.\nUse /help")
    else:
        bot.reply_to(message, "❌ Wrong password.")

@bot.message_handler(commands=["addacc"])
def add_account(message):
    if message.from_user.id not in AUTHORIZED_USERS:
        return bot.reply_to(message, "❌ Unauthorized.")
    try:
        _, username, password = message.text.strip().split()
        result = try_login(message.from_user.id, username, password)
        bot.reply_to(message, result)
        bot.send_message(message.chat.id,
            f"📩 If login not success,\ncheck Gmail.\nSend: /code {username} 123456")
    except:
        bot.reply_to(message, "❌ Use: /addacc <username> <password>")

@bot.message_handler(commands=["code"])
def send_code(message):
    uid = message.from_user.id
    if uid not in AUTHORIZED_USERS:
        return bot.reply_to(message, "❌ Unauthorized.")
    try:
        _, username, code = message.text.strip().split()
        if username not in user_data[uid]["pending"]:
            return bot.reply_to(message, "⚠️ No verification pending.")
        cl, pwd = user_data[uid]["pending"].pop(username)
        cl.challenge_resolve(code)
        cl.login(username, pwd)
        user_data[uid]["clients"][username] = cl
        save_accounts()
        bot.reply_to(message, f"✅ Code verified, @{username} added.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=["setthread"])
def set_thread(message):
    uid = message.from_user.id
    if uid not in AUTHORIZED_USERS:
        return bot.reply_to(message, "❌ Unauthorized.")
    try:
        thread_id = message.text.strip().split()[1]
        user_data[uid]["thread_id"] = thread_id
        bot.reply_to(message, f"✅ Thread ID set:\n{thread_id}")
    except:
        bot.reply_to(message, "❌ Use: /setthread <thread_id>")

@bot.message_handler(commands=["setmsg"])
def set_custom_msg(message):
    uid = message.from_user.id
    if uid not in AUTHORIZED_USERS:
        return bot.reply_to(message, "❌ Unauthorized.")
    try:
        msg = message.text.split(" ", 1)[1]
        user_data[uid]["custom_msgs"].append(msg)
        bot.reply_to(message, "✅ Message added.")
    except:
        bot.reply_to(message, "❌ Use: /setmsg <your message>")

@bot.message_handler(commands=["delmsg"])
def delete_messages(message):
    uid = message.from_user.id
    if uid not in AUTHORIZED_USERS:
        return bot.reply_to(message, "❌ Unauthorized.")
    user_data[uid]["custom_msgs"] = []
    bot.reply_to(message, "🗑️ Messages cleared.")

@bot.message_handler(commands=["delacc"])
def delete_account(message):
    uid = message.from_user.id
    if uid not in AUTHORIZED_USERS:
        return bot.reply_to(message, "❌ Unauthorized.")
    try:
        _, username = message.text.strip().split()
        if username in user_data[uid]["clients"]:
            del user_data[uid]["clients"][username]
            save_accounts()
            bot.reply_to(message, f"✅ Removed @{username}")
        else:
            bot.reply_to(message, f"⚠️ Not found.")
    except:
        bot.reply_to(message, "❌ Use: /delacc <username>")

@bot.message_handler(commands=["startspam"])
def start_spam(message):
    uid = message.from_user.id
    if uid not in AUTHORIZED_USERS:
        return bot.reply_to(message, "❌ Unauthorized.")
    data = user_data[uid]
    if not data["thread_id"]:
        return bot.reply_to(message, "❌ Set thread ID first.")
    data["stop"] = False
    data["pause"] = False
    bot.send_message(message.chat.id, "🚀 Spam started...")

    def spam_loop(cl, label):
        count = 0
        start_time = time.time()
        while time.time() - start_time < spam_duration:
            if data["stop"]: break
            if data["pause"]:
                time.sleep(1)
                continue
            try:
                msgs = data["custom_msgs"] or default_msgs
                msg = random.choice(msgs)
                repeat = 20
                spam_text = (msg + "\n") * repeat
                cl.direct_send(
                    text=spam_text.strip(),
                    thread_ids=[data["thread_id"]]
                )
                count += 1
                print(f"{label} ✅ Sent #{count}")
                time.sleep(0.5)
            except Exception as e:
                print(f"{label} ❌ {e}")
                break

    for uname, cl in data["clients"].items():
        if cl:
            for i in range(5):
                threading.Thread(
                    target=spam_loop,
                    args=(cl, f"{uname}-T{i+1}")
                ).start()

@bot.message_handler(commands=["pause"])
def pause(message):
    uid = message.from_user.id
    if uid in AUTHORIZED_USERS:
        user_data[uid]["pause"] = True
        bot.reply_to(message, "⏸️ Paused.")

@bot.message_handler(commands=["resume"])
def resume(message):
    uid = message.from_user.id
    if uid in AUTHORIZED_USERS:
        user_data[uid]["pause"] = False
        bot.reply_to(message, "▶️ Resumed.")

@bot.message_handler(commands=["stopspam"])
def stop(message):
    uid = message.from_user.id
    if uid in AUTHORIZED_USERS:
        user_data[uid]["stop"] = True
        bot.reply_to(message, "🛑 Stopped.")

@bot.message_handler(commands=["status"])
def status(message):
    uid = message.from_user.id
    if uid not in AUTHORIZED_USERS: return
    d = user_data[uid]
    msgs_text = "\n".join(d["custom_msgs"]) or 'None'
    msg = f"""
✅ Accounts: {len(d['clients'])}
🧵 Thread ID: {d['thread_id'] or 'Not set'}
⏹️ Stop: {d['stop']}
⏸️ Pause: {d['pause']}
📝 Msgs:
{msgs_text}
🔐 Pending: {', '.join(d['pending'].keys()) or 'None'}
"""
    bot.reply_to(message, msg)

@bot.message_handler(commands=["help"])
def help_msg(message):
    bot.reply_to(message, """
🛠️ Commands:
/addacc <username> <password>
/code <username> <123456>
/setthread <thread_id>
/setmsg <your message>
/delmsg
/delacc <username>
/startspam
/pause
/resume
/stopspam
/status
""")

if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling()
