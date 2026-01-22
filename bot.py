# freelancing_bot.py - Telegram Bot for Freelancing Platform
# Features: Project posting, freelancer profiles, bidding, messaging, payments, reviews
# Required: pip install python-telegram-bot==20.4 sqlite3 asyncio

import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, Document, PhotoSize
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ConversationHandler
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database setup
DB_NAME = "freelancing_bot.db"

def init_database():
    """Initialize SQLite database with all necessary tables"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            user_type TEXT CHECK(user_type IN ('client', 'freelancer')),
            bio TEXT,
            skills TEXT,
            portfolio TEXT,
            rating REAL DEFAULT 0.0,
            balance REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_verified BOOLEAN DEFAULT 0
        )
    ''')
    
    # Projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            budget_min REAL,
            budget_max REAL,
            category TEXT,
            deadline DATE,
            status TEXT DEFAULT 'open' CHECK(status IN ('open', 'in_progress', 'completed', 'cancelled')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES users (user_id)
        )
    ''')
    
    # Bids table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bids (
            bid_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            freelancer_id INTEGER,
            amount REAL,
            proposal TEXT,
            delivery_time INTEGER,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (project_id),
            FOREIGN KEY (freelancer_id) REFERENCES users (user_id)
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            project_id INTEGER,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users (user_id),
            FOREIGN KEY (receiver_id) REFERENCES users (user_id),
            FOREIGN KEY (project_id) REFERENCES projects (project_id)
        )
    ''')
    
    # Reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            reviewer_id INTEGER,
            reviewed_id INTEGER,
            rating INTEGER CHECK(rating BETWEEN 1 AND 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (project_id),
            FOREIGN KEY (reviewer_id) REFERENCES users (user_id),
            FOREIGN KEY (reviewed_id) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Conversation states
POST_PROJECT, PROJECT_TITLE, PROJECT_DESC, PROJECT_BUDGET, PROJECT_CATEGORY, PROJECT_DEADLINE = range(6)
BID_AMOUNT, BID_PROPOSAL, BID_DELIVERY = range(3)
EDIT_PROFILE, EDIT_BIO, EDIT_SKILLS, EDIT_PORTFOLIO = range(4)

# Main menu keyboard
def get_main_keyboard(user_type: str = None):
    """Return main menu keyboard based on user type"""
    if user_type == 'client':
        keyboard = [
            [KeyboardButton("📋 Post Project"), KeyboardButton("📊 My Projects")],
            [KeyboardButton("💰 My Balance"), KeyboardButton("📨 Messages")],
            [KeyboardButton("⭐ Reviews"), KeyboardButton("👤 Profile")]
        ]
    elif user_type == 'freelancer':
        keyboard = [
            [KeyboardButton("🔍 Find Projects"), KeyboardButton("💼 My Bids")],
            [KeyboardButton("💰 My Balance"), KeyboardButton("📨 Messages")],
            [KeyboardButton("⭐ Reviews"), KeyboardButton("👤 Profile")]
        ]
    else:
        keyboard = [
            [KeyboardButton("🚀 Get Started"), KeyboardButton("ℹ️ Help")]
        ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT user_type FROM users WHERE user_id = ?", (user.id,))
    result = cursor.fetchone()
    
    if not result:
        # New user - ask to choose role
        keyboard = [
            [InlineKeyboardButton("👔 Client", callback_data="role_client")],
            [InlineKeyboardButton("💻 Freelancer", callback_data="role_freelancer")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"👋 Welcome, {user.first_name}!\n\n"
            "Choose your role to get started with our freelancing platform:",
            reply_markup=reply_markup
        )
    else:
        user_type = result[0]
        await update.message.reply_text(
            f"👋 Welcome back, {user.first_name}!\n"
            f"Role: {user_type.capitalize()}\n\n"
            "Choose an option from the menu:",
            reply_markup=get_main_keyboard(user_type)
        )
    
    conn.close()

async def handle_role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle role selection callback"""
    query = update.callback_query
    await query.answer()
    
    user_type = query.data.split("_")[1]
    user = update.effective_user
    
    # Save user to database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, user_type)
        VALUES (?, ?, ?, ?, ?)
    ''', (user.id, user.username, user.first_name, user.last_name, user_type))
    conn.commit()
    conn.close()
    
    await query.edit_message_text(
        f"✅ You are now registered as a {user_type}!\n\n"
        f"Welcome to our freelancing platform, {user.first_name}!\n\n"
        "Choose an option from the menu:",
        reply_markup=get_main_keyboard(user_type)
    )

async def post_project_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start project posting conversation"""
    await update.message.reply_text(
        "📋 Let's post your project!\n\n"
        "First, please enter the project title:"
    )
    return POST_PROJECT

async def handle_project_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle project title input"""
    context.user_data['project_title'] = update.message.text
    await update.message.reply_text(
        "Great! Now please describe your project in detail:\n"
        "• What needs to be done?\n"
        "• What are the requirements?\n"
        "• Any specific skills needed?"
    )
    return PROJECT_DESC

async def handle_project_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle project description input"""
    context.user_data['project_desc'] = update.message.text
    await update.message.reply_text(
        "💰 What's your budget range?\n"
        "Please enter minimum and maximum budget (e.g., 100-500 USD):"
    )
    return PROJECT_BUDGET

async def handle_project_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle project budget input"""
    try:
        budget_range = update.message.text.replace('USD', '').replace('$', '').strip()
        min_budget, max_budget = map(float, budget_range.split('-'))
        context.user_data['budget_min'] = min_budget
        context.user_data['budget_max'] = max_budget
        
        # Show category options
        keyboard = [
            [InlineKeyboardButton("💻 Web Development", callback_data="cat_web")],
            [InlineKeyboardButton("📱 Mobile Development", callback_data="cat_mobile")],
            [InlineKeyboardButton("🎨 Design", callback_data="cat_design")],
            [InlineKeyboardButton("✍️ Writing", callback_data="cat_writing")],
            [InlineKeyboardButton("📊 Data Science", callback_data="cat_data")],
            [InlineKeyboardButton("🔧 Other", callback_data="cat_other")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🏷️ Select project category:",
            reply_markup=reply_markup
        )
        return PROJECT_CATEGORY
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format! Please use format: min-max (e.g., 100-500)"
        )
        return PROJECT_BUDGET

async def handle_project_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle project category selection"""
    query = update.callback_query
    await query.answer()
    
    category_map = {
        'cat_web': 'Web Development',
        'cat_mobile': 'Mobile Development',
        'cat_design': 'Design',
        'cat_writing': 'Writing',
        'cat_data': 'Data Science',
        'cat_other': 'Other'
    }
    
    context.user_data['category'] = category_map[query.data]
    await query.edit_message_text(
        "📅 When is the deadline for this project?\n"
        "Please enter date (YYYY-MM-DD):"
    )
    return PROJECT_DEADLINE

async def handle_project_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle project deadline input and save project"""
    try:
        deadline = datetime.strptime(update.message.text, '%Y-%m-%d').date()
        
        # Save project to database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO projects (client_id, title, description, budget_min, budget_max, category, deadline)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            update.effective_user.id,
            context.user_data['project_title'],
            context.user_data['project_desc'],
            context.user_data['budget_min'],
            context.user_data['budget_max'],
            context.user_data['category'],
            deadline
        ))
        project_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            f"✅ Project posted successfully!\n\n"
            f"📋 Project ID: {project_id}\n"
            f"📝 Title: {context.user_data['project_title']}\n"
            f"💰 Budget: ${context.user_data['budget_min']}-${context.user_data['budget_max']}\n"
            f"🏷️ Category: {context.user_data['category']}\n"
            f"📅 Deadline: {deadline}\n\n"
            "Freelancers can now bid on your project!",
            reply_markup=get_main_keyboard('client')
        )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid date format! Please use YYYY-MM-DD format"
        )
        return PROJECT_DEADLINE

async def find_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available projects for freelancers"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.project_id, p.title, p.budget_min, p.budget_max, p.category, p.deadline, u.first_name
        FROM projects p
        JOIN users u ON p.client_id = u.user_id
        WHERE p.status = 'open'
        ORDER BY p.created_at DESC
        LIMIT 10
    ''')
    
    projects = cursor.fetchall()
    conn.close()
    
    if not projects:
        await update.message.reply_text(
            "🔍 No open projects available at the moment.\n"
            "Check back later!"
        )
        return
    
    message = "🔍 **Available Projects:**\n\n"
    keyboard = []
    
    for project in projects:
        project_id, title, budget_min, budget_max, category, deadline, client_name = project
        message += f"📋 *Project #{project_id}*\n"
        message += f"📝 {title}\n"
        message += f"💰 Budget: ${budget_min}-${budget_max}\n"
        message += f"🏷️ Category: {category}\n"
        message += f"📅 Deadline: {deadline}\n"
        message += f"👤 Client: {client_name}\n\n"
        
        keyboard.append([InlineKeyboardButton(f"View Project #{project_id}", callback_data=f"project_{project_id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup)

async def handle_project_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle project view callback"""
    query = update.callback_query
    await query.answer()
    
    project_id = int(query.data.split("_")[1])
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.title, p.description, p.budget_min, p.budget_max, p.category, p.deadline, u.first_name, u.username
        FROM projects p
        JOIN users u ON p.client_id = u.user_id
        WHERE p.project_id = ?
    ''', (project_id,))
    
    project = cursor.fetchone()
    
    if not project:
        await query.edit_message_text("❌ Project not found!")
        return
    
    title, description, budget_min, budget_max, category, deadline, client_name, client_username = project
    
    message = f"📋 **Project #{project_id}**\n\n"
    message += f"📝 *Title:* {title}\n\n"
    message += f"📄 *Description:*\n{description}\n\n"
    message += f"💰 *Budget:* ${budget_min}-${budget_max}\n"
    message += f"🏷️ *Category:* {category}\n"
    message += f"📅 *Deadline:* {deadline}\n"
    message += f"👤 *Client:* {client_name} (@{client_username})\n\n"
    
    keyboard = [
        [InlineKeyboardButton("💼 Place Bid", callback_data=f"bid_{project_id}")],
        [InlineKeyboardButton("📨 Contact Client", callback_data=f"contact_{project_id}")],
        [InlineKeyboardButton("🔙 Back to Projects", callback_data="back_projects")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message, reply_markup=reply_markup)

async def start_bid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start bidding process"""
    query = update.callback_query
    await query.answer()
    
    project_id = int(query.data.split("_")[1])
    context.user_data['bid_project_id'] = project_id
    
    await query.edit_message_text(
        f"💼 Place your bid for Project #{project_id}\n\n"
        "💰 Enter your bid amount (in USD):"
    )
    return BID_AMOUNT

async def handle_bid_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bid amount input"""
    try:
        amount = float(update.message.text)
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be positive!")
            return BID_AMOUNT
        
        context.user_data['bid_amount'] = amount
        await update.message.reply_text(
            "✅ Amount recorded!\n\n"
            "📝 Now write your proposal:\n"
            "• Why are you the best fit?\n"
            "• What's your approach?\n"
            "• Relevant experience?"
        )
        return BID_PROPOSAL
        
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number!")
        return BID_AMOUNT

async def handle_bid_proposal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bid proposal input"""
    context.user_data['bid_proposal'] = update.message.text
    await update.message.reply_text(
        "⏰ How many days will you need to complete this project?"
    )
    return BID_DELIVERY

async def handle_bid_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bid delivery time and save bid"""
    try:
        delivery_time = int(update.message.text)
        if delivery_time <= 0:
            await update.message.reply_text("❌ Delivery time must be positive!")
            return BID_DELIVERY
        
        # Save bid to database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bids (project_id, freelancer_id, amount, proposal, delivery_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            context.user_data['bid_project_id'],
            update.effective_user.id,
            context.user_data['bid_amount'],
            context.user_data['bid_proposal'],
            delivery_time
        ))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            f"✅ Bid placed successfully!\n\n"
            f"💰 Amount: ${context.user_data['bid_amount']}\n"
            f"⏰ Delivery: {delivery_time} days\n\n"
            "The client will review your bid and contact you if interested.",
            reply_markup=get_main_keyboard('freelancer')
        )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number of days!")
        return BID_DELIVERY

async def view_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View user profile"""
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_type, bio, skills, portfolio, rating, balance, is_verified
        FROM users WHERE user_id = ?
    ''', (user_id,))
    
    user_data = cursor.fetchone()
    conn.close()
    
    if not user_data:
        await update.message.reply_text("❌ Profile not found!")
        return
    
    user_type, bio, skills, portfolio, rating, balance, is_verified = user_data
    
    message = f"👤 **Your Profile**\n\n"
    message += f"🏷️ *Type:* {user_type.capitalize()}\n"
    message += f"⭐ *Rating:* {rating:.1f}/5.0\n"
    message += f"💰 *Balance:* ${balance:.2f}\n"
    message += f"✅ *Verified:* {'Yes' if is_verified else 'No'}\n\n"
    
    if bio:
        message += f"📝 *Bio:* {bio}\n\n"
    if skills:
        message += f"🔧 *Skills:* {skills}\n\n"
    if portfolio:
        message += f"🌐 *Portfolio:* {portfolio}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Profile", callback_data="edit_profile")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup)

async def edit_profile_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start profile editing"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📝 Edit Bio", callback_data="edit_bio")],
        [InlineKeyboardButton("🔧 Edit Skills", callback_data="edit_skills")],
        [InlineKeyboardButton("🌐 Edit Portfolio", callback_data="edit_portfolio")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_profile")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("✏️ **Edit Profile**\n\nWhat would you like to edit?", reply_markup=reply_markup)

async def handle_message_handlers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle general message handlers"""
    text = update.message.text
    
    if text == "📋 Post Project":
        return await post_project_start(update, context)
    elif text == "🔍 Find Projects":
        return await find_projects(update, context)
    elif text == "👤 Profile":
        return await view_profile(update, context)
    elif text == "🚀 Get Started":
        return await start(update, context)
    elif text == "ℹ️ Help":
        await update.message.reply_text(
            "🤖 **Freelancing Bot Help**\n\n"
            "📋 **For Clients:**\n"
            "• Post projects with detailed requirements\n"
            "• Review freelancer bids\n"
            "• Manage payments and reviews\n\n"
            "💻 **For Freelancers:**\n"
            "• Browse and bid on projects\n"
            "• Build your profile and portfolio\n"
            "• Communicate with clients\n\n"
            "📞 Need support? Contact @admin"
        )
    else:
        await update.message.reply_text(
            "❓ I didn't understand that. Please use the menu buttons or type /help"
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.message.reply_text(
        "❌ Operation cancelled.\n"
        "Choose an option from the menu:",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END

def main():
    """Start the bot"""
    # Initialize database
    init_database()
    
    # Bot token
    bot_token = "8336359761:AAGQ9On9PKt7dM7PJGtC2C5AId2I4JQmCEc"
    
    # Create application
    application = Application.builder().token(bot_token).build()
    
    # Conversation handlers
    post_project_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📋 Post Project$"), post_project_start)],
        states={
            POST_PROJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_title)],
            PROJECT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_desc)],
            PROJECT_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_budget)],
            PROJECT_CATEGORY: [CallbackQueryHandler(handle_project_category)],
            PROJECT_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_project_deadline)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=True
    )
    
    bid_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_bid, pattern="^bid_")],
        states={
            BID_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bid_amount)],
            BID_PROPOSAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bid_proposal)],
            BID_DELIVERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bid_delivery)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=True
    )
    
    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(handle_role_selection, pattern="^role_"))
    application.add_handler(CallbackQueryHandler(handle_project_view, pattern="^project_"))
    application.add_handler(CallbackQueryHandler(edit_profile_start, pattern="^edit_profile$"))
    application.add_handler(post_project_conv)
    application.add_handler(bid_conv)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_handlers))
    
    # Start bot
    print("🚀 Freelancing Bot started!")
    application.run_polling()

if __name__ == '__main__':
    main()
