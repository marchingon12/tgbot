import time
from bs4 import BeautifulSoup
from requests import get
from telegram import ParseMode
from telegram.error import BadRequest

from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.alternate import typing_action

GITHUB = "https://github.com"
DEVICES_DATA = "https://raw.githubusercontent.com/androidtrackers/certified-android-devices/master/by_device.json"


@typing_action
def magisk(update, context):
    url = "https://raw.githubusercontent.com/topjohnwu/magisk_files/"
    releases = ""
    for type, branch in {
        "Stable": ["master/stable", "master"],
        "Beta": ["master/beta", "master"],
        "Canary": ["canary/canary", "canary"],
    }.items():
        data = get(url + branch[0] + ".json").json()
        if type != "Canary":
            releases += (
                f"*{type}*: \n"
                f'• Zip - [{data["magisk"]["version"]}-{data["magisk"]["versionCode"]}]({data["magisk"]["link"]}) - [Changelog]({data["magisk"]["note"]})\n'
                f'• App - [{data["app"]["version"]}-{data["app"]["versionCode"]}]({data["app"]["link"]}) - [Changelog]({data["app"]["note"]})\n'
                f'• Uninstaller - [{data["magisk"]["version"]}-{data["magisk"]["versionCode"]}]({data["uninstaller"]["link"]})\n\n'
            )
        else:
            releases += (
                f"*{type}*: \n"
                f'• Zip - [{data["magisk"]["version"]}-{data["magisk"]["versionCode"]}]({url}{branch[1]}/{data["magisk"]["link"]}) - [Changelog]({url}{branch[1]}/{data["magisk"]["note"]})\n'
                f'• App - [{data["app"]["version"]}-{data["app"]["versionCode"]}]({url}{branch[1]}/{data["app"]["link"]}) - [Changelog]({url}{branch[1]}/{data["app"]["note"]})\n'
                f'• Uninstaller - [{data["magisk"]["version"]}-{data["magisk"]["versionCode"]}]({url}{branch[1]}/{data["uninstaller"]["link"]})\n\n'
            )

    update.message.reply_text(
        "*Latest Magisk Releases:*\n\n{}".format(releases),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


@typing_action
def twrp(update, context):
    args = context.args
    if len(args) == 0:
        reply = "No codename provided, write a codename for fetching informations."
        del_msg = update.effective_message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
        )
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found") or (
                err.message == "Message can't be deleted"
            ):
                return

    _device = " ".join(args)
    url = get(f"https://eu.dl.twrp.me/{_device}/")
    if url.status_code == 404:
        reply = f"Couldn't find twrp downloads for {_device}!\n"
        del_msg = update.effective_message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found") or (
                err.message == "Message can't be deleted"
            ):
                return
    else:
        reply = f"*Latest Official TWRP for {_device}*\n"
        db = get(DEVICES_DATA).json()
        newdevice = _device.strip("lte") if _device.startswith("beyond") else _device
        try:
            brand = db[newdevice][0]["brand"]
            name = db[newdevice][0]["name"]
            reply += f"*{brand} - {name}*\n"
        except KeyError as err:
            pass
        page = BeautifulSoup(url.content, "lxml")
        date = page.find("em").text.strip()
        reply += f"*Updated:* {date}\n"
        trs = page.find("table").find_all("tr")
        row = 2 if trs[0].find("a").text.endswith("tar") else 1
        for i in range(row):
            download = trs[i].find("a")
            dl_link = f"https://eu.dl.twrp.me{download['href']}"
            dl_file = download.text
            size = trs[i].find("span", {"class": "filesize"}).text
            reply += f"[{dl_file}]({dl_link}) - {size}\n"

        update.message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )


__help__ = """
Get the latest Magsik releases or TWRP for your device!

*Android related commands:*

 × /magisk - Gets the latest magisk release for Stable/Beta/Canary.
 × /twrp <codename> -  Gets latest twrp for the android device using the codename.
"""

__mod_name__ = "Android"

MAGISK_HANDLER = DisableAbleCommandHandler("magisk", magisk)
TWRP_HANDLER = DisableAbleCommandHandler("twrp", twrp, pass_args=True)

dispatcher.add_handler(MAGISK_HANDLER)
dispatcher.add_handler(TWRP_HANDLER)
