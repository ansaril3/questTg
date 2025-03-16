from config import bot
from handlers.game_handler import send_chapter
from handlers.stats_handler import show_characteristics
from handlers.inventory_handler import show_inventory
from handlers.instruction_handler import send_instruction

bot.polling()
