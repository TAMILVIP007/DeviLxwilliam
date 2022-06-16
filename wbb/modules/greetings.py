"""
MIT License

Copyright (c) 2021 TheHamkerCat

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
import os
from datetime import datetime
from random import shuffle

from pyrogram import filters
from pyrogram.errors.exceptions.bad_request_400 import (
    ChatAdminRequired,
    UserNotParticipant,
)
from pyrogram.types import (
    Chat,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    User,
)

from wbb import SUDOERS, WELCOME_DELAY_KICK_SEC, app
from wbb.core.decorators.errors import capture_err
from wbb.core.decorators.permissions import adminsOnly
from wbb.core.keyboard import ikb
from wbb.utils.dbfunctions import (
    captcha_off,
    captcha_on,
    del_welcome,
    get_captcha_cache,
    get_welcome,
    has_solved_captcha_once,
    is_captcha_on,
    is_gbanned_user,
    save_captcha_solved,
    set_welcome,
    update_captcha_cache,
)
from wbb.utils.filter_groups import welcome_captcha_group
from wbb.utils.functions import extract_text_and_keyb, generate_captcha

__MODULE__ = "Greetings"
__HELP__ = """
/set_welcome - Reply this to a message containing correct
format for a welcome message, check end of this message.

/del_welcome - Delete the welcome message.
/get_welcome - Get the welcome message.

**SET_WELCOME ->**

The format should be something like below.

```
**Hi** {name} Welcome to {chat}

~ #This separater (~) should be there between text and buttons, remove this comment also

button=[Duck, https://duckduckgo.com]
button2=[Github, https://github.com]
```

**NOTES ->**

for /rules, you can do /filter rules to a message
containing rules of your groups whenever a user
sends /rules, he'll get the message

Checkout /markdownhelp to know more about formattings and other syntax.
"""

answers_dicc = []
loop = asyncio.get_running_loop()


async def send_welcome_message(chat: Chat, user_id: int, delete: bool = False):
    raw_text = await get_welcome(chat.id)

    if not raw_text:
        return

    text, keyb = extract_text_and_keyb(ikb, raw_text)

    if "{chat}" in text:
        text = text.replace("{chat}", chat.title)
    if "{name}" in text:
        text = text.replace("{name}", (await app.get_users(user_id)).mention)

    async def _send_wait_delete():
        m = await app.send_message(
            chat.id,
            text=text,
            reply_markup=keyb,
            disable_web_page_preview=True,
        )
        await asyncio.sleep(300)
        await m.delete()

    asyncio.create_task(_send_wait_delete())

# WELCOME MESSAGE


@app.on_message(
    filters.command("set_welcome") & ~filters.private & ~filters.edited)
@adminsOnly("can_change_info")
async def set_welcome_func(_, message):
    usage = "You need to reply to a text, check the Greetings module in /help"
    if not message.reply_to_message:
        await message.reply_text(usage)
        return
    if not message.reply_to_message.text:
        await message.reply_text(usage)
        return
    chat_id = message.chat.id
    raw_text = message.reply_to_message.text.markdown
    if not (extract_text_and_keyb(ikb, raw_text)):
        return await message.reply_text("Wrong formating, check help section.")
    await set_welcome(chat_id, raw_text)
    await message.reply_text("Welcome message has been successfully set.")


@app.on_message(
    filters.command("del_welcome") & ~filters.private & ~filters.edited)
@adminsOnly("can_change_info")
async def del_welcome_func(_, message):
    chat_id = message.chat.id
    await del_welcome(chat_id)
    await message.reply_text("Welcome message has been deleted.")


@app.on_message(
    filters.command("get_welcome") & ~filters.private & ~filters.edited)
@adminsOnly("can_change_info")
async def get_welcome_func(_, message):
    chat = message.chat
    welcome = await get_welcome(chat.id)
    if not welcome:
        return await message.reply_text("No welcome message set.")
    if not message.from_user:
        return await message.reply_text(
            "You're anon, can't send welcome message."
        )

    await send_welcome_message(chat, message.from_user.id)

    await message.reply_text(f'`{welcome.replace("`", "")}`')
