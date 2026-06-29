from aiogram import Bot
from aiogram.types import BotCommand


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="start", description="Старт — что умеет бот"),
        BotCommand(command="meet", description="Создать новую встречу"),
        # BotCommand(command="link_meeting", description="Привязать встречу к чату"),
        # BotCommand(command="status", description="Кто заполнил слоты"),
        # BotCommand(command="my_slots", description="Заполнить слоты текстом (AI)"),
        # BotCommand(command="note", description="Сохранить заметку во время встречи"),
        # BotCommand(command="task", description="Назначить задачу участнику"),
        # BotCommand(command="end_meeting", description="Завершить встречу и получить итоги"),
        BotCommand(command="about", description="О боте"),
    ]
    await bot.set_my_commands(main_menu_commands)
