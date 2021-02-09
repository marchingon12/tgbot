import html
import random
import re
import subprocess
import sys
import os
from typing import Optional, List
from requests import get
from html import escape
from datetime import datetime

from io import BytesIO
from random import randint
import requests as r

from telegram import (
    Message,
    Chat,
    MessageEntity,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ParseMode,
    ChatAction,
    TelegramError,
    MAX_MESSAGE_LENGTH,
)

from telegram.ext import CommandHandler, CallbackQueryHandler, Filters
from telegram.utils.helpers import escape_markdown, mention_html
from telegram.error import BadRequest

from tg_bot import (
    dispatcher,
    OWNER_ID,
    TOKEN,
    SUDO_USERS,
    SUPPORT_USERS,
    WHITELIST_USERS,
)
from tg_bot.__main__ import STATS, USER_INFO, GDPR
from tg_bot.modules.disable import (
    DisableAbleCommandHandler,
    DisableAbleMessageHandler,
)
from tg_bot.modules.helper_funcs.extraction import extract_user
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.alternate import typing_action, send_action
import tg_bot.modules.helper_funcs.fun_strings as fun


@typing_action
def get_id(update, context):
    args = context.args
    user_id = extract_user(update.effective_message, args)
    if user_id:
        if (
            update.effective_message.reply_to_message
            and update.effective_message.reply_to_message.forward_from
        ):
            user1 = update.effective_message.reply_to_message.from_user
            user2 = update.effective_message.reply_to_message.forward_from
            update.effective_message.reply_text(
                "The original sender, {}, has an ID of `{}`.\nThe forwarder, {}, has an ID of `{}`.".format(
                    escape_markdown(user2.first_name),
                    user2.id,
                    escape_markdown(user1.first_name),
                    user1.id,
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            user = context.bot.get_chat(user_id)
            update.effective_message.reply_text(
                "{}'s id is `{}`.".format(escape_markdown(user.first_name), user.id),
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == "private":
            update.effective_message.reply_text(
                "Your id is `{}`.".format(chat.id),
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            update.effective_message.reply_text(
                "This group's id is `{}`.".format(chat.id),
                parse_mode=ParseMode.MARKDOWN,
            )


def info(update, context):
    args = context.args
    msg = update.effective_message  # type: Optional[Message]
    user_id = extract_user(update.effective_message, args)
    chat = update.effective_chat

    if user_id:
        user = context.bot.get_chat(user_id)

    elif not msg.reply_to_message and not args:
        user = msg.from_user

    elif (
        not msg.reply_to_message
        and len(args) >= 1
        and not args[0].startswith("@")
        and not args[0].isdigit()
        and not msg.parse_entities([MessageEntity.TEXT_MENTION])
    ):
        msg.reply_text("I can't extract a user from this.")
        return

    else:
        return

    del_msg = msg.reply_text(
        "Hold tight while I steal some data from <b>FBI Database</b>...",
        parse_mode=ParseMode.HTML,
    )

    text = (
        "<b>USER INFO</b>:"
        "\n\nID: <code>{}</code>"
        "\nFirst Name: {}".format(user.id, html.escape(user.first_name))
    )

    if user.last_name:
        text += "\nLast Name: {}".format(html.escape(user.last_name))

    if user.username:
        text += "\nUsername: @{}".format(html.escape(user.username))

    text += "\nPermanent user link: {}".format(mention_html(user.id, "link"))

    text += "\nNumber of profile pics: {}".format(
        context.bot.get_user_profile_photos(user.id).total_count
    )

    if user.id == OWNER_ID:
        text += "\n\nAye this guy is my owner.\nI would never do anything against him!"

    elif user.id in SUDO_USERS:
        text += (
            "\n\nThis person is one of my sudo users! "
            "Nearly as powerful as my owner - so watch it."
        )

    elif user.id in SUPPORT_USERS:
        text += (
            "\n\nThis person is one of my support users! "
            "Not quite a sudo user, but can still gban you off the map."
        )

    elif user.id in WHITELIST_USERS:
        text += (
            "\n\nThis person has been whitelisted! "
            "That means I'm not allowed to ban/kick them."
        )

    try:
        memstatus = chat.get_member(user.id).status
        if memstatus == "administrator" or memstatus == "creator":
            result = context.bot.get_chat_member(chat.id, user.id)
            if result.custom_title:
                text += f"\n\nThis user has custom title <b>{result.custom_title}</b> in this chat."
    except BadRequest:
        pass

    for mod in USER_INFO:
        try:
            mod_info = mod.__user_info__(user.id).strip()
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    try:
        profile = context.bot.get_user_profile_photos(user.id).photos[0][-1]
        context.bot.sendChatAction(chat.id, "upload_photo")
        context.bot.send_photo(
            chat.id,
            photo=profile,
            caption=(text),
            parse_mode=ParseMode.HTML,
        )
    except IndexError:
        context.bot.sendChatAction(chat.id, "typing")
        msg.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )
    finally:
        del_msg.delete()


@typing_action
def echo(update, context):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)
    message.delete()


@typing_action
def gdpr(update, context):
    update.effective_message.reply_text("Deleting identifiable data...")
    for mod in GDPR:
        mod.__gdpr__(update.effective_user.id)

    update.effective_message.reply_text(
        "Your personal data has been deleted.\n\nNote that this will not unban "
        "you from any chats, as that is telegram data, not bot data. "
        "Flooding, warns, and gbans are also preserved, as of "
        "[this](https://ico.org.uk/for-organisations/guide-to-the-general-data-protection-regulation-gdpr/individual-rights/right-to-erasure/), "
        "which clearly states that the right to erasure does not apply "
        '"for the performance of a task carried out in the public interest", as is '
        "the case for the aforementioned pieces of data.",
        parse_mode=ParseMode.MARKDOWN,
    )


MARKDOWN_HELP = """
Markdown is a very powerful formatting tool supported by telegram. {} has some enhancements, to make sure that \
saved messages are correctly parsed, and to allow you to create buttons.

- <code>_italic_</code>: wrapping text with '_' will produce italic text
- <code>*bold*</code>: wrapping text with '*' will produce bold text
- <code>`code`</code>: wrapping text with '`' will produce monospaced text, also known as 'code'
- <code>~strike~</code> wrapping text with '~' will produce strikethrough text
- <code>--underline--</code> wrapping text with '--' will produce underline text
- <code>[sometext](someURL)</code>: this will create a link - the message will just show <code>sometext</code>, \
and tapping on it will open the page at <code>someURL</code>.
EG: <code>[test](example.com)</code>

- <code>[buttontext](buttonurl:someURL)</code>: this is a special enhancement to allow users to have telegram \
buttons in their markdown. <code>buttontext</code> will be what is displayed on the button, and <code>someurl</code> \
will be the url which is opened.
EG: <code>[This is a button](buttonurl:example.com)</code>

If you want multiple buttons on the same line, use :same, as such:
<code>[one](buttonurl://example.com)
[two](buttonurl://google.com:same)</code>
This will create two buttons on a single line, instead of one button per line.

Keep in mind that your message <b>MUST</b> contain some text other than just a button!
""".format(
    dispatcher.bot.first_name
)


@typing_action
def markdown_help(update, context):
    update.effective_message.reply_text(MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "Try forwarding the following message to me, and you'll see!"
    )
    update.effective_message.reply_text(
        "/save test This is a markdown test. _italics_, --underline--, *bold*, `code`, ~strike~ "
        "[URL](example.com) [button](buttonurl:github.com) "
        "[button2](buttonurl://google.com:same)"
    )


@typing_action
def ud(update, context):
    msg = update.effective_message
    args = context.args
    text = " ".join(args).lower()
    if not text:
        msg.reply_text("Please enter keywords to search!")
        return
    try:
        results = get(f"http://api.urbandictionary.com/v0/define?term={text}").json()
        reply_text = (
            f"Word: {text}\n\n"
            f'Definition:\n{results["list"][0]["definition"]}\n\n'
            f'Example:\n{results["list"][0]["example"]}\n\n'
        )
    except IndexError:
        reply_text = (
            f"Word: {text}\nResults: Sorry could not find any matching results!"
        )
    ignore_chars = "[]"
    reply = reply_text
    for chars in ignore_chars:
        reply = reply.replace(chars, "")
    if len(reply) >= 4096:
        reply = reply[:4096]  # max msg lenth of tg.
    try:
        msg.reply_text(reply)
    except BadRequest as err:
        msg.reply_text(f"Error! {err.message}")


@typing_action
def src(update, context):
    update.effective_message.reply_text(
        "Hey there! You can find what makes me click [here](https://github.com/nitanmarcel/tgbot).",
        parse_mode=ParseMode.MARKDOWN,
    )


def staff_ids(update, context):
    sfile = "List of SUDO & SUPPORT users:\n"
    sfile += f"× SUDO USER IDs; {SUDO_USERS}\n"
    sfile += f"× SUPPORT USER IDs; {SUPPORT_USERS}"
    with BytesIO(str.encode(sfile)) as output:
        output.name = "staff-ids.txt"
        update.effective_message.reply_document(
            document=output,
            filename="staff-ids.txt",
            caption="Here is the list of SUDO & SUPPORTS users.",
        )


@typing_action
def nekobin(update, context):
    message = update.effective_message
    args = message.text.split(None, 2)[1:]

    if len(args) == 1:
        extension = "txt"
        text = args[0]
        message.reply_text(
            "You have not specified a file extension. Default: <b>.txt</b>",
            parse_mode=ParseMode.HTML,
        )
    else:
        extension, text = args

    if len(text) >= 1:
        key = (
            r.post(
                "https://nekobin.com/api/documents",
                json={"content": f"{text}\n"},
            )
            .json()
            .get("result")
            .get("key")
        )

        dispatcher.bot.send_message(
            message.chat.id,
            text=f"<b>Message nekofied!</b>\n File extension: .{extension}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="View on nekobin",
                            url=f"https://nekobin.com/{key}.{extension}",
                        ),
                    ]
                ]
            ),
        )
    else:
        message.reply_text(
            "You have two options: \n1. Reply to a file or text to nekofy it!\n 2. Send command with text and specify file extension."
        )


@typing_action
def runs(update, context):
    update.effective_message.reply_text(random.choice(fun.RUN_STRINGS))


@typing_action
def slap(update, context):
    args = context.args
    msg = update.effective_message

    # reply to correct message
    reply_text = (
        msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text
    )

    # get user who sent message
    if msg.from_user.username:
        curr_user = "@" + escape_markdown(msg.from_user.username)
    else:
        curr_user = "[{}](tg://user?id={})".format(
            msg.from_user.first_name, msg.from_user.id
        )

    user_id = extract_user(update.effective_message, args)
    if user_id:
        slapped_user = context.bot.get_chat(user_id)
        user1 = curr_user
        if slapped_user.username:
            user2 = "@" + escape_markdown(slapped_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(
                slapped_user.first_name, slapped_user.id
            )

    # if no target found, bot targets the sender
    else:
        user1 = "[{}](tg://user?id={})".format(context.bot.first_name, context.bot.id)
        user2 = curr_user

    temp = random.choice(fun.SLAP_TEMPLATES)
    item = random.choice(fun.ITEMS)
    hit = random.choice(fun.HIT)
    throw = random.choice(fun.THROW)

    repl = temp.format(user1=user1, user2=user2, item=item, hits=hit, throws=throw)

    reply_text(repl, parse_mode=ParseMode.MARKDOWN)


@typing_action
def dice(update, context):
    context.bot.sendDice(update.effective_chat.id)


def decide(update, context):
    args = update.effective_message.text.split(None, 1)
    if len(args) >= 2:  # Don't reply if no args
        reply_text = (
            update.effective_message.reply_to_message.reply_text
            if update.effective_message.reply_to_message
            else update.effective_message.reply_text
        )
        reply_text(random.choice(fun.DECIDE))


def yesnowtf(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    res = r.get("https://yesno.wtf/api")
    if res.status_code != 200:
        return msg.reply_text(random.choice(fun.DECIDE))
    else:
        res = res.json()
    try:
        context.bot.send_animation(
            chat.id, animation=res["image"], caption=str(res["answer"]).upper()
        )
    except BadRequest:
        return


def me_too(update, context):
    message = update.effective_message
    reply = random.choice(["Me too thanks", "Haha yes, me too", "Same lol", "Me irl"])
    message.reply_text(reply)


def goodnight(update, context):
    message = update.effective_message
    reply = random.choice(fun.GDNIGHT)
    message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


def goodmorning(update, context):
    message = update.effective_message
    reply = random.choice(fun.GDMORNING)
    message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


__help__ = """
An "odds and ends" module for small, simple commands which don't really fit anywhere

 - /id: Get the current group id. If used by replying to a message, gets that user's id.
 - /info: Get information about a user.
 - /source: Get the bot's source link.
 - /nekofy <py/c/java/txt...> <code>: Uploads input code to neko.bin (max. 4096 chars). Reply to file to upload. 
 - /wiki <query>: Search wikipedia articles.
 - /dict <query>: Search for words you are unsure about with a dictionary. Supported languages are: en, de, fr, ru.
 - /ud <query> : Search stuffs in urban dictionary.
 - /reverse: Reverse searches image or stickers on google.
 - /gdpr: Deletes your information from the bot's database. Private group chats only.
 - /markdownhelp: Short summary of how markdown works in Telegram (can only be called in private group chats/Bot pm).

 And some other fun commands:

 - /decide: Randomly answer yes no etc.
 - /runs: Reply a random string from an array of replies.
 - /slap: Slap a user, or get slapped if not a reply.
 - /roll: Rolls a dice.
*Regex based memes:*

`/decide` can be also used with regex like: `Khaleesi? <question>: randomly answer "Yes, No" etc.`

Some other regex filters are:
`me too` | `goodmorning` | `goodnight`.

The bot will reply random strings accordingly when these words are used!
All regex filters can be disabled as well: `/disable metoo`.

"""

__mod_name__ = "Miscs"

ID_HANDLER = DisableAbleCommandHandler("id", get_id, pass_args=True)
INFO_HANDLER = DisableAbleCommandHandler("info", info, pass_args=True)
ECHO_HANDLER = CommandHandler("echo", echo, filters=CustomFilters.sudo_filter)
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help, filters=Filters.private)
GDPR_HANDLER = CommandHandler("gdpr", gdpr, filters=Filters.private)
UD_HANDLER = DisableAbleCommandHandler("ud", ud)
STAFFLIST_HANDLER = CommandHandler(
    "staffids", staff_ids, filters=Filters.user(OWNER_ID)
)
SRC_HANDLER = CommandHandler("source", src)
NEKOFY_HANDLER = CommandHandler("nekofy", nekobin, pass_args=True, run_async=True)

## Fun stuff
DECIDE_HANDLER = DisableAbleMessageHandler(
    Filters.regex(r"(?i)^Khaleesi\?"), decide, friendly="decide"
)
GDMORNING_HANDLER = DisableAbleMessageHandler(
    Filters.regex(r"(?i)(goodmorning|morning)"), goodmorning, friendly="goodmorning"
)
GDNIGHT_HANDLER = DisableAbleMessageHandler(
    Filters.regex(r"(?i)(goodnight|night)"), goodnight, friendly="goodnight"
)
DICE_HANDLER = DisableAbleCommandHandler("roll", dice)
YESNOWTF_HANDLER = DisableAbleCommandHandler("decide", yesnowtf)
RUNS_HANDLER = DisableAbleCommandHandler("runs", runs)
SLAP_HANDLER = DisableAbleCommandHandler("slap", slap, pass_args=True)

dispatcher.add_handler(UD_HANDLER)
dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(GDPR_HANDLER)
dispatcher.add_handler(STAFFLIST_HANDLER)
dispatcher.add_handler(SRC_HANDLER)
dispatcher.add_handler(NEKOFY_HANDLER)

## Fun stuff
dispatcher.add_handler(DECIDE_HANDLER)
dispatcher.add_handler(GDMORNING_HANDLER)
dispatcher.add_handler(GDNIGHT_HANDLER)
dispatcher.add_handler(DICE_HANDLER)
dispatcher.add_handler(YESNOWTF_HANDLER)
dispatcher.add_handler(RUNS_HANDLER)
dispatcher.add_handler(SLAP_HANDLER)
