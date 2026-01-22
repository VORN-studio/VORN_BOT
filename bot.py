import asyncio
import logging
import os
import threading
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import json

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "8336359761:AAGQ9On9PKt7dM7PJGtC2C5AId2I4JQmCEc"
ADMIN_ID = 8022643557

# База данных (в реальном проекте лучше использовать SQLite/PostgreSQL)
users = {}
orders = {}
freelancers = {}
order_id_counter = 1

# Создаем Flask приложение
app = Flask(__name__)
bot_instance = None
loop = None

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint для Telegram"""
    if bot_instance and loop:
        update = Update.de_json(request.get_json(), bot_instance.application.bot)
        asyncio.run_coroutine_threadsafe(bot_instance.application.process_update(update), loop)
    return 'OK'

@app.route('/')
def index():
    """Health check endpoint"""
    return 'Freelance Bot is running!'

class FreelanceBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("neworder", self.new_order_command))
        self.application.add_handler(CommandHandler("myorders", self.my_orders_command))
        self.application.add_handler(CommandHandler("profile", self.profile_command))
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name
        
        # Регистрация пользователя
        if user_id not in users:
            users[user_id] = {
                'username': username,
                'user_id': user_id,
                'role': None,  # 'customer' или 'freelancer'
                'balance': 0,
                'orders_count': 0,
                'registered_at': datetime.now().isoformat()
            }
        
        keyboard = [
            [InlineKeyboardButton("🛒 Я заказчик", callback_data="role_customer")],
            [InlineKeyboardButton("💼 Я фрилансер", callback_data="role_freelancer")],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
        ]
        
        await update.message.reply_text(
            f"👋 Добро пожаловать, {username}!\n\n"
            "Это бот для фриланс-работы. Вы можете:\n"
            "• 🛒 Размещать заказы (если вы заказчик)\n"
            "• 💼 Выполнять заказы (если вы фрилансер)\n\n"
            "Пожалуйста, выберите вашу роль:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """
🤖 *Помощь по боту*

📋 *Основные команды:*
/start - Начать работу с ботом
/neworder - Создать новый заказ
/myorders - Мои заказы
/profile - Мой профиль
/admin - Админ-панель (для админа)

🛒 *Для заказчиков:*
• Создавайте заказы с подробным описанием
• Указывайте бюджет и сроки
• Выбирайте исполнителей из предложений
• Оплачивайте выполненную работу

💼 *Для фрилансеров:*
• Просматривайте доступные заказы
• Откликайтесь на интересные проекты
• Выполняйте работу в срок
• Получайте оплату за заказы

💡 *Советы:*
• Чем подробнее описание заказа, тем больше откликов
• Указывайте реалистичные сроки и бюджет
• Своевременно отвечайте на сообщения

❓ *Нужна помощь?* Свяжитесь с администратором: @admin
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def new_order_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /neworder"""
        user_id = update.effective_user.id
        
        if user_id not in users or users[user_id]['role'] != 'customer':
            await update.message.reply_text(
                "❌ Только заказчики могут создавать заказы!\n"
                "Используйте /start для выбора роли."
            )
            return
        
        await update.message.reply_text(
            "📝 Создание нового заказа\n\n"
            "Пожалуйста, введите описание заказа в следующем формате:\n\n"
            "📋 *Название заказа*\n"
            "💰 *Бюджет (в рублях)*\n"
            "⏰ *Срок выполнения*\n"
            "📄 *Подробное описание*\n\n"
            "Пример:\n"
            "Создать сайт-визитку\n"
            "5000\n"
            "3 дня\n"
            "Нужен простой сайт-визитка для бизнеса с 3 страницами: главная, услуги, контакты."
        )
        
        # Устанавливаем состояние ожидания описания заказа
        context.user_data['waiting_for_order'] = True
    
    async def my_orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /myorders"""
        user_id = update.effective_user.id
        
        if user_id not in users:
            await update.message.reply_text("❌ Сначала зарегистрируйтесь: /start")
            return
        
        user_orders = [order for order in orders.values() if order['customer_id'] == user_id]
        
        if not user_orders:
            await update.message.reply_text("📭 У вас пока нет заказов")
            return
        
        text = "📋 *Ваши заказы:*\n\n"
        for order in user_orders:
            status_emoji = {"open": "🔍", "in_progress": "⚡", "completed": "✅", "cancelled": "❌"}
            text += f"🔹 *Заказ #{order['id']}*\n"
            text += f"📝 {order['title']}\n"
            text += f"💰 {order['budget']}₽ | {status_emoji.get(order['status'], '❓')} {order['status']}\n\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /profile"""
        user_id = update.effective_user.id
        
        if user_id not in users:
            await update.message.reply_text("❌ Сначала зарегистрируйтесь: /start")
            return
        
        user = users[user_id]
        role_text = {"customer": "🛒 Заказчик", "freelancer": "💼 Фрилансер"}.get(user['role'], "❓ Не определена")
        
        profile_text = f"""
👤 *Ваш профиль*

🆔 ID: {user_id}
👤 Имя: {user['username']}
🎭 Роль: {role_text}
💰 Баланс: {user['balance']}₽
📊 Заказов: {user['orders_count']}
📅 Регистрация: {user['registered_at'][:10]}
        """
        
        await update.message.reply_text(profile_text, parse_mode='Markdown')
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /admin"""
        user_id = update.effective_user.id
        
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ Доступ запрещен!")
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
            [InlineKeyboardButton("📋 Заказы", callback_data="admin_orders")],
            [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")]
        ]
        
        await update.message.reply_text(
            "🔧 *Админ-панель*\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        data = query.data
        
        if data == "role_customer":
            users[user_id]['role'] = 'customer'
            await query.edit_message_text(
                "✅ Вы зарегистрированы как *заказчик*!\n\n"
                "Теперь вы можете:\n"
                "• Создавать заказы (/neworder)\n"
                "• Просматривать свои заказы (/myorders)\n"
                "• Управлять профилем (/profile)",
                parse_mode='Markdown'
            )
            # Показать выбор категории для заказа
            await self.show_category_selection(query)
        
        elif data == "role_freelancer":
            users[user_id]['role'] = 'freelancer'
            await query.edit_message_text(
                "✅ Вы зарегистрированы как *фрилансер*!\n\n"
                "Теперь вы можете:\n"
                "• Просматривать доступные заказы\n"
                "• Откликаться на проекты\n"
                "• Управлять профилем (/profile)",
                parse_mode='Markdown'
            )
            # Показать выбор специализации
            await self.show_specialization_selection(query)
        
        elif data == "help":
            await self.help_command(update, context)
        
        elif data.startswith("cat_"):
            await self.handle_category_selection(query, data, context)
        
        elif data.startswith("spec_"):
            await self.handle_specialization_selection(query, data, context)
        
        elif data.startswith("order_"):
            await self.handle_order_action(query, data)
        
        elif data.startswith("admin_"):
            await self.handle_admin_action(query, data)
    
    async def show_category_selection(self, query):
        """Показать выбор категории для заказа"""
        keyboard = [
            [InlineKeyboardButton("💻 Программирование и IT", callback_data="cat_programming")],
            [InlineKeyboardButton("🎨 Дизайн и графика", callback_data="cat_design")],
            [InlineKeyboardButton("📸 Фотосъемка и видео", callback_data="cat_media")],
            [InlineKeyboardButton("✍️ Тексты и переводы", callback_data="cat_writing")],
            [InlineKeyboardButton("📊 Маркетинг и реклама", callback_data="cat_marketing")],
            [InlineKeyboardButton("🔧 Ремонт и строительство", callback_data="cat_construction")],
            [InlineKeyboardButton("🎵 Музыка и аудио", callback_data="cat_music")],
            [InlineKeyboardButton("📚 Образование и консультации", callback_data="cat_education")],
            [InlineKeyboardButton("🚗 Транспорт и логистика", callback_data="cat_transport")],
            [InlineKeyboardButton("🏠 Быт и услуги", callback_data="cat_services")]
        ]
        
        await query.message.reply_text(
            "🎯 *Выберите категорию вашего заказа:*\n\n"
            "Это поможет найти подходящих исполнителей для вашей задачи.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def handle_category_selection(self, query, data, context=None):
        """Обработка выбора категории заказа"""
        user_id = query.from_user.id
        cat_type = data.split("_")[1]
        
        # Словарь категорий
        categories = {
            "programming": "💻 Программирование и IT",
            "design": "🎨 Дизайн и графика",
            "media": "📸 Фотосъемка и видео",
            "writing": "✍️ Тексты и переводы",
            "marketing": "📊 Маркетинг и реклама",
            "construction": "🔧 Ремонт и строительство",
            "music": "🎵 Музыка и аудио",
            "education": "📚 Образование и консультации",
            "transport": "🚗 Транспорт и логистика",
            "services": "🏠 Быт и услуги"
        }
        
        cat_name = categories.get(cat_type, "❓ Неизвестная категория")
        
        # Сохраняем категорию пользователя
        if user_id in users:
            users[user_id]['category'] = cat_name
            users[user_id]['cat_type'] = cat_type
        
        await query.edit_message_text(
            f"✅ Вы выбрали категорию: {cat_name}\n\n"
            f"🎯 Теперь опишите подробно вашу задачу.\n\n"
            f"📝 *Пожалуйста, укажите:*\n\n"
            f"📋 *Что именно нужно сделать*\n"
            f"💰 *Ваш бюджет (в рублях)*\n"
            f"⏰ *Когда нужно выполнить*\n"
            f"📍 *Местоположение (если важно)*\n"
            f"📄 *Дополнительные требования*\n\n"
            f"⏰ Наш менеджер подберет для вас лучших исполнителей!",
            parse_mode='Markdown'
        )
        
        # Устанавливаем состояние ожидания описания задачи
        context.user_data['waiting_for_task_description'] = True
        context.user_data['selected_category'] = cat_type
    
    async def show_specialization_selection(self, query):
        """Показать выбор специализации для фрилансера"""
        keyboard = [
            [InlineKeyboardButton("💻 Программирование", callback_data="spec_programming")],
            [InlineKeyboardButton("📸 Фотосъемка", callback_data="spec_photography")],
            [InlineKeyboardButton("🎬 Монтаж видео", callback_data="spec_video_editing")],
            [InlineKeyboardButton("🎨 Дизайн", callback_data="spec_design")],
            [InlineKeyboardButton("✍️ Копирайтинг", callback_data="spec_copywriting")],
            [InlineKeyboardButton("📊 Маркетинг", callback_data="spec_marketing")],
            [InlineKeyboardButton("🔧 IT поддержка", callback_data="spec_it_support")],
            [InlineKeyboardButton("🎵 Музыка и звук", callback_data="spec_music")],
            [InlineKeyboardButton("📝 Переводы", callback_data="spec_translation")],
            [InlineKeyboardButton("🏗️ Строительство и ремонт", callback_data="spec_construction")]
        ]
        
        await query.message.reply_text(
            "🎯 *Выберите вашу специализацию:*\n\n"
            "Это поможет нам находить для вас наиболее релевантные заказы.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def handle_specialization_selection(self, query, data, context=None):
        """Обработка выбора специализации фрилансера"""
        user_id = query.from_user.id
        spec_type = data.split("_")[1]
        
        # Словарь специализаций
        specializations = {
            "programming": "💻 Программирование",
            "photography": "📸 Фотосъемка", 
            "video_editing": "🎬 Монтаж видео",
            "design": "🎨 Дизайн",
            "copywriting": "✍️ Копирайтинг",
            "marketing": "📊 Маркетинг",
            "it_support": "🔧 IT поддержка",
            "music": "🎵 Музыка и звук",
            "translation": "📝 Переводы",
            "construction": "🏗️ Строительство и ремонт"
        }
        
        spec_name = specializations.get(spec_type, "❓ Неизвестная специализация")
        
        # Сохраняем специализацию пользователя
        if user_id in users:
            users[user_id]['specialization'] = spec_name
            users[user_id]['spec_type'] = spec_type
        
        await query.edit_message_text(
            f"✅ Вы выбрали специализацию: {spec_name}\n\n"
            f"🎯 Теперь мы будем находить для вас заказы по этой специализации.\n\n"
            f"📝 *Для получения заказов, пожалуйста, предоставьте следующую информацию:*\n\n"
            f"👤 Ваше имя и фамилия\n"
            f"📞 Ваш Telegram username для связи\n"
            f"📧 Краткое описание вашего опыта\n"
            f"💰 Примерная цена за час работы\n\n"
            f"📸 *Прикрепите примеры ваших работ (если есть)*\n\n"
            f"⏰ Наш менеджер свяжется с вами в ближайшее время!",
            parse_mode='Markdown'
        )
        
        # Устанавливаем состояние ожидания контактной информации
        context.user_data['waiting_for_contact_info'] = True
        context.user_data['selected_spec'] = spec_type
    
    async def show_available_orders(self, query):
        """Показать доступные заказы для фрилансеров"""
        available_orders = [order for order in orders.values() if order['status'] == 'open']
        
        if not available_orders:
            await query.message.reply_text("📭 Сейчас нет доступных заказов")
            return
        
        text = "🔍 *Доступные заказы:*\n\n"
        keyboard = []
        
        for order in available_orders[:5]:  # Показываем первые 5 заказов
            text += f"🔹 *Заказ #{order['id']}*\n"
            text += f"📝 {order['title']}\n"
            text += f"💰 {order['budget']}₽ | ⏰ {order['deadline']}\n"
            text += f"📄 {order['description'][:100]}...\n\n"
            
            keyboard.append([InlineKeyboardButton(f"Откликнуться #{order['id']}", callback_data=f"respond_order_{order['id']}")])
        
        if keyboard:
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await query.message.reply_text(text, parse_mode='Markdown')
    
    async def handle_order_action(self, query, data):
        """Обработка действий с заказами"""
        user_id = query.from_user.id
        
        if data.startswith("respond_order_"):
            order_id = int(data.split("_")[2])
            if order_id in orders:
                order = orders[order_id]
                await query.message.reply_text(
                    f"✅ Вы откликнулись на заказ #{order_id}\n\n"
                    f"📝 {order['title']}\n"
                    f"💰 {order['budget']}₽\n\n"
                    "Ожидайте ответа от заказчика."
                )
                # Здесь можно добавить уведомление заказчику
    
    async def handle_admin_action(self, query, data):
        """Обработка админских действий"""
        if data == "admin_stats":
            stats = f"""
📊 *Статистика бота*

👥 Пользователей: {len(users)}
📋 Заказов: {len(orders)}
🛒 Заказчиков: {len([u for u in users.values() if u['role'] == 'customer'])}
💼 Фрилансеров: {len([u for u in users.values() if u['role'] == 'freelancer'])}
            """
            await query.message.reply_text(stats, parse_mode='Markdown')
        
        elif data == "admin_users":
            text = "👥 *Пользователи:*\n\n"
            for user in list(users.values())[:10]:  # Показываем первых 10
                role = {"customer": "🛒", "freelancer": "💼"}.get(user['role'], "❓")
                text += f"{role} {user['username']} (ID: {user['user_id']})\n"
            await query.message.reply_text(text, parse_mode='Markdown')
        
        elif data == "admin_orders":
            text = "📋 *Заказы:*\n\n"
            for order in list(orders.values())[:10]:  # Показываем первые 10
                status = {"open": "🔍", "in_progress": "⚡", "completed": "✅"}.get(order['status'], "❓")
                text += f"{status} Заказ #{order['id']}: {order['title']}\n"
            await query.message.reply_text(text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Проверяем, ожидаем ли мы описание заказа
        if context.user_data.get('waiting_for_order'):
            await self.process_order_creation(update, context, text)
            return
        
        # Проверяем, ожидаем ли мы контактную информацию от фрилансера
        if context.user_data.get('waiting_for_contact_info'):
            await self.process_contact_info(update, context, text)
            return
        
        # Проверяем, ожидаем ли мы описание задачи от заказчика
        if context.user_data.get('waiting_for_task_description'):
            await self.process_task_description(update, context, text)
            return
        
        # Другие обработки сообщений...
        await update.message.reply_text(
            "🤔 Я не понял вашу команду.\n"
            "Используйте /help для просмотра доступных команд."
        )
    
    async def process_task_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Обработка описания задачи от заказчика"""
        user_id = update.effective_user.id
        
        # Сохраняем описание задачи
        if user_id in users:
            users[user_id]['task_description'] = text
            users[user_id]['task_date'] = datetime.now().isoformat()
        
        # Сброс состояния
        context.user_data['waiting_for_task_description'] = False
        
        # Отправляем подтверждение
        await update.message.reply_text(
            "✅ *Ваша задача принята в обработку!*\n\n"
            "📝 Описание вашей задачи сохранено.\n"
            "⏰ Наш менеджер изучит информацию и свяжется с вами в ближайшее время.\n\n"
            "🎯 Мы подберем для вас лучших исполнителей!\n\n"
            "💡 *Совет:* Чем подробнее описание, тем точнее будет подбор исполнителей.",
            parse_mode='Markdown'
        )
        
        # Отправляем уведомление администратору
        try:
            user = users[user_id]
            cat_name = user.get('category', 'Не указана')
            
            admin_message = f"""
🔔 *Новый заказ от клиента!*

👤 Имя: {user['username']}
🆔 ID: {user_id}
🎯 Категория: {cat_name}
� Описание задачи:
{text}
📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}

📝 Свяжитесь с клиентом для уточнения деталей.
            """
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_message,
                parse_mode='Markdown'
            )
        except:
            pass  # Игнорируем ошибки доставки
        
    async def process_contact_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Обработка контактной информации от фрилансера"""
        user_id = update.effective_user.id
        
        # Сохраняем контактную информацию
        if user_id in users:
            users[user_id]['contact_info'] = text
            users[user_id]['contact_info_date'] = datetime.now().isoformat()
        
        # Сброс состояния
        context.user_data['waiting_for_contact_info'] = False
        
        # Отправляем подтверждение
        await update.message.reply_text(
            "✅ *Спасибо за информацию!*\n\n"
            "📝 Ваши данные сохранены.\n"
            "⏰ Наш менеджер свяжется с вами в ближайшее время.\n\n"
            "🎯 Мы будем уведомлять вас о релевантных заказах.\n\n"
            "💡 *Совет:* Чем подробнее ваша информация, тем больше шансов получить заказы!",
            parse_mode='Markdown'
        )
        
        # Отправляем уведомление администратору
        try:
            user = users[user_id]
            spec_name = user.get('specialization', 'Не указана')
            
            admin_message = f"""
🔔 *Новый фрилансер зарегистрирован!*

👤 Имя: {user['username']}
🆔 ID: {user_id}
🎯 Специализация: {spec_name}
📧 Контактная информация:
{text}
📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}

📝 Свяжитесь с фрилансером для верификации.
            """
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_message,
                parse_mode='Markdown'
            )
        except:
            pass  # Игнорируем ошибки доставки
    
    async def process_order_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Обработка создания нового заказа"""
        global order_id_counter
        
        lines = text.strip().split('\n')
        if len(lines) != 4:
            await update.message.reply_text(
                "❌ Неверный формат! Пожалуйста, введите:\n"
                "📋 Название заказа\n"
                "💰 Бюджет\n"
                "⏰ Срок\n"
                "📄 Описание"
            )
            return
        
        try:
            title = lines[0].strip()
            budget = int(lines[1].strip())
            deadline = lines[2].strip()
            description = lines[3].strip()
            
            # Создание заказа
            order = {
                'id': order_id_counter,
                'customer_id': update.effective_user.id,
                'title': title,
                'budget': budget,
                'deadline': deadline,
                'description': description,
                'status': 'open',
                'created_at': datetime.now().isoformat(),
                'responses': []
            }
            
            orders[order_id_counter] = order
            order_id_counter += 1
            
            # Обновление статистики пользователя
            users[update.effective_user.id]['orders_count'] += 1
            
            # Сброс состояния
            context.user_data['waiting_for_order'] = False
            
            confirmation_text = f"""
✅ *Заказ успешно создан!*

📋 *Заказ #{order['id']}*
📝 {title}
💰 {budget}₽
⏰ {deadline}
📄 {description}

🔍 Ваш заказ теперь доступен для фрилансеров!
            """
            
            await update.message.reply_text(confirmation_text, parse_mode='Markdown')
            
            # Уведомление фрилансеров (в реальном проекте)
            for user_id, user in users.items():
                if user['role'] == 'freelancer':
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"🔔 *Новый заказ!*\n\n📋 Заказ #{order['id']}: {title}\n💰 {budget}₽",
                            parse_mode='Markdown'
                        )
                    except:
                        pass  # Игнорируем ошибки доставки
                        
        except ValueError:
            await update.message.reply_text("❌ Бюджет должен быть числом!")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка при создании заказа: {str(e)}")
    
    async def run(self):
        """Запуск бота"""
        logger.info("Запуск фриланс-бота...")
        
        # Получаем URL из переменных окружения (для Render)
        webhook_url = os.environ.get('RENDER_EXTERNAL_URL')
        if webhook_url:
            webhook_url = f"{webhook_url}/webhook"
            logger.info(f"Установка webhook: {webhook_url}")
            await self.application.bot.set_webhook(url=webhook_url)
            await self.application.initialize()
            await self.application.start()
            logger.info("Бот запущен в режиме webhook!")
        else:
            # Локальный запуск с polling
            await self.application.updater.start_polling()
            logger.info("Бот запущен в режиме polling!")

# Основная функция
async def run_bot():
    """Запуск бота в asyncio loop"""
    global bot_instance, loop
    bot_instance = FreelanceBot()
    
    # Получаем URL из переменных окружения (для Render)
    webhook_url = os.environ.get('RENDER_EXTERNAL_URL')
    if webhook_url:
        webhook_url = f"{webhook_url}/webhook"
        logger.info(f"Установка webhook: {webhook_url}")
        await bot_instance.application.bot.set_webhook(url=webhook_url)
        await bot_instance.application.initialize()
        await bot_instance.application.start()
        logger.info("Бот запущен в режиме webhook!")
        
        # Держим loop активным
        while True:
            await asyncio.sleep(1)
    else:
        # Локальный запуск с polling
        await bot_instance.application.initialize()
        await bot_instance.application.start()
        await bot_instance.application.updater.start_polling()
        logger.info("Бот запущен в режиме polling!")


def start_flask():
    """Запуск Flask сервера"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    try:
        webhook_url = os.environ.get('RENDER_EXTERNAL_URL')
        if webhook_url:
            # Запускаем asyncio loop в отдельном потоке
            def run_loop():
                global loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(run_bot())
            
            bot_thread = threading.Thread(target=run_loop, daemon=True)
            bot_thread.start()
            
            # Запускаем Flask в основном потоке
            start_flask()
        else:
            # Локальный запуск
            asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("Бот остановлен")
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")