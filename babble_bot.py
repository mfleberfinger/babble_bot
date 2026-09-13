import telebot
from mangle import Mangle
import random
import configparser
from datetime import datetime
import re
from time import time
from mangle import MangleMethod

# get config
config = configparser.ConfigParser()
config.read("babble_bot.cfg")

# create bot with key
bot = telebot.TeleBot(config['telegram_bot_api']['telegram_token'].strip())
me = bot.get_me()
bot_username = me.username
bot_mention = "@{}".format(bot_username).lower()

blacklist = set(["tlh-Qaak"])

m = Mangle(language="en",
           language_blacklist=blacklist,
           low=2,
           high=50)

freq = 0.1

times_to_mangle_info_messages = 2

# maps messageid -> message info dict (see mangle)
messages = {}

languages = set(m.languages) - blacklist

language = "en"

bracket_matcher = re.compile(r"^\[.*\]")
language_matcher = re.compile(r"[\w-]+")

# TODO put these in config (and update example!)
#low = 2
#high = 50

since = int(time())


def mentioned_bot(message):
    text = message.text or ""
    return bot_mention in text.lower()


def should_mangle(message):
    text = message.text or ""
    if int(message.date) <= since:
        return False
    if not text or "/info" in text:
        return False
    # Always respond in DMs, or in groups when @mentioned. Otherwise
    # randomly mangle (only possible if Group Privacy is disabled).
    if message.chat.type == "private" or mentioned_bot(message):
        return True
    return random.random() < freq


def send_to_chat(message, text, **kwargs):
    return bot.send_message(
        message.chat.id,
        text,
        message_thread_id=getattr(message, "message_thread_id", None),
        **kwargs)


@bot.message_handler(func=should_mangle)
def mangle_message(message):
    message_text, language_list = parse(message.text)

    method = None
    if language_list:
        method = MangleMethod.manual

    try:
        bot.send_chat_action(
            message.chat.id,
            "typing",
            message_thread_id=getattr(message, "message_thread_id", None))
        message_info = m.mangle(message_text,
                                method=method,
                                language_list=language_list)
    except Exception as e:
        print("mangle failed: {}".format(e))
        send_to_chat(message, "babble failed. try again?")
        return

    if message_info['all_messages'] is False:
        try:
            err = m.mangle("One or more languages not recognized.",
                           times=3,
                           method=MangleMethod.straight)['all_messages'][-1]
        except Exception:
            err = "One or more languages not recognized."
        send_to_chat(message, err)
        return

    sent = send_to_chat(message, message_info['all_messages'][-1])
    messages[sent.message_id] = message_info


@bot.message_handler(
    commands=['info'],
    func=lambda m: m.reply_to_message is not None and m.reply_to_message.
    message_id in messages and int(m.date) > since)
def handle_info(message):
    message_info = messages[message.reply_to_message.message_id]
    send_to_chat(
        message,
        "*{}:*\n{}\n".format(mangle_info("language picking method"),
                             mangle_info(message_info['method'])) +
        "*{}*:\n".format(mangle_info("all translations")) + "\n".join([
            "_({})_ {}".format(message_info['languages'][i],
                               message_info['all_messages'][i])
            for i in range(len(message_info['languages']))
        ]),
        parse_mode="Markdown")


def parse(text):
    '''
	Parses a message's text, performing a few tasks:
	- Remove instances of the bot mention
	- Parse a language list from the start of the message
	'''

    text = re.sub("@" + re.escape(bot_username) + " *",
                  "",
                  text,
                  flags=re.IGNORECASE)

    language_list_result = re.search(r"^\[.*\]", text)
    found_languages = None
    if language_list_result:
        language_list_string = language_list_result.group(0)[
            1:-1]  # remove brackets on the sides
        found_languages = re.findall(r"[\w-]+", language_list_string)
        text = re.sub(r"^\[.*\] *", "", text)

    return (text, None if not found_languages else list(found_languages))


def mangle_info(text):
    return m.mangle(text,
                    method=MangleMethod.straight,
                    times=times_to_mangle_info_messages)['all_messages'][-1]


if __name__ == "__main__":
    print("Bot started as @{}!".format(bot_username))
    if not me.can_read_all_group_messages:
        print(
            "Group Privacy is ON: the bot only receives @mentions, /commands, "
            "and replies to itself. Disable Group Privacy in @BotFather and "
            "re-add the bot to the group if you want random mangling.")
    bot.infinity_polling()  # Bot waits for events.
