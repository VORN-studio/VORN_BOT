# 🤖 Freelancing Telegram Bot

A comprehensive Telegram bot for freelancing platforms that connects clients with freelancers.

## 🚀 Features

### For Clients 👔
- **Post Projects**: Create detailed project listings with budget, deadline, and requirements
- **Manage Bids**: Review and accept/reject freelancer proposals
- **Track Progress**: Monitor project status and communicate with freelancers
- **Payment Management**: Handle secure payments and transactions
- **Review System**: Rate and review freelancers after project completion

### For Freelancers 💻
- **Browse Projects**: Find relevant projects based on skills and category
- **Place Bids**: Submit competitive proposals with pricing and delivery time
- **Profile Management**: Build professional profiles with skills and portfolio
- **Messaging**: Direct communication with clients
- **Earnings Tracking**: Monitor income and payment history

### General Features 🌟
- **User Verification**: Verified freelancer badges for trusted professionals
- **Rating System**: 5-star rating system for both clients and freelancers
- **Category System**: Organized project categories (Web Dev, Mobile, Design, etc.)
- **Real-time Notifications**: Instant updates for bids, messages, and project changes
- **Secure Database**: SQLite database with proper data management

## 📋 Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up Telegram Bot Token
1. Create a bot with [@BotFather](https://t.me/botfather) on Telegram
2. Get your bot token
3. Set environment variable:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

### 3. Run the Bot
```bash
python bot.py
```

## 🗄️ Database Structure

The bot uses SQLite with the following tables:
- **users**: User profiles and account information
- **projects**: Project listings and details
- **bids**: Freelancer proposals and bids
- **messages**: Communication between users
- **reviews**: Ratings and feedback system

## 🎯 Bot Commands

### General Commands
- `/start` - Begin using the bot and select your role
- `/help` - Show help information
- `/cancel` - Cancel current operation

### Menu Options
- **📋 Post Project** (Clients) - Create a new project listing
- **🔍 Find Projects** (Freelancers) - Browse available projects
- **💼 My Bids** (Freelancers) - View your active bids
- **📊 My Projects** (Clients) - Manage your posted projects
- **👤 Profile** - View and edit your profile
- **💰 My Balance** - Check account balance
- **📨 Messages** - View conversations
- **⭐ Reviews** - See ratings and reviews

## 🔧 Configuration

### Environment Variables
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token (required)

### Database Configuration
The bot automatically creates a SQLite database file `freelancing_bot.db` on first run.

## 📝 Project Categories

- 💻 Web Development
- 📱 Mobile Development  
- 🎨 Design
- ✍️ Writing
- 📊 Data Science
- 🔧 Other

## 🛡️ Security Features

- User authentication through Telegram
- Secure database operations
- Input validation and sanitization
- Role-based access control
- Transaction logging

## 🚀 Deployment

### Local Development
```bash
python bot.py
```

### Production (Recommended)
- Use a process manager like `pm2` or `systemd`
- Set up proper logging
- Configure backup for the database
- Use environment variables for sensitive data

## 📞 Support

For support or questions:
- Contact the bot administrator
- Check the `/help` command in the bot
- Review this documentation

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is open source and available under the MIT License.
