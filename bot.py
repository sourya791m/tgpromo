import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, ContextTypes
)
from config import BOT_TOKEN, ADMIN_ID
import database as db
from admin import admin_conv_handler

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

def method_name(index: int) -> str:
    names = {
        1: "🔴 Ban Method",
        2: "🟢 Unban Method",
        3: "❄️ Unfreeze Method",
        4: "♾️ Permanent Limit Remove",
        5: "⚠️ Limit Remove",
        6: "🚨 Scam Report",
    }
    return names.get(index, f"Method {index}")

async def get_effective_settings():
    settings = {
        "channel_1_id": await db.get_setting("channel_1_id") or "-1003260353876",
        "channel_2_id": await db.get_setting("channel_2_id") or "-1003971062167",
        "join_request_channel_id": await db.get_setting("join_request_channel_id") or "-1004360222856",
        "backup_gc_id": await db.get_setting("backup_gc_id") or "-1004331557651",
        "channel_1_link": await db.get_setting("channel_1_link") or "https://t.me/TheNextLevelOfficial",
        "channel_2_link": await db.get_setting("channel_2_link") or "https://t.me/+hYM-A7mpsV4xOTll",
        "join_request_channel_link": await db.get_setting("join_request_channel_link") or "https://t.me/+QucLSiC1M8ZmODc1",
        "backup_gc_link": await db.get_setting("backup_gc_link") or "https://t.me/+pPvJbytZmX80NGFl",
        "required_refs_method_1": int(await db.get_setting("required_refs_method_1") or 5),
        "required_refs_method_2": int(await db.get_setting("required_refs_method_2") or 10),
        "required_refs_all": int(await db.get_setting("required_refs_all") or 15),
        "support_link": await db.get_setting("support_link") or "https://t.me/your_support",
    }
    return settings

async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> tuple:
    settings = await get_effective_settings()
    checks = {
        "Channel 1": settings["channel_1_id"],
        "Channel 2": settings["channel_2_id"],
        "Channel 3 (Join Request)": settings["join_request_channel_id"],
        "Backup GC (Join Request)": settings["backup_gc_id"],
    }
    status = {}
    all_ok = True
    for name, chat_id in checks.items():
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            if member.status in ["member", "administrator", "creator"]:
                status[name] = "✅"
            else:
                status[name] = "❌"
                all_ok = False
        except Exception:
            status[name] = "⚠️ Error"
            all_ok = False
    return all_ok, status

async def show_requirements(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    settings = await get_effective_settings()
    keyboard = [
        [InlineKeyboardButton("📢 Channel 1", url=settings["channel_1_link"])],
        [InlineKeyboardButton("📢 Channel 2", url=settings["channel_2_link"])],
        [InlineKeyboardButton("🔔 Join Request Channel 3", url=settings["join_request_channel_link"])],
        [InlineKeyboardButton("💬 Backup GC Join Request", url=settings["backup_gc_link"])],
        [InlineKeyboardButton("✅ Check Membership", callback_data="check_membership")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "🔐 **Membership Required**\n\n"
        "Complete these 4 steps:\n"
        "1️⃣ Join Channel 1\n"
        "2️⃣ Join Channel 2\n"
        "3️⃣ Send join request to Channel 3\n"
        "4️⃣ Send join request to Backup GC\n\n"
        "Then press **Check Membership**."
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    user = await db.get_user(user_id)
    ref_count = user["referral_count"]
    settings = await get_effective_settings()
    all_unlocked = ref_count >= settings["required_refs_all"]

    if all_unlocked:
        req_btn = InlineKeyboardButton("👤 Request Telegram Account", callback_data="request_account")
    else:
        req_btn = InlineKeyboardButton(f"🔒 Request Account ({settings['required_refs_all']} refs)", callback_data="noop")

    keyboard = [
        [InlineKeyboardButton("📚 Telegram Methods", callback_data="methods_menu")],
        [InlineKeyboardButton("🎁 My Referrals", callback_data="my_referrals")],
        [req_btn],
        [InlineKeyboardButton("📞 Support", callback_data="support")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🏠 **Main Menu**\nChoose an option:"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    if await db.is_blocked(user_id):
        await update.message.reply_text("⛔ You are blocked.")
        return

    await db.set_username_first_name(user_id, user.username, user.first_name)

    # Referral handling
    if context.args and context.args[0].startswith("ref_"):
        try:
            referrer_id = int(context.args[0][4:])
            success = await db.set_referrer(user_id, referrer_id)
            if success:
                try:
                    await context.bot.send_message(referrer_id, f"🎉 New referral! {user.first_name} joined using your link.")
                except:
                    pass
        except ValueError:
            pass

    all_ok, _ = await check_membership(user_id, context)
    if all_ok:
        await main_menu(update, context, user_id)
    else:
        await show_requirements(update, context, user_id)

# Callback button handler (main user flow)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if await db.is_blocked(user_id):
        await query.edit_message_text("⛔ You are blocked.")
        return

    data = query.data

    if data == "check_membership":
        all_ok, status = await check_membership(user_id, context)
        if all_ok:
            await main_menu(update, context, user_id)
        else:
            msg = "🔍 **Membership Status:**\n"
            for req, st in status.items():
                msg += f"{st} {req}\n"
            msg += "\n❌ Complete all steps and press again."
            keyboard = [[InlineKeyboardButton("🔄 Check Again", callback_data="check_membership")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "methods_menu":
        user = await db.get_user(user_id)
        ref_count = user["referral_count"]
        keyboard = []
        for i in range(1, 7):
            unlocked = await db.is_method_unlocked(user_id, i)
            # also auto-unlock based on current ref count
            if not unlocked:
                settings = await get_effective_settings()
                if (i == 1 and ref_count >= settings["required_refs_method_1"]) or \
                   (i == 2 and ref_count >= settings["required_refs_method_2"]) or \
                   (ref_count >= settings["required_refs_all"]):
                    await db.unlock_method(user_id, i)
                    unlocked = True
            if unlocked:
                btn_text = f"✅ {method_name(i)}"
            else:
                btn_text = f"🔒 {method_name(i)}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"method_{i}")])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="main_menu")])
        await query.edit_message_text("📚 **Telegram Methods**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("method_"):
        method_index = int(data.split("_")[1])
        user = await db.get_user(user_id)
        ref_count = user["referral_count"]
        unlocked = await db.is_method_unlocked(user_id, method_index)
        if not unlocked:
            settings = await get_effective_settings()
            if method_index == 1 and ref_count >= settings["required_refs_method_1"]:
                await db.unlock_method(user_id, method_index)
                unlocked = True
            elif method_index == 2 and ref_count >= settings["required_refs_method_2"]:
                await db.unlock_method(user_id, method_index)
                unlocked = True
            elif ref_count >= settings["required_refs_all"]:
                await db.unlock_method(user_id, method_index)
                unlocked = True
        if unlocked:
            text = await db.get_method_text(method_index)
            keyboard = [[InlineKeyboardButton("⬅️ Back to Methods", callback_data="methods_menu")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            settings = await get_effective_settings()
            if method_index == 1:
                required = settings["required_refs_method_1"]
            elif method_index == 2:
                required = settings["required_refs_method_2"]
            else:
                required = settings["required_refs_all"]
            remaining = required - ref_count
            msg = (
                f"🔒 **{method_name(method_index)}**\n\n"
                f"Your referrals: {ref_count}\n"
                f"Required: {required}\n"
                f"You need **{remaining}** more successful referrals."
            )
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="methods_menu")]]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "my_referrals":
        user = await db.get_user(user_id)
        ref_count = user["referral_count"]
        settings = await get_effective_settings()
        bot_username = (await context.bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

        if ref_count < settings["required_refs_method_1"]:
            next_unlock = settings["required_refs_method_1"]
            desc = "Unlock Method 1"
        elif ref_count < settings["required_refs_method_2"]:
            next_unlock = settings["required_refs_method_2"]
            desc = "Unlock Method 2"
        elif ref_count < settings["required_refs_all"]:
            next_unlock = settings["required_refs_all"]
            desc = "Unlock ALL Methods"
        else:
            next_unlock = "All methods unlocked"
            desc = "🎉"

        msg = (
            f"🎁 **Referral System**\n\n"
            f"Your referrals: {ref_count}\n"
            f"Next unlock: {next_unlock} ({desc})\n"
            f"Referral link:\n`{ref_link}`"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "request_account":
        user = await db.get_user(user_id)
        ref_count = user["referral_count"]
        settings = await get_effective_settings()
        if ref_count < settings["required_refs_all"]:
            await query.answer("You need 15 referrals to request an account.", show_alert=True)
            return
        keyboard = [
            [InlineKeyboardButton("✅ Yes, request account", callback_data="confirm_request")],
            [InlineKeyboardButton("❌ Cancel", callback_data="main_menu")],
        ]
        await query.edit_message_text("Submit account request? Admin will be notified.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "confirm_request":
        user = await db.get_user(user_id)
        request_id = await db.add_account_request(user_id, user["username"], user["first_name"], user["referral_count"])
        admin_msg = (
            f"📩 **New Account Request**\n\n"
            f"User: {user['first_name']} (@{user['username']})\n"
            f"ID: `{user_id}`\n"
            f"Referrals: {user['referral_count']}\n"
            f"Date: {user.get('registered_date', 'N/A')}\n\n"
            f"Request ID: {request_id}"
        )
        admin_kb = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{request_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{request_id}"),
            ]
        ]
        try:
            msg = await context.bot.send_message(ADMIN_ID, admin_msg, reply_markup=InlineKeyboardMarkup(admin_kb), parse_mode="Markdown")
            async with db.aiosqlite.connect(db.DB_PATH) as conn:
                await conn.execute("UPDATE account_requests SET admin_message_id = ? WHERE id = ?", (msg.message_id, request_id))
                await conn.commit()
        except Exception as e:
            logging.error(f"Admin notify failed: {e}")
        await query.edit_message_text("✅ Request submitted. You'll be notified when admin responds.")
        await query.message.reply_text("⬅️ Return to main menu:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]))

    elif data == "support":
        settings = await get_effective_settings()
        keyboard = [
            [InlineKeyboardButton("📞 Contact Support", url=settings["support_link"])],
            [InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")],
        ]
        await query.edit_message_text("📞 **Support**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "help":
        settings = await get_effective_settings()
        msg = (
            "ℹ️ **Help**\n\n"
            "1️⃣ Complete the 4 membership requirements:\n"
            "   - Channel 1, Channel 2 (join)\n"
            "   - Channel 3 (join request)\n"
            "   - Backup GC (join request)\n"
            f"2️⃣ Refer friends:\n"
            f"   {settings['required_refs_method_1']} refs → Method 1\n"
            f"   {settings['required_refs_method_2']} refs → Method 2\n"
            f"   {settings['required_refs_all']} refs → ALL methods\n"
            "3️⃣ View method texts (display only).\n"
            "4️⃣ After 15 refs, request a Telegram account.\n\n"
            "⚠️ This bot **only shows** method texts – it does NOT perform any actions."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "main_menu":
        await main_menu(update, context, user_id)

    elif data == "admin_panel":
        if user_id == ADMIN_ID:
            from admin import show_admin_panel
            await show_admin_panel(update, context)
        else:
            await query.answer("Access denied.", show_alert=True)

    elif data == "noop":
        await query.answer("Not enough referrals yet.", show_alert=True)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(msg="Exception:", exc_info=context.error)

def main():
    import asyncio
    asyncio.run(db.init_db())

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    # Main user callback handler (exclude admin approve/reject patterns)
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(?!approve_|reject_|admin_|edit_).*"))
    # Admin conversation & approve/reject callbacks
    application.add_handler(admin_conv_handler)

    application.add_error_handler(error_handler)

    print("Bot started...")
    application.run_polling()

if __name__ == "__main__":
    main()