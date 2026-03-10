import asyncio
import importlib
import signal
from pyrogram import idle
from Extractor.modules import ALL_MODULES

loop = asyncio.get_event_loop()

# Graceful shutdown
should_exit = asyncio.Event()

def shutdown():
    print("Shutting down gracefully...")
    should_exit.set()  # triggers exit from idle

signal.signal(signal.SIGTERM, lambda s, f: loop.create_task(should_exit.set()))
signal.signal(signal.SIGINT, lambda s, f: loop.create_task(should_exit.set()))

async def sumit_boot():
    for all_module in ALL_MODULES:
        importlib.import_module("Extractor.modules." + all_module)

    # Mark bot as running for the web dashboard
    try:
        import sys, os
        # Ensure project root is in path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from bot_status import mark_bot_running
        mark_bot_running()
        print("» Dashboard status: Bot marked as ACTIVE ✅")
    except Exception as e:
        print(f"» Dashboard status update failed: {e}")

    print("» ʙᴏᴛ ᴅᴇᴘʟᴏʏ sᴜᴄᴄᴇssғᴜʟʟʏ ✨ 🎉")
    await idle()  # keeps the bot alive

    print("» ɢᴏᴏᴅ ʙʏᴇ ! sᴛᴏᴘᴘɪɴɢ ʙᴏᴛ.")

if __name__ == "__main__":
    try:
        loop.run_until_complete(sumit_boot())
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        # Cancel pending tasks to avoid "destroyed but pending" error
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()
        print("Loop closed.")
