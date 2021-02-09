from tg_bot import client, SUDO_USERS

import asyncio
from telethon import events
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.errors.rpcerrorlist import MessageDeleteForbiddenError

# Check if user has admin rights


async def is_administrator(user_id: int, message):
    admin = False
    async for user in client.iter_participants(
        message.chat_id, filter=ChannelParticipantsAdmins
    ):
        if user_id == user.id or user_id in SUDO_USERS:
            admin = True
            break
    return admin


@client.on(events.NewMessage(pattern="^/purge"))
async def purge(event):
    chat = event.chat_id
    msgs = []

    if not await is_administrator(user_id=event.from_id, message=event):
        await event.reply("You're not an admin!")
        return

    msg = await event.get_reply_message()
    if not msg:
        await event.reply("Reply to a message to select where to start purging from.")
        return

    try:
        msg_id = msg.id
        count = 0
        to_delete = event.message.id - 1
        await event.client.delete_messages(chat, event.message.id)
        msgs.append(event.reply_to_msg_id)
        for m_id in range(to_delete, msg_id - 1, -1):
            msgs.append(m_id)
            count += 1
            if len(msgs) == 100:
                await event.client.delete_messages(chat, msgs)
                msgs = []

        await event.client.delete_messages(chat, msgs)
        del_res = await event.client.send_message(
            event.chat_id, f"Purged {count} messages."
        )

        await asyncio.sleep(2)
        await del_res.delete()

    except MessageDeleteForbiddenError:
        text = "Failed to delete messages.\n"
        text += "Selected messages may be too old or you haven't given me enough admin rights!"
        del_res = await event.respond(text, parse_mode="md")
        await asyncio.sleep(5)
        await del_res.delete()


@client.on(events.NewMessage(pattern="^/purgeme"))
async def purgeme(event):
    message = event.chat_id
    count = int(message[9:])
    i = 1

    try:
        async for message in event.client.iter_messages(event.chat_id, from_user="me"):
            if i > count + 1:
                break
            i += 1
            await message.delete()

            purged_msgs = await event.client.send_message(
                event.chat_id,
                f"Purged {count} messages.",
            )

            await asyncio.sleep(2)
            i = 1
            await purged_msgs.delete()

    except MessageDeleteForbiddenError:
        text = "Failed to delete messages.\n"
        text += "Selected messages may be too old or you haven't given me enough admin rights!"
        purged_msgs = await event.respond(text, parse_mode="md")
        await asyncio.sleep(5)
        await purged_msgs.delete()


@client.on(events.NewMessage(pattern="^/del$"))
async def delete_msg(event):

    if not await is_administrator(user_id=event.from_id, message=event):
        await event.reply("You're not an admin!")
        return

    chat = event.chat_id
    msg = await event.get_reply_message()
    if not msg:
        await event.reply("Reply to some message to delete it.")
        return
    to_delete = event.message
    chat = await event.get_input_chat()
    rm = [msg, to_delete]
    await event.client.delete_messages(chat, rm)


__mod_name__ = "Deleting"

__help__ = """
Deleting a selected amount of messages are easy with this command. \
Bot purges messages all together or individually.

*Admin only:*
 × /del: Deletes the message you replied to.
 × /purge: Deletes all messages between the message you sent with the command issued and the replied to message.
"""
