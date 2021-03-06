# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import traceback
import os
from datetime import datetime
from uniborg import util
from sql_helpers.global_variables_sql import SYNTAX, MODULE_LIST

thumb_image_path = Config.TMP_DOWNLOAD_DIRECTORY + "/thumb_image.jpg"
MODULE_LIST.append("core")
DELETE_TIMEOUT = 5


@borg.on(util.admin_cmd(pattern="reload (?P<shortname>\w+)$"))  # pylint:disable=E0602
async def load_reload(event):
    await event.delete()
    shortname = event.pattern_match["shortname"]
    try:
        if shortname in borg._plugins:  # pylint:disable=E0602
            borg.remove_plugin(shortname)  # pylint:disable=E0602
        borg.load_plugin(shortname)  # pylint:disable=E0602
        msg = await event.respond(f"Successfully reloaded {shortname}")
        await asyncio.sleep(DELETE_TIMEOUT)
        await msg.delete()
    except Exception as e:  # pylint:disable=C0103,W0703
        trace_back = traceback.format_exc()
        # pylint:disable=E0602
        logger.warn(f"Failed to (re)load {shortname}: {trace_back}")
        await event.respond(f"Failed to (re)load {shortname}: {e}")


@borg.on(util.admin_cmd(pattern="(?:unload) (?P<shortname>\w+)$"))  # pylint:disable=E0602
async def remove(event):
    await event.delete()
    shortname = event.pattern_match["shortname"]
    if shortname == "_core":
        msg = await event.respond(f"{shortname} can not be removed!")
    elif shortname in borg._plugins:  # pylint:disable=E0602
        borg.remove_plugin(shortname)  # pylint:disable=E0602
        msg = await event.respond(f"Unloaded {shortname}")
    else:
        msg = await event.respond(f"{shortname} is not loaded!")
    await asyncio.sleep(DELETE_TIMEOUT)
    await msg.delete()

@borg.on(util.admin_cmd(pattern="load"))  # pylint:disable=E0602
async def install_plug_in(event):
    if event.fwd_from:
        return
    if event.reply_to_msg_id:
        try:
            downloaded_file_name = await borg.download_media(  # pylint:disable=E0602
                await event.get_reply_message(),
                borg._plugin_path  # pylint:disable=E0602
            )
            if "(" not in downloaded_file_name:
                borg.load_plugin_from_file(downloaded_file_name)  # pylint:disable=E0602
                await event.edit("Loaded `{}`".format(os.path.basename(downloaded_file_name)))
            else:
                os.remove(downloaded_file_name)
                await event.edit("Module already exists!")
        except Exception as e:  # pylint:disable=C0103,W0703
            await event.edit(str(e))
            os.remove(downloaded_file_name)
    await asyncio.sleep(DELETE_TIMEOUT)
    await event.delete()

@borg.on(util.admin_cmd(pattern="share (.*)"))
async def share_plug_in(event):
    if event.fwd_from:
        return
    mone = await event.edit("Searching for required file..")
    input_str = event.pattern_match.group(1)
    plugin = f"stdplugins/{input_str}.py"
    thumb = None
    if os.path.exists(thumb_image_path):
        thumb = thumb_image_path
    if os.path.exists(plugin):
        start = datetime.now()
        c_time = time.time()
        await borg.send_file(
            event.chat_id,
            plugin,
            force_document=True,
            supports_streaming=False,
            allow_cache=False,
            reply_to=event.message.id,
            thumb=thumb,
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(d, t, mone, c_time, "")
            )
        )
        end = datetime.now()
        # os.remove(input_str)
        ms = (end - start).seconds
        await mone.edit(f"Uploaded {input_str} in {ms} seconds.")
    else:
        await mone.edit("404: Module not found")
        
@borg.on(util.admin_cmd(pattern="nuke (.*)"))
async def nuke_plug_in(event):
    if event.fwd_from:
        return
    mone = await event.edit("Searching for required file..")
    input_str = event.pattern_match.group(1)
    plugin = f"stdplugins/{input_str}.py"
    if os.path.exists(plugin):
        try:
            os.remove(plugin)
            await mone.edit(f"{input_str} has been nuked!")
        except Exception as e:
            await mone.edit(f"Unexpected error occured: {e}")
    else:
        await mone.edit("404: Module not found")

SYNTAX.update({
    "core": "\
**Requested Module --> core**\
\n\n**Detailed usage of fuction(s):**\
\n\n```.load <as_a_reply_to_a_module_file>```\
\nUsage: Load a specified module.\
\n\n```.reload <module_name>```\
\nUsage: Reload any module that was unloaded.\
\n\n```.unload <module_name>```\
\nUsage: Unload any loaded module.\
\n\n```.share <module_name>```\
\nUsage: Share any loaded module.\
\n\n```.nuke <module_name>```\
\nUsage: Nuke any module, loaded or unloaded.\
"
})
