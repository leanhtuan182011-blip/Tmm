import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# Cấu hình Token và Admin ID chính xác của bạn
TOKEN = "8764217727:AAHRRldohQkBBtSVBl6hk3KHIZW3ShTJS8Y"
ADMIN_ID = 8810248698

# Kho dữ liệu và danh mục sản phẩm (Hotmail đã giảm xuống 100đ)
database = {
    "balance": {},  # {user_id: số_dư}
    "inventory": {
        "hotmail": ["acc1|pass1", "acc2|pass2"],
        "igclone": ["ig1|pass1"],
        "clone_1_5": ["clone1|pass1", "clone2|pass2"],
        "telegram": ["acc_tg_1", "acc_tg_2"],
        "youtube": ["yt_acc_1", "yt_acc_2"],
    },
    "prices": {
        "hotmail": 100,  # Giảm xuống 100đ theo yêu cầu
        "igclone": 10000,
        "clone_1_5": 2800,
        "telegram": 15000,
        "youtube": 30000,
    },
    "bank_info": {
        "name": "VietinBank",
        "stk": "999962183939",
        "owner": "LE QUANG TUAN",
        "branch": "CN HAI DUONG - PGD TRAN HUNG DAO",
    },
    "pending_deposits": {},
}


class BuyState(StatesGroup):
    waiting_for_quantity = State()


router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Mua Tài Khoản", callback_data="shop_menu")],
            [InlineKeyboardButton(text="💰 Nạp Tiền", callback_data="deposit_menu")],
            [
                InlineKeyboardButton(
                    text="👤 Tài Khoản Của Tôi", callback_data="profile"
                )
            ],
        ]
    )
    await message.answer(
        "👋 Chào mừng bạn đến với **SHOP ACC MEO**!\n\nVui lòng chọn chức năng bên dưới:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


# Bảng quản trị - Chỉ chuẩn xác ADMIN_ID mới mở được
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Bạn không có quyền truy cập bảng quản trị!")
        return

    inv = database["inventory"]
    p = database["prices"]
    text = (
        f"👑 **BẢNG QUẢN TRỊ ADMIN (ĐẶC QUYỀN)**\n\n"
        f"• Trạng thái Bot: 🟢 Đang hoạt động\n\n"
        f"📦 **Tồn kho hiện tại:**\n"
        f"- Hotmail: {len(inv['hotmail'])} ({p['hotmail']:,}đ)\n"
        f"- IG Clone: {len(inv['igclone'])} ({p['igclone']:,}đ)\n"
        f"- Clone 1-5 Page: {len(inv['clone_1_5'])} ({p['clone_1_5']:,}đ)\n"
        f"- Telegram: {len(inv['telegram'])} ({p['telegram']:,}đ)\n"
        f"- Youtube Premium: {len(inv['youtube'])} ({p['youtube']:,}đ)\n\n"
        f"💰 **Cộng tiền test:** `/cong [user_id] [số_tiền]`"
    )
    await message.answer(text, parse_mode="Markdown")


# Lệnh cộng tiền độc quyền cho Admin
@router.message(Command("cong"))
async def cmd_cong(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Bạn không có quyền dùng lệnh này!")
        return

    args = message.text.split()
    if len(args) < 3:
        await message.answer("⚠️ Sai cú pháp! Dùng: `/cong [user_id] [số_tiền]`")
        return

    try:
        target_id = int(args[1])
        amount = int(args[2])
        current = database["balance"].get(target_id, 0)
        database["balance"][target_id] = current + amount

        await message.answer(
            f"✅ Đã cộng thành công {amount:,} VNĐ cho user `{target_id}`!"
        )
        await message.bot.send_message(
            target_id,
            f"🎉 Tài khoản của bạn đã được cộng thêm **{amount:,} VNĐ** từ Admin!",
            parse_mode="Markdown",
        )
    except ValueError:
        await message.answer(
            "❌ User ID và Số tiền phải là số nguyên (dạng số) hợp lệ!"
        )


# --- MENU MUA HÀNG & CHỌN SỐ LƯỢNG ---
@router.callback_query(F.data == "shop_menu")
async def shop_menu(callback: CallbackQuery):
    inv = database["inventory"]
    p = database["prices"]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📧 Hotmail ({len(inv['hotmail'])} có sẵn - {p['hotmail']:,}đ)",
                    callback_data="buy_hotmail",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"📸 IG Clone ({len(inv['igclone'])} có sẵn - {p['igclone']:,}đ)",
                    callback_data="buy_igclone",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"📘 Clone 1-5 Page ({len(inv['clone_1_5'])} có sẵn - {p['clone_1_5']:,}đ)",
                    callback_data="buy_clone_1_5",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"✈️ Telegram ({len(inv['telegram'])} có sẵn - {p['telegram']:,}đ)",
                    callback_data="buy_telegram",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"▶️ Youtube Premium ({len(inv['youtube'])} có sẵn - {p['youtube']:,}đ)",
                    callback_data="buy_youtube",
                )
            ],
            [InlineKeyboardButton(text="⬅️ Quay lại", callback_data="back_home")],
        ]
    )
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            "🛒 **DANH MỤC SẢN PHẨM**\n\nVui lòng chọn loại tài khoản bạn muốn mua:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
    else:
        await callback.message.edit_text(
            "🛒 **DANH MỤC SẢN PHẨM**\n\nVui lòng chọn loại tài khoản bạn muốn mua:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )


@router.callback_query(F.data.startswith("buy_"))
async def select_product_to_buy(callback: CallbackQuery, state: FSMContext):
    prod_type = callback.data.replace("buy_", "")
    stock_count = len(database["inventory"][prod_type])
    price = database["prices"].get(prod_type, 10000)

    if stock_count == 0:
        await callback.answer(
            "❌ Sản phẩm này đang tạm hết hàng!", show_alert=True
        )
        return

    await state.update_data(prod_type=prod_type, price=price, stock=stock_count)
    await state.set_state(BuyState.waiting_for_quantity)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Quay lại", callback_data="shop_menu")]
        ]
    )
    text = (
        f"📦 **MUA HÀNG**: `{prod_type.upper()}`\n"
        f"• Giá bán: **{price:,} VNĐ / 1 acc**\n"
        f"• Tồn kho: **{stock_count} tài khoản**\n\n"
        f"💬 **Vui lòng nhập số lượng bạn muốn mua bằng cách nhắn trực tiếp số (ví dụ: `1`, `2`, `5`...) vào khung chat này:**"
    )

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            text, reply_markup=keyboard, parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            text, reply_markup=keyboard, parse_mode="Markdown"
        )


@router.message(BuyState.waiting_for_quantity, F.text)
async def process_buy_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(
            "⚠️ Vui lòng chỉ nhập số lượng dạng chữ số (ví dụ: 1, 2, 3...)"
        )
        return

    quantity = int(message.text)
    data = await state.get_data()
    prod_type = data.get("prod_type")
    price = data.get("price")
    stock = data.get("stock")

    if quantity <= 0:
        await message.answer("⚠️ Số lượng phải lớn hơn 0.")
        return

    if quantity > stock:
        await message.answer(
            f"❌ Kho không đủ số lượng! Hiện tại chỉ còn lại {stock} tài khoản."
        )
        return

    total_price = quantity * price
    user_id = message.from_user.id
    user_balance = database["balance"].get(user_id, 0)

    if user_balance < total_price:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💰 Nạp Tiền Ngay", callback_data="deposit_menu"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Quay lại", callback_data="back_home"
                    )
                ],
            ]
        )
        await message.answer(
            f"❌ **Số dư không đủ!**\n"
            f"• Tổng tiền cần trả: **{total_price:,} VNĐ**\n"
            f"• Số dư ví của bạn: **{user_balance:,} VNĐ**\n\n"
            f"Vui lòng nạp thêm tiền để tiếp tục mua hàng.",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
        await state.clear()
        return

    # Trừ tiền và xuất kho
    database["balance"][user_id] = user_balance - total_price
    purchased_accounts = []
    for _ in range(quantity):
        acc = database["inventory"][prod_type].pop(0)
        purchased_accounts.append(acc)

    await state.clear()

    acc_text = "\n".join([f"`{acc}`" for acc in purchased_accounts])
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Tiếp Tục Mua Sắm", callback_data="shop_menu"
                )
            ]
        ]
    )

    await message.answer(
        f"✅ **GIAO DỊCH THÀNH CÔNG!**\n\n"
        f"• Sản phẩm: `{prod_type.upper()}` x{quantity}\n"
        f"• Tổng thanh toán: **{total_price:,} VNĐ**\n"
        f"• Số dư ví còn lại: **{database['balance'][user_id]:,} VNĐ**\n\n"
        f"📦 **Thông tin tài khoản của bạn:**\n{acc_text}",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


# --- NẠP TIỀN & HIỂN THỊ QR CODE (TỰ ĐỘNG GỬI DUYỆT CHO ADMIN) ---
@router.callback_query(F.data == "deposit_menu")
async def deposit_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="50.000 VNĐ", callback_data="dep_50000"
                ),
                InlineKeyboardButton(
                    text="100.000 VNĐ", callback_data="dep_100000"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="200.000 VNĐ", callback_data="dep_200000"
                ),
                InlineKeyboardButton(
                    text="500.000 VNĐ", callback_data="dep_500000"
                ),
            ],
            [InlineKeyboardButton(text="⬅️ Quay lại", callback_data="back_home")],
        ]
    )
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            "💳 **CHỌN MỨC TIỀN CẦN NẠP**\n\nVui lòng chọn số tiền bạn muốn nạp vào hệ thống:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
    else:
        await callback.message.edit_text(
            "💳 **CHỌN MỨC TIỀN CẦN NẠP**\n\nVui lòng chọn số tiền bạn muốn nạp vào hệ thống:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )


@router.callback_query(F.data.startswith("dep_"))
async def process_deposit_amount(callback: CallbackQuery, state: FSMContext):
    amount = int(callback.data.split("_")[1])
    user = callback.from_user
    code_nap = f"NAP{user.id}"

    bank = database["bank_info"]
    text = (
        f"📌 **QUÉT MÃ QR ĐỂ NẠP TIỀN**\n\n"
        f"• Ngân hàng: `{bank['name']}`\n"
        f"• Số tài khoản: `{bank['stk']}`\n"
        f"• Chủ tài khoản: `{bank['owner']}`\n"
        f"• Chi nhánh: `{bank['branch']}`\n"
        f"• Số tiền: **{amount:,} VNĐ**\n"
        f"• Nội dung chuyển khoản (BẮT BUỘC): `{code_nap}`\n\n"
        f"⏳ *Vui lòng quét mã QR chuyển khoản đúng số tiền và đúng nội dung. Hệ thống sẽ tự động gửi yêu cầu để Admin xác nhận.*"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Quay lại", callback_data="back_home")]
        ]
    )

    # Gửi mã QR yêu cầu cho khách (kèm thông tin)
    await callback.message.delete()
    await callback.message.answer_photo(
        photo="https://cdn.phototourl.com/member/2026-10-07-4782d3ec-1cd5-48f6-b290-796675497b63.png",
        caption=text,
        reply_markup=keyboard,
        parse_mode="Markdown",
    )

    # Tự động tạo yêu cầu và gửi thẳng thông báo sang cho Admin (Khách không cần gửi ảnh nữa)
    pending_id = f"{user.id}_{amount}"
    database["pending_deposits"][pending_id] = {
        "user_id": user.id,
        "amount": amount,
    }

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Duyệt", callback_data=f"approve_{pending_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Từ chối", callback_data=f"reject_{pending_id}"
                ),
            ]
        ]
    )

    username_str = f"@{user.username}" if user.username else "Không có"
    await callback.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"🔔 **CÓ YÊU CẦU NẠP TIỀN MỚI!**\n\n"
            f"• Khách hàng: {username_str} (ID: `{user.id}`)\n"
            f"• Số tiền yêu cầu: **{amount:,} VNĐ**\n"
            f"• Nội dung chuyển: `{code_nap}`\n\n"
            f"*(Khách đã mở mã QR, chờ bạn kiểm tra tài khoản ngân hàng để duyệt!)*"
        ),
        reply_markup=admin_keyboard,
        parse_mode="Markdown",
    )


@router.callback_query(
    F.data.startswith("approve_") | F.data.startswith("reject_")
)
async def handle_deposit_action(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "❌ Bạn không có quyền thực hiện thao tác này!", show_alert=True
        )
        return

    action, pending_id = callback.data.split("_", 1)
    deposit_info = database["pending_deposits"].get(pending_id)

    if not deposit_info:
        await callback.message.edit_text(
            text="⚠️ Đơn nạp này đã được xử lý trước đó hoặc không tồn tại."
        )
        return

    target_user_id = deposit_info["user_id"]
    amount = deposit_info["amount"]

    if action == "approve":
        current = database["balance"].get(target_user_id, 0)
        database["balance"][target_user_id] = current + amount

        await callback.message.edit_text(
            text=f"✅ **ĐÃ DUYỆT THÀNH CÔNG**\nĐã cộng {amount:,} VNĐ cho user `{target_user_id}`.",
            parse_mode="Markdown",
        )
        await callback.bot.send_message(
            target_user_id,
            f"🎉 **Nạp tiền thành công!** Tài khoản của bạn vừa được Admin cộng **{amount:,} VNĐ**.",
            parse_mode="Markdown",
        )
    else:
        await callback.message.edit_text(
            text=f"❌ **ĐÃ TỪ CHỐI ĐƠN NẠP** của user `{target_user_id}`.",
            parse_mode="Markdown",
        )
        await callback.bot.send_message(
            target_user_id,
            "❌ Yêu cầu nạp tiền của bạn đã bị từ chối hoặc không tìm thấy giao dịch. Vui lòng liên hệ Admin để được hỗ trợ.",
        )

    del database["pending_deposits"][pending_id]


@router.callback_query(F.data == "back_home")
async def back_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Mua Tài Khoản", callback_data="shop_menu")],
            [InlineKeyboardButton(text="💰 Nạp Tiền", callback_data="deposit_menu")],
            [
                InlineKeyboardButton(
                    text="👤 Tài Khoản Của Tôi", callback_data="profile"
                )
            ],
        ]
    )
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            "👋 Chào mừng bạn trở lại **SHOP ACC MEO**!\nVui lòng chọn chức năng:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
    else:
        await callback.message.edit_text(
            "👋 Chào mừng bạn trở lại **SHOP ACC MEO**!\nVui lòng chọn chức năng:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = database["balance"].get(user_id, 0)
    text = (
        f"👤 **THÔNG TIN TÀI KHOẢN**\n\n"
        f"• ID của bạn: `{user_id}`\n"
        f"• Số dư ví: **{balance:,} VNĐ**"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Quay lại", callback_data="back_home")]
        ]
    )
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            text, reply_markup=keyboard, parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            text, reply_markup=keyboard, parse_mode="Markdown"
        )


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot đang chạy...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
