import logging
import os
import time

from dotenv import dotenv_values, load_dotenv
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv(".env")

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")
TG_TOKEN = os.getenv("TG_TOKEN")
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

from notion_client import Client

# Obtain the `token_v2` value by inspecting your browser cookies on a logged-in (non-guest) session on Notion.so
notion = Client(auth=NOTION_TOKEN)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


def get_plain_test(json_obj):
    try:
        return json_obj["properties"]["Name"]["title"][0]["plain_text"]
    except:
        pass

    try:
        return json_obj["properties"]["title"]["title"][0]["plain_text"]
    except:
        pass

    try:
        return json_obj["title"][0]["plain_text"]
    except:
        pass


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    start = time.time()
    query = update.message.text
    result = notion.databases.query(DATABASE_ID, filter={
        "property": "Name",
        "title": {
            "contains": query
        }
    })
    results = result["results"]

    database_result_tuple = [(x["url"], get_plain_test(x)) for x in results]

    search_result = notion.search(query=query)

    try:
        search_result_tuple = [(x["url"], get_plain_test(x)) for x in
                               search_result["results"]]
    except:
        logger.exception(f"Error with {search_result['results']}")
        raise

    response = '\n\n'.join([f"{x[1]} / {x[0]}" for x in search_result_tuple + database_result_tuple])
    stop = time.time()
    logger.info(f"{stop-start:.2f}s {query=}")
    await update.message.reply_text(response or "Ничего не нашлось")


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TG_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
