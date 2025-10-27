@echo off
cd /d "%~dp0"
echo.
echo 🌕 Starting VORN Bot...
echo -----------------------------------

:: 1) ԱԿՏԻՎԱՑՆՈՒՄ ԵՆՔ VENV-Ը (Python 3.11-ով ստեղծված .venv)
call ".\.venv\Scripts\activate.bat"

:: 2) ՏԱՐԱԾԱԿԱՆ ՓՈՓՈԽԱԿԱՆՆԵՐԸ (քո իրական token-ը դրված է այստեղ)
set BOT_TOKEN=8419223502:AAFIH7f7FqwaLi-Gos07ZWe8u4HWG5sjO5M

:: 3) INTRO վիդեո. եթե դեռ չունես ուղիղ .mp4 հղում, թող դատարկ՝ տեքստային intro կցուցադրի
set INTRO_MEDIA_URL=

:: 4) ԳՈՐԾԱՐԿԵԼ ԲՈՏԸ հենց այս venv Python-ով
python bot.py

echo.
echo -----------------------------------
echo ✅ If you see "Bot is running...", open your bot in Telegram and type /start
echo (Press Ctrl+C here to stop the bot)
pause
