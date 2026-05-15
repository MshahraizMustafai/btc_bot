import os
import logging
import requests
import xml.etree.ElementTree as ET
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

BOT_TOKEN = os.environ.get("BOT_TOKEN")

CHAT_IDS = []

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PKT = pytz.timezone("Asia/Karachi")

# ============ BTC PRICE ============
def get_btc_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true", timeout=10)
        data = r.json()
        price = data["bitcoin"]["usd"]
        change = data["bitcoin"]["usd_24h_change"]
        emoji = "🟢" if change > 0 else "🔴"
        return f"₿ *BTC Price:* ${price:,.0f}\n{emoji} *24h Change:* {change:.2f}%"
    except:
        return "⚠️ Price fetch nahi hua"

# ============ FEAR & GREED ============
def get_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/", timeout=10)
        data = r.json()["data"][0]
        value = data["value"]
        label = data["value_classification"]
        if int(value) >= 75:
            emoji = "🤑"
        elif int(value) >= 55:
            emoji = "😊"
        elif int(value) >= 45:
            emoji = "😐"
        elif int(value) >= 25:
            emoji = "😨"
        else:
            emoji = "😱"
        return f"{emoji} *Fear & Greed:* {value}/100 ({label})"
    except:
        return "⚠️ Fear & Greed fetch nahi hua"

# ============ BTC NEWS ============
def get_btc_news():
    news_list = []
    feeds = [
        "https://cointelegraph.com/rss/tag/bitcoin",
        "https://coindesk.com/arc/outboundfeeds/rss/",
    ]
    for url in feeds:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(r.content)
            items = root.findall(".//item")
            for item in items[:3]:
                title = item.find("title").text
                link = item.find("link").text
                news_list.append(f"📰 [{title}]({link})")
            if len(news_list) >= 5:
                break
        except:
            continue
    if news_list:
        return "\n\n".join(news_list[:5])
    return "⚠️ News fetch nahi hui"

# ============ FULL UPDATE ============
def get_full_update():
    price = get_btc_price()
    fg = get_fear_greed()
    news = get_btc_news()
    msg = f"""
🔥 *BTC MARKET UPDATE*
━━━━━━━━━━━━━━━
{price}
{fg}
━━━━━━━━━━━━━━━
📡 *Latest BTC News:*

{news}
━━━━━━━━━━━━━━━
🕐 _Pakistan Time Update_
"""
    return msg

# ============ COMMANDS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in CHAT_IDS:
        CHAT_IDS.append(chat_id)
    await update.message.reply_text(
        "🤖 *BTC Bot Active!*\n\n"
        "Commands:\n"
        "/btc — Live Price\n"
        "/news — Latest News\n"
        "/trend — Market Trend\n"
        "/update — Full Update\n\n"
        "⏰ Auto updates: 2PM, 6PM, 9PM PKT",
        parse_mode="Markdown"
    )

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in CHAT_IDS:
        CHAT_IDS.append(chat_id)
    price = get_btc_price()
    fg = get_fear_greed()
    await update.message.reply_text(f"{price}\n{fg}", parse_mode="Markdown")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in CHAT_IDS:
        CHAT_IDS.append(chat_id)
    await update.message.reply_text(get_btc_news(), parse_mode="Markdown", disable_web_page_preview=True)

async def trend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in CHAT_IDS:
        CHAT_IDS.append(chat_id)
    try:
        r = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
        data = r.json()["data"]
        btc_dom = data["market_cap_percentage"]["btc"]
        total_mc = data["total_market_cap"]["usd"]
        change = data["market_cap_change_percentage_24h_usd"]
        trend_emoji = "🐂 Bullish" if change > 0 else "🐻 Bearish"
        msg = f"""
📊 *Market Trend*
━━━━━━━━━━━━━━━
{trend_emoji}
💰 *Total Market Cap:* ${total_mc/1e12:.2f}T
₿ *BTC Dominance:* {btc_dom:.1f}%
📈 *24h Change:* {change:.2f}%
"""
        await update.message.reply_text(msg, parse_mode="Markdown")
    except:
        await update.message.reply_text("⚠️ Trend fetch nahi hua")

async def update_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in CHAT_IDS:
        CHAT_IDS.append(chat_id)
    await update.message.reply_text(get_full_update(), parse_mode="Markdown", disable_web_page_preview=True)

# ============ AUTO UPDATES ============
async def send_auto_update(context: ContextTypes.DEFAULT_TYPE):
    msg = get_full_update()
    for chat_id in CHAT_IDS:
        try:
            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown", disable_web_page_preview=True)
        except:
            pass

# ============ MAIN ============
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("trend", trend))
    app.add_handler(CommandHandler("update", update_cmd))

    scheduler = AsyncIOScheduler(timezone=PKT)
    scheduler.add_job(send_auto_update, "cron", hour=14, minute=0, args=[app])
    scheduler.add_job(send_auto_update, "cron", hour=18, minute=0, args=[app])
    scheduler.add_job(send_auto_update, "cron", hour=21, minute=0, args=[app])
    scheduler.start()

    logger.info("Bot chalu ho gaya!")
    app.run_polling()

if __name__ == "__main__":
    main()
