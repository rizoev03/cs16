import valve.source.a2s
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Список серверов
SERVERS = [
    ("185.121.2.222", 27015),
    ("185.121.2.222", 27016),
    ("185.121.2.222", 27017),
    ("185.121.2.222", 27018),
    ("185.121.2.222", 27019),
]

# Подписчики
SUBSCRIBERS = []

# ID администратора
ADMIN_ID = 938543725

# Токен для Telegram-бота
TOKEN = '6607081317:AAEcvKVhk0Km5nSTFa6R3APikiUO6iIZN9g'


# Получение информации о сервере
def get_server_status(ip, port):
    try:
        with valve.source.a2s.ServerQuerier((ip, port)) as server:
            info = server.info()
            players = server.players()
            return {
                "name": info["server_name"],
                "map": info["map"],
                "players": players["players"],
                "max_players": info["max_players"],
            }
    except Exception as e:
        return None


# Команда /info для отображения всех серверов
def info(update: Update, context: CallbackContext):
    response = "📋 Информация о всех серверах:\n\n"
    for idx, (ip, port) in enumerate(SERVERS, start=1):
        status = get_server_status(ip, port)
        if status:
            response += (
                f"🔹 **Сервер {idx}**: {status['name']}\n"
                f"   Карта: {status['map']}\n"
                f"   Игроки: {len(status['players'])}/{status['max_players']}\n"
                f"   Команда: /sv{idx}\n\n"
            )
        else:
            response += f"🔹 Сервер {idx} недоступен\n\n"
    update.message.reply_text(response, parse_mode="Markdown")


# Генерация функций для индивидуальных серверов
def generate_server_command(idx, ip, port):
    def server_command(update: Update, context: CallbackContext):
        status = get_server_status(ip, port)
        if status:
            players_list = "\n".join(
                [f"   {i + 1}. {player['name']} ({player['score']} очков)" for i, player in
                 enumerate(status["players"])]
            )
            if not players_list:
                players_list = "   Нет активных игроков."
            response = (
                f"📌 **Сервер {idx}**: {status['name']}\n"
                f"Карта: {status['map']}\n"
                f"Игроки: {len(status['players'])}/{status['max_players']}\n\n"
                f"🎮 Список игроков:\n{players_list}"
            )
        else:
            response = f"❌ Сервер {idx} ({ip}:{port}) недоступен."
        update.message.reply_text(response, parse_mode="Markdown")

    return server_command


# Команда для подписки на рассылку
def subscribe(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id not in SUBSCRIBERS:
        SUBSCRIBERS.append(user_id)
        update.message.reply_text("Вы подписаны на уведомления о серверах.")
    else:
        update.message.reply_text("Вы уже подписаны.")


# Команда для отписки от рассылки
def unsubscribe(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id in SUBSCRIBERS:
        SUBSCRIBERS.remove(user_id)
        update.message.reply_text("Вы отписались от уведомлений.")
    else:
        update.message.reply_text("Вы не были подписаны.")


# Команда для рассылки от администратора
def broadcast(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    if user_id != ADMIN_ID:
        update.message.reply_text("⛔ У вас нет прав для выполнения этой команды.")
        return

    message = update.message.text.replace("/broadcast", "").strip()
    if not message:
        update.message.reply_text("❗ Укажите текст сообщения для рассылки.")
        return

    sent_count = 0
    for subscriber in SUBSCRIBERS:
        try:
            context.bot.send_message(chat_id=subscriber, text=f"📢 Сообщение от администратора:\n\n{message}")
            sent_count += 1
        except Exception:
            pass

    update.message.reply_text(f"✅ Сообщение отправлено {sent_count} подписчикам.")


# Основная настройка бота
def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Регистрация команд
    dispatcher.add_handler(CommandHandler("info", info))

    # Регистрация команд для индивидуальных серверов
    for idx, (ip, port) in enumerate(SERVERS, start=1):
        dispatcher.add_handler(CommandHandler(f"sv{idx}", generate_server_command(idx, ip, port)))

    dispatcher.add_handler(CommandHandler("subscribe", subscribe))
    dispatcher.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dispatcher.add_handler(CommandHandler("broadcast", broadcast))

    # Запуск бота
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
