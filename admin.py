from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
)
from config import ADMIN_ID
import database as db

# States
SELECT_METHOD, SELECT_LINK, BLOCK_USER, UNBLOCK_USER, BROADCAST = range(5)

def method_name_admin(i):
    names = {
        1: "🔴 Ban Method",
        2: "🟢 Unban Method",
        3: "❄️ Unfreeze Method",
        4: "♾️ Permanent Limit Remove",
        5: "⚠️ Limit Remove",
        6: "🚨 Scam Report",
    }
    return names.get(i, f"Method {i}")

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👥 Users", callback_data="admin_users")],
        [InlineKeyboardButton("📩 Account Requests", callback_data="admin_requests")],
        [InlineKeyboardButton("📚 Manage Methods", callback_data="admin_methods")],
        [InlineKeyboardButton("🔗 Manage Required Links", callback_data="admin_links")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("🚫 Block User", callback_data="admin_block")],
        [InlineKeyboardButton("✅ Unblock User", callback_data="admin_unblock")],
        [InlineKeyboardButton("⬅️ Close", callback_data="main_menu")],
    ]
    await update.callback_query.edit_message_text(
        "⚙️ **Admin Panel**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

async def admin_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.answer("Access denied.", show_alert=True)
        return ConversationHandler.END

    data = query.data

    if data == "admin_users":
        users = await db.get_all_users()
        text = "👥 **Users:**\n"
        for u in users[:20]:
            text += f"`{u['user_id']}` - {u['first_name']} (@{u['username']}) | refs: {u['referral_count']}\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]]), parse_mode="Markdown")
        return ConversationHandler.END

    elif data == "admin_requests":
        requests = await db.get_pending_requests()
        if not requests:
            await query.edit_message_text("No pending requests.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]]))
            return ConversationHandler.END
        text = "📩 **Pending Requests:**\n"
        for r in requests:
            text += f"ID {r['id']}: {r['first_name']} (@{r['username']}) refs: {r['referral_count']}\n"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]]), parse_mode="Markdown")
        return ConversationHandler.END

    elif data == "admin_methods":
        keyboard = []
        for i in range(1, 7):
            keyboard.append([InlineKeyboardButton(method_name_admin(i), callback_data=f"edit_method_{i}")])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")])
        await query.edit_message_text("📚 Select method to edit:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

    elif data == "admin_links":
        keyboard = [
            [InlineKeyboardButton("Channel 1", callback_data="edit_link_channel_1")],
            [InlineKeyboardButton("Channel 2", callback_data="edit_link_channel_2")],
            [InlineKeyboardButton("Join Request Channel 3", callback_data="edit_link_join_request_channel")],
            [InlineKeyboardButton("Backup GC", callback_data="edit_link_backup_gc")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")],
        ]
        await query.edit_message_text("🔗 Select link to edit:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

    elif data == "admin_broadcast":
        await query.edit_message_text("Send the message you want to broadcast:")
        return BROADCAST

    elif data == "admin_stats":
        stats = await db.get_statistics()
        msg = (
            f"📊 **Statistics**\n\n"
            f"Users: {stats['total_users']}\n"
            f"Referrals: {stats['total_referrals']}\n"
            f"Account requests: {stats['total_requests']}\n"
            f"Pending: {stats['pending_requests']}"
        )
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]]), parse_mode="Markdown")
        return ConversationHandler.END

    elif data == "admin_block":
        await query.edit_message_text("Send the user ID to block:")
        return BLOCK_USER

    elif data == "admin_unblock":
        await query.edit_message_text("Send the user ID to unblock:")
        return UNBLOCK_USER

    elif data == "admin_panel":
        await show_admin_panel(update, context)
        return ConversationHandler.END

    # Edit method / link triggers
    if data.startswith("edit_method_"):
        method_id = int(data.split("_")[2])
        context.user_data["edit_method_id"] = method_id
        await query.edit_message_text(f"Send new text for {method_name_admin(method_id)}:")
        return SELECT_METHOD

    if data.startswith("edit_link_"):
        link_type = data[10:]  # e.g., channel_1, backup_gc, join_request_channel
        context.user_data["edit_link_type"] = link_type
        await query.edit_message_text("Send new values in format:\n`ChatID|Link`\nExample: `-100xxx|https://t.me/...`")
        return SELECT_LINK

    # Approve / Reject handling (from admin DM)
    if data.startswith("approve_") or data.startswith("reject_"):
        await handle_approve_reject(update, context)
        return ConversationHandler.END

    return ConversationHandler.END

async def handle_approve_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    action, req_id = data.split("_")
    req_id = int(req_id)
    req = await db.get_request_by_id(req_id)
    if not req:
        await query.edit_message_text("Request not found.")
        return
    if action == "approve":
        await db.update_request_status(req_id, "approved")
        try:
            await context.bot.send_message(req["user_id"], "✅ Your account request has been approved! Admin will contact you.")
        except:
            pass
        await query.edit_message_text(query.message.text + "\n\n✅ Approved")
    else:
        await db.update_request_status(req_id, "rejected")
        try:
            await context.bot.send_message(req["user_id"], "❌ Your request was rejected.")
        except:
            pass
        await query.edit_message_text(query.message.text + "\n\n❌ Rejected")

# State handlers
async def receive_method_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    method_id = context.user_data.get("edit_method_id")
    new_text = update.message.text
    await db.set_method_text(method_id, new_text)
    await update.message.reply_text("✅ Method text updated.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")]]))
    return ConversationHandler.END

async def receive_link_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link_type = context.user_data.get("edit_link_type")
    parts = update.message.text.split("|")
    if len(parts) != 2:
        await update.message.reply_text("Invalid format. Use `ChatID|Link`")
        return SELECT_LINK
    chat_id, link = parts[0].strip(), parts[1].strip()
    id_key = f"{link_type}_id"
    link_key = f"{link_type}_link"
    await db.set_setting(id_key, chat_id)
    await db.set_setting(link_key, link)
    await update.message.reply_text("✅ Link updated.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")]]))
    return ConversationHandler.END

async def block_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = int(update.message.text)
        await db.block_user(uid)
        await update.message.reply_text(f"🚫 User {uid} blocked.")
    except:
        await update.message.reply_text("Invalid ID.")
    return ConversationHandler.END

async def unblock_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = int(update.message.text)
        await db.unblock_user(uid)
        await update.message.reply_text(f"✅ User {uid} unblocked.")
    except:
        await update.message.reply_text("Invalid ID.")
    return ConversationHandler.END

async def broadcast_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = await db.get_all_users()
    sent = 0
    for u in users:
        try:
            await context.bot.send_message(u["user_id"], update.message.text)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"📢 Sent to {sent}/{len(users)} users.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

admin_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(admin_entry, pattern="^(admin_|approve_|reject_|edit_method_|edit_link_)"),
    ],
    states={
        SELECT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_method_text)],
        SELECT_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link_value)],
        BLOCK_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, block_user_id)],
        UNBLOCK_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, unblock_user_id)],
        BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_msg)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)