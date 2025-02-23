# Обработка инвентаря

# Просмотр инвентаря (с золотыми монетами)
@bot.message_handler(func=lambda message: message.text == "🎒 Инвентарь")
def show_inventory(message):
    chat_id = message.chat.id
    state = load_state(chat_id)

    inventory_text = "\n".join(f"🔹 {item}" for item in state["inventory"]) if state["inventory"] else "📭 Пусто"
    bot.send_message(chat_id, f"🎒 Ваш инвентарь:\n{inventory_text}\n\n💰 Золото: {state['gold']} монет")

    # После отображения инвентаря повторно отправляем клавиатуру действий
    send_options_keyboard(chat_id, chapters.get(state["chapter"]))
