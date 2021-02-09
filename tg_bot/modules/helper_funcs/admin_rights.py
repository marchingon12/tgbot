from telegram import User, Chat


def user_can_promote(chat: Chat, user: User, bot_id: int) -> bool:
    return chat.get_member(user.id).can_promote_members


def user_can_ban(chat: Chat, user: User, bot_id: int) -> bool:
    return chat.get_member(user.id).can_restrict_members


def user_can_pin(chat: Chat, user: User, bot_id: int) -> bool:
    return chat.get_member(user.id).can_pin_messages


def user_can_changeinfo(chat: Chat, user: User, bot_id: int) -> bool:
    return chat.get_member(user.id).can_change_info


def user_can_deletemsgs(chat: Chat, user: User, bot_id: int) -> bool:
    return chat.get_member(user.id).can_delete_messages


def user_can_voicechat(chat: Chat, user: User, bot_id: int) -> bool:
    return chat.get_member(user.id).user_can_voice_chat


def user_can_beanonymous(chat: Chat, user: User, bot_id: int) -> bool:
    return chat.get_member(user.id).user_can_be_anonymous
