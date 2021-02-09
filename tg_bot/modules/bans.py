import html

from telegram import Chat, User, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import (
    bot_admin,
    user_admin,
    is_user_ban_protected,
    can_restrict,
    is_user_admin,
    is_user_in_chat,
)
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.helper_funcs.admin_rights import user_can_ban
from tg_bot.modules.helper_funcs.alternate import typing_action
from tg_bot.modules.log_channel import loggable


@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def ban(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
        message.reply_text("You don't have enough rights to ban users!")
        return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Dude atleast refer some user to ban!")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("I'm not gonna ban an admin, don't make fun of yourself!")
        return ""

    if user_id == context.bot.id:
        message.reply_text("I'm not gonna BAN myself, are you crazy or wot?")
        return ""

    log = (
        "<b>{}:</b>"
        "\n#BANNED"
        "\n<b>Admin:</b> {}"
        "\n<b>User:</b> {} (<code>{}</code>)".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(member.user.id, member.user.first_name),
            member.user.id,
        )
    )
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        # context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        context.bot.sendMessage(
            chat.id,
            BAN_STICKER,
            "Let {} walk the plank.".format(
                mention_html(member.user.id, member.user.first_name)
            ),
            parse_mode=ParseMode.HTML,
        )
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("Banned!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Well damn, I can't ban that user.")

    return ""


@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def temp_ban(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
        message.reply_text("You don't have enough rights to temporarily ban someone!")
        return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Dude! atleast refer some user to ban...")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Wow! let's start banning Admins themselves?...")
        return ""

    if user_id == context.bot.id:
        message.reply_text("I'm not gonna BAN myself, are you crazy or wot?")
        return ""

    if not reason:
        message.reply_text("You haven't specified a time to ban this user for!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = (
        "<b>{}:</b>"
        "\n#TEMP BANNED"
        "\n<b>Admin:</b> {}"
        "\n<b>User:</b> {} (<code>{}</code>)"
        "\n<b>Time:</b> {}".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(member.user.id, member.user.first_name),
            member.user.id,
            time_val,
        )
    )
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        # context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Banned! User will be banned for {}.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(
                "Goodbye.. we'll meet after {}.".format(time_val), quote=False
            )
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Well damn, I can't ban that user.")

    return ""


@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def kick(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
        message.reply_text("You don't have enough rights to kick users!")
        return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Yeahh... let's start kicking admins?")
        return ""

    if user_id == context.bot.id:
        message.reply_text("Yeahhh I'm not gonna do that")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        # context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        context.bot.sendMessage(
            chat.id,
            "Untill we meet again {}.".format(
                mention_html(member.user.id, member.user.first_name)
            ),
            parse_mode=ParseMode.HTML,
        )
        log = (
            "<b>{}:</b>"
            "\n#KICKED"
            "\n<b>Admin:</b> {}"
            "\n<b>User:</b> {} (<code>{}</code>)".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                mention_html(member.user.id, member.user.first_name),
                member.user.id,
            )
        )
        if reason:
            log += "\n<b>Reason:</b> {}".format(reason)

        return log

    else:
        message.reply_text("Get Out!.")

    return ""


@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def unban(update, context):
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
        message.reply_text("You don't have enough rights to unban people here!")
        return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if user_id == context.bot.id:
        message.reply_text("How would I unban myself if I wasn't here...?")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text(
            "Why are you trying to unban someone who's already in this chat?"
        )
        return ""

    chat.unban_member(user_id)
    message.reply_text("Done, they can join again!")

    log = (
        "<b>{}:</b>"
        "\n#UNBANNED"
        "\n<b>Admin:</b> {}"
        "\n<b>User:</b> {} (<code>{}</code>)".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(member.user.id, member.user.first_name),
            member.user.id,
        )
    )
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    return log


__help__ = """

Some people need to be publicly banned; spammers, annoyances, or just trolls.
This module allows you to do that easily, by exposing some common actions, so everyone will see!

*Admin only:*
 - /ban <userhandle>: Bans a user. (via handle, or reply)
 - /tban <userhandle> x(m/h/d): Bans a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
 - /unban <userhandle>: Unbans a user. (via handle, or reply)
 - /kick <userhandle>: Kicks a user, (via handle, or reply)

An example of temporarily banning someone:
`/tban @username 2h`; this bans a user for 2 hours.
"""

__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler(
    "ban", ban, pass_args=True, filters=Filters.chat_type.groups
)
TEMPBAN_HANDLER = CommandHandler(
    ["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.chat_type.groups
)
KICK_HANDLER = CommandHandler(
    "kick", kick, pass_args=True, filters=Filters.chat_type.groups
)
UNBAN_HANDLER = CommandHandler(
    "unban", unban, pass_args=True, filters=Filters.chat_type.groups
)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)