from dotenv import load_dotenv
import telebot, json, os, datetime, sys

# Получаю папку, в котором лежит файл
dir = os.path.dirname(os.path.abspath(__file__))

#Пути к файлам
exceptions_path = os.path.join(dir, "exceptions.json")
config_path = os.path.join(dir, "config.env")
prompts_path = os.path.join(dir, "prompts.txt")

# Читаю токен
load_dotenv(dotenv_path=config_path)
token = os.getenv("TOKEN")
admin = os.getenv("ADMIN")

# Получаем исключения
with open(exceptions_path, "r", encoding="utf-8") as file:
    data = json.load(file)
blacklist = data["blacklist"]


#Функция с чата гпт чтобы избегать случайной маркировки в MarkdownV2
def escape_md(text: str) -> str:
    escape_chars = r"_*[]()~`>#+-=|{}.!\\"
    return ''.join(f'\\{c}' if c in escape_chars else c for c in text)



# Правила муринского языка🛣
def murinost(word, vowels, letters, exceptions):
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


#Взаимодействия с юзером
def main():
    bot = telebot.TeleBot(token)

    @bot.message_handler(commands=['start'])
    def start_message(message):
        if (message.from_user.username not in blacklist):
            bot.send_message(message.chat.id, "Охайо друн, этность муринский переводчик, пиши текст для переводость!")

            #Записываю юзера
            with open(prompts_path, "a", encoding="utf-8") as file:
                file.write(f"\nПользователь @{message.from_user.username} запустил бота\n")
        else:
            bot.send_message(message.chat.id, "Тебя забанили🛑")

    #Команда, которая выводит все заимодействия с пользователями
    @bot.message_handler(commands=['checklast'])
    def print_last(message):
        username = message.from_user.username
        if (username not in blacklist and username == admin):
            if (username == admin):
                with open(prompts_path, "r", encoding="utf-8") as file:
                    content = file.read()
                if content != "":
                    bot.send_message(message.chat.id, f"Вот последние взаимодействия:||\n{escape_md(content)}||", parse_mode="MarkdownV2")
                else:
                    bot.send_message(message.chat.id, "Список пуст💨")
            else:
                bot.send_message(message.chat.id, "Эта команда доступна только для админов🛑")
        else:
            bot.send_message(message.chat.id, "Тебя забанили🛑")

    # Команда, которая очищает облако
    @bot.message_handler(commands=['dellast', 'deletelast', 'dl'])
    def delete_last(message):
        username = message.from_user.username
        if (username not in blacklist and username == admin):
            if (username == admin):
                with open(prompts_path, "w", encoding="utf-8") as file:
                    file.write("")
                    bot.send_message(message.chat.id, "Облако очищено💭")
            else:
                bot.send_message(message.chat.id, "Эта команда доступна только для админов🛑")
        else:
            bot.send_message(message.chat.id, "Тебя забанили🛑")

    # Принятия ввода и работа с ним
    @bot.message_handler(content_types=['text'])
    def handle_message(message):
        if (message.from_user.username not in blacklist):
            user_input = message.text.lower()

            #Очистка от лишних символов(в муринском языке не приветствеум их)
            symbols = [',', '.', '-', ':', ';', '?', '!', '%', '"', '/'
                       '1', '2', '3', '4', '5', '6', '7', '8', '9', '0']

            words = user_input.split()
            output = ""

            for word in words:
                for _ in word:
                    if _ in symbols:
                        new_word = word.replace(_, "")
                        if word in words:
                            index = words.index(word)
                            words[index] = new_word

            #Собираю результат
            for word in words:
                output = output + murinost(word, data["vowels"], data["letters"], data["exceptions"]) + " "

            bot.send_message(message.chat.id, output)

            #Записать запрос юзера и инфо про него
            with open(prompts_path, "a", encoding="utf-8") as file:
                date_time = datetime.datetime.fromtimestamp(message.date)
                date = date_time.strftime("%d.%m.%Y")
                time = date_time.strftime("%H:%M:%S")
                file.write(
                    f"\nНик: @{message.from_user.username}\n"
                    f"Дата: {date}\n"
                    f"Время: {time}\n"
                    f"Написал: {message.text}\n"
                    f"Ответ: {output}\n"
                )
        else:
            bot.send_message(message.chat.id, "Тебя забанили🛑")


    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()