from dotenv import load_dotenv
import telebot, json, os, datetime, sys

# Получаю папку, в котором лежит файл
cur_dir = os.path.dirname(os.path.abspath(__file__))

#Пути к файлам
exceptions_path = os.path.join(cur_dir, "exceptions.json")
config_path = os.path.join(cur_dir, "config.env")
prompts_path = os.path.join(cur_dir, "prompts.txt")

# Читаю токен
load_dotenv(dotenv_path=config_path)
token = os.getenv("TOKEN")
admin = os.getenv("ADMIN").split()

# Получаем исключения
with open(exceptions_path, "r", encoding="utf-8") as file:
    data = json.load(file)
blacklist = data["blacklist"]


class Logger:
    @staticmethod
    def log(case, *data):
        # case = warning, info, error etc...

        date_time = datetime.datetime.now()
        date = date_time.strftime("%d.%m.%Y")
        time = date_time.strftime("%H:%M:%S")

        log_text = f"\n[{case}] [{date}/{time}]\n{'\n'.join(data)}\n"

        with open(prompts_path, "a", encoding="utf-8") as file:
            file.write(log_text)

    @staticmethod
    def clear():
        with open(prompts_path, "w") as file:
            file.write('')

    @staticmethod
    def get():
        with open(prompts_path, "r", encoding="utf-8") as file:
            text = file.read()
            return text


#Функция с чата гпт чтобы избегать случайной маркировки в MarkdownV2
def escape_md(text: str) -> str:
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    return ''.join(f'\\{c}' if c in escape_chars else c for c in text)

# Правила муринского языка🛣
def murinost(word):
    vowels, letters, exceptions = data["vowels"], data["letters"], data["exceptions"]

    if word in exceptions:
        return exceptions[word]

    if len(word) <= 3 or word.endswith(("сть", "шь")) or word[-1] == "ь" or word in exceptions.values():
        return word

    #Если заканчиваеться на гласную и "т" то добавляю префикс
    if word[-1] == "т" and word[-2] in vowels:
        prefix = "бурмалд"
        #Если вторая буква на гласная тогда "о" к префиксу
        if word[1] not in vowels:
            prefix = prefix + "о"
        #Возвращаю префикс с словом без первой буквы
        return prefix + word[1:]

    if word.endswith("инец"):
        return "бурмалдинец"

    #Если последния бука - согласная
    if word[-1] in letters:
        return word[:-1] + "сть"

    # Если последния бука - гласная
    if word[-1] in vowels:
        return word + "сть"

    #Если нихуя не подошло
    return word + "ость"

def translate(text):
    symbols = ",.-:;?!%\"'/\\1234567890"

    text = text.lower()
    text = "".join([i if i not in symbols else "" for i in text])
    text = text.split()

    translated = " ".join(murinost(word) for word in text) 

    return translated


# Принятия ввода
if __name__ == "__main__":
    bot = telebot.TeleBot(token)

    @bot.message_handler(commands=['start'])
    def start_message(message):
        if message.from_user.username in blacklist:
            bot.send_message(message.chat.id, "Тебя забанили🛑")

        bot.send_message(message.chat.id, "Охайо друн, этность муринский переводчик, пиши текст для переводость!")

        #Записываю юзера
        Logger.log("info", f"Пользователь @{message.from_user.username} запустил бота")

    #Команда, которая выводит все заимодействия с пользователями
    @bot.message_handler(commands=['checklast'])
    def print_last(message):
        username = message.from_user.username

        if username not in admin:
            return

        content = Logger.get()
        if content:
            bot.send_message(message.chat.id, f"Вот последние взаимодействия:||\n{escape_md(content)}||", parse_mode="MarkdownV2")

    # Команда, которая очищает облако
    @bot.message_handler(commands=['dellast', 'deletelast', 'dl'])
    def delete_last(message):
        username = message.from_user.username

        if username not in admin:
            return

        Logger.clear()

        bot.send_message(message.chat.id, "Облако очищено💭")

    @bot.message_handler(content_types=['text'])
    def translate_handler(message):
        if message.from_user.username in blacklist:
            bot.send_message(message.chat.id, "Тебя забанили🛑")
            return

        text = translate(message.text)
        bot.send_message(message.chat.id, text)
        
        #Записать запрос юзера и инфо про него
        Logger.log(
                "info",
                f"Ник: @{message.from_user.username}",
                f"Текст: {message.text}",
                f"Ответ: {text}"
        )
       
    bot.infinity_polling(skip_pending=True)

