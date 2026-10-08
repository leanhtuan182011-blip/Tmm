import asyncio
import datetime
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
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

# Cấu hình Token và Admin ID chính xác của bạn
TOKEN = "8764217727:AAHRRldohQkBBtSVBl6hk3KHIZW3ShTJS8Y"
ADMIN_ID = 8810248698

# Link nhóm bắt buộc tham gia và Username hỗ trợ
REQUIRED_CHANNEL_URL = "https://t.me/+ucEoZDfmrtM4MTc1"
# Nếu nhóm/channel của bạn là dạng public (có username @), hãy điền username vào đây để check được bằng get_chat_member.
# Nếu là nhóm private hoàn toàn, bot cần được add làm Admin của nhóm để có quyền check thành viên.
# Ở đây ta mặc định hỗ trợ cơ chế nút bấm xác nhận join.

# Kho dữ liệu và danh mục sản phẩm
database = {
    "balance": {},  # {user_id: số_dư}
    "all_users": set(),  # Lưu danh sách tất cả user đã vào bot để bắn thông báo hàng về
    "inventory": {
        "hotmail": [],
        "igclonew": [],
        "igdaspam": [],
        "igngam": [],
        "fbreg": [],
        "fb8page": [],
        "fb15page": [],
        "fb282": [],
        "clone_1_5": [],
        "telegram": [],
        "youtube": [],
    },
    "prices": {
        "hotmail": 100,
        "igclonew": 1000,
        "igdaspam": 500,
        "igngam": 1200,
        "fbreg": 2000,
        "fb8page": 12000,
        "fb15page": 18000,
        "fb282": 50,
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
    "orders": {},
    "history": {},
}

# Bàn phím Menu chính bên dưới (Reply Keyboard)
main_reply_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍️ Sản phẩm"), KeyboardButton(text="👛 Ví")],
        [KeyboardButton(text="🛡️ Bảo hành"), KeyboardButton(text="💬 Hỗ trợ")],
        [KeyboardButton(text="👤 Tài khoản"), KeyboardButton(text="🌐 Nạp tiền")],
        [
            KeyboardButton(text="📦 Đơn hàng"),
            KeyboardButton(text="📜 Lịch sử giao dịch"),
        ],
    ],
    resize_keyboard=True,
)


class BuyState(StatesGroup):
    waiting_for_quantity = State()


router = Router()


# Hàm kiểm tra và tạo giao diện chào mừng khi đã gia nhập nhóm
async def send_welcome_menu(message_or_callback):
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
    text_intro = (
        "👋 Chào mừng bạn đến với **SHOP CLONE RẺ**!\n\n"
        "Vui lòng chọn chức năng bên dưới:"
    )

    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(
            text_intro, reply_markup=main_reply_kb
        )
        await message_or_callback.message.answer(
            "⚡ Bảng điều khiển nhanh:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
    else:
        await message_or_callback.answer(
            text_intro, reply_markup=main_reply_kb
        )
        await message_or_callback.answer(
            "⚡ Bảng điều khiển nhanh:",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    database["all_users"].add(message.from_user.id)

    # Giao diện yêu cầu gia nhập nhóm trước khi dùng bot
    join_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔗 Tham gia Nhóm Ngay", url=REQUIRED_CHANNEL_URL
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Xác nhận đã tham gia", callback_data="check_join"
                )
            ],
        ]
    )

    await message.answer(
        "⚠️ **THÔNG BÁO YÊU CẦU**\n\n"
        "Để sử dụng **SHOP CLONE RẺ**, bạn bắt buộc phải tham gia nhóm thông báo của shop trước!\n\n"
        "👉 Bấm nút bên dưới để vào nhóm, sau đó quay lại bấm **'Xác nhận đã tham gia'**.",
        reply_markup=join_keyboard,
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "check_join")
async def callback_check_join(callback: CallbackQuery):
    # Cho phép qua thẳng menu chính khi bấm xác nhận
    await callback.message.delete()
    await callback.answer(
        "✅ Xác nhận thành công! Chào mừng bạn đến với shop.", show_alert=True
    )
    await send_welcome_menu(callback)


# --- BẢNG QUẢN TRỊ ADMIN VÀ CÁC LỆNH THÊM KHO ---
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Bạn không có quyền truy cập bảng quản trị!")
        return

    inv = database["inventory"]
    p = database["prices"]
    text = (
        f"👑 **BẢNG QUẢN TRỊ ADMIN - SHOP CLONE RẺ**\n\n"
        f"• Trạng thái Bot: 🟢 Đang hoạt động\n"
        f"• Tổng user đã dùng bot: {len(database['all_users'])}\n"
        f"• Thành viên lưu số dư: {len(database['balance'])}\n\n"
        f"📦 **Tồn kho hiện tại:**\n"
        f"- Hotmail: {len(inv['hotmail'])} ({p['hotmail']}đ)\n"
        f"- IG Clone New: {len(inv['igclonew'])} ({p['igclonew']:,}đ)\n"
        f"- IG Qua Spam: {len(inv['igdaspam'])} ({p['igdaspam']:,}đ)\n"
        f"- IG Ngâm+Nuôi: {len(inv['igngam'])} ({p['igngam']:,}đ)\n"
        f"- FB Reg New: {len(inv['fbreg'])} ({p['fbreg']:,}đ)\n"
        f"- FB Kẹp 8 Page: {len(inv['fb8page'])} ({p['fb8page']:,}đ)\n"
        f"- FB Kẹp 15 Page: {len(inv['fb15page'])} ({p['fb15page']:,}đ)\n"
        f"- FB 282: {len(inv['fb282'])} ({p['fb282']}đ)\n"
        f"- Clone 1-5 Page: {len(inv['clone_1_5'])} ({p['clone_1_5']:,}đ)\n"
        f"- Telegram: {len(inv['telegram'])} ({p['telegram']:,}đ)\n"
        f"- Youtube Premium: {len(inv['youtube'])} ({p['youtube']:,}đ)\n\n"
        f"🛠️ **Cú pháp Thêm Kho (Dán danh sách acc phía sau):**\n"
        f"• `/themhotmail [acc|pass]`\n"
        f"• `/themisclonew [acc|pass]`\n"
        f"• `/themisdaspam [acc|pass]`\n"
        f"• `/themisngam [acc|pass]`\n"
        f"• `/themfbreg [acc|pass]`\n"
        f"• `/themfb8page [acc|pass]`\n"
        f"• `/themfb15page [acc|pass]`\n"
        f"• `/them282 [acc|pass]`\n"
        f"• `/themclone15 [acc|pass]`\n"
        f"• `/themtelegram [acc|pass]`\n"
        f"• `/themyoutube [acc|pass]`\n\n"
        f"⚙️ **Lệnh cộng tiền:** `/cong [user_id] [số_tiền]`"
    )
    await message.answer(text, parse_mode="Markdown")


async def broadcast_new_stock(bot: Bot, product_name: str, count: int):
    """Hàm tự động gửi thông báo tới tất cả user khi có hàng mới lên kho"""
    if not database["all_users"]:
        return

    notification_text = (
        f"🚨 **THÔNG BÁO: HÀNG MỚI VỀ!** 🚨\n\n"
        f"• Sản phẩm: **{product_name.upper()}**\n"
        f"• Số lượng vừa lên kho: **{count} tài khoản**\n\n"
        f"🛒 Nhanh tay truy cập bot để mua ngay kẻo hết!"
    )

    shop_btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Mua Ngay Tại Shop", callback_data="shop_menu"
                )
            ]
        ]
    )

    for uid in list(database["all_users"]):
        try:
            await bot.send_message(
                chat_id=uid, text=notification_text, reply_markup=shop_btn, parse_mode="Markdown"
            )
            await asyncio.sleep(0.05)  # Tránh spam quá nhanh gây lỗi Floodwait từ Telegram
        except Exception:
            # Có thể user đã chặn bot hoặc xóa tài khoản
            pass


async def add_inventory_helper(message: Message, key: str, name: str):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Bạn không có quyền sử dụng lệnh này!")
        return

    lines = message.text.split("\n")
    accounts_to_add = []
    for line in lines[1:]:
        acc_str = line.strip()
        if acc_str:
            accounts_to_add.append(acc_str)

    if not accounts_to_add and len(message.text.split(maxsplit=1)) > 1:
        raw_text = message.text.split(maxsplit=1)[1]
        for acc_str in raw_text.split("\n"):
            if acc_str.strip():
                accounts_to_add.append(acc_str.strip())

    if not accounts_to_add:
        await message.answer(
            f"⚠️ Vui lòng nhập danh sách tài khoản cần thêm vào sau lệnh `{message.text.split()[0]}` (mỗi acc một dòng)."
        )
        return

    database["inventory"][key].extend(accounts_to_add)
    added_count = len(accounts_to_add)
    await message.answer(
        f"✅ Đã thêm thành công **{added_count}** tài khoản vào kho `{name}`!\n"
        f"📢 Đang tiến hành gửi thông báo có hàng đến tất cả thành viên..."
    )

    # Kích hoạt gửi thông báo hàng về cho tất cả mọi người
    asyncio.create_task(broadcast_new_stock(message.bot, name, added_count))


@router.message(Command("themhotmail"))
async def add_hotmail(message: Message):
    await add_inventory_helper(message, "hotmail", "Hotmail")


@router.message(Command("themisclonew"))
async def add_igclonew(message: Message):
    await add_inventory_helper(message, "igclonew", "IG Clone New")


@router.message(Command("themisdaspam"))
async def add_igdaspam(message: Message):
    await add_inventory_helper(message, "igdaspam", "IG Qua Spam")


@router.message(Command("themisngam"))
async def add_igngam(message: Message):
    await add_inventory_helper(message, "igngam", "IG Ngâm+Nuôi")


@router.message(Command("themfbreg"))
async def add_fbreg(message: Message):
    await add_inventory_helper(message, "fbreg", "FB Reg New")


@router.message(Command("themfb8page"))
async def add_fb8page(message: Message):
    await add_inventory_helper(message, "fb8page", "FB Kẹp 8 Page")


@router.message(Command("themfb15page"))
async def add_fb15page(message: Message):
    await add_inventory_helper(message, "fb15page", "FB Kẹp 15 Page")


@router.message(Command("them282"))
async def add_fb282(message: Message):
    await add_inventory_helper(message, "fb282", "FB 282")


@router.message(Command("themclone15"))
async def add_clone15(message: Message):
    await add_inventory_helper(message, "clone_1_5", "Clone 1-5 Page")


@router.message(Command("themtelegram"))
async def add_telegram(message: Message):
    await add_inventory_helper(message, "telegram", "Telegram")


@router.message(Command("themyoutube"))
async def add_youtube(message: Message):
    await add_inventory_helper(message, "youtube", "Youtube Premium")


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

        time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if target_id not in database["history"]:
            database["history"][target_id] = []
        database["history"][target_id].append(
            {
                "time": time_str,
                "content": "Admin cộng tiền trực tiếp",
                "amount": amount,
            }
        )

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


# --- XỬ LÝ CÁC NÚT TỪ BÀN PHÍM REPLY (MENU DƯỚI) ---
@router.message(F.text == "🛍️ Sản phẩm")
async def btn_san_pham(message: Message, state: FSMContext):
    database["all_users"].add(message.from_user.id)
    await state.clear()
    await show_shop_menu(message)


@router.message(F.text.in_({"👛 Ví", "👤 Tài khoản"}))
async def btn_tai_khoan(message: Message, state: FSMContext):
    database["all_users"].add(message.from_user.id)
    await state.clear()
    user_id = message.from_user.id
    balance = database["balance"].get(user_id, 0)
    text = (
        f"👤 **THÔNG TIN TÀI KHOẢN**\n\n"
        f"• ID của bạn: `{user_id}`\n"
        f"• Số dư ví: **{balance:,} VNĐ**"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_reply_kb)


@router.message(F.text == "🛡️ Bảo hành")
async def btn_bao_hanh(message: Message):
    database["all_users"].add(message.from_user.id)
    text = (
        f"🛡️ **CHÍNH SÁCH BẢO HÀNH**\n\n"
        f"1. Bảo hành đổi mới 1-1 trong vòng 24h nếu tài khoản lỗi do nhà cung cấp (sai pass, checkpoint lần đầu).\n"
        f"2. Không bảo hành với các trường hợp đổi thông tin, change pass hoặc sử dụng vi phạm chính sách nền tảng.\n"
        f"3. Liên hệ hỗ trợ: `@truonganh445` nếu gặp sự cố."
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_reply_kb)


@router.message(F.text == "💬 Hỗ trợ")
async def btn_ho_tro(message: Message):
    database["all_users"].add(message.from_user.id)
    text = (
        f"💬 **HỖ TRỢ KHÁCH HÀNG**\n\n"
        f"• Mọi thắc mắc, khiếu nại hoặc cần nạp tiền thủ công vui lòng liên hệ trực tiếp Admin.\n"
        f"• Hỗ trợ chính thức: `@truonganh445`."
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_reply_kb)


@router.message(F.text == "🌐 Nạp tiền")
async def btn_nap_tien(message: Message, state: FSMContext):
    database["all_users"].add(message.from_user.id)
    await state.clear()
    await show_deposit_menu(message)


@router.message(F.text == "📦 Đơn hàng")
async def btn_don_hang(message: Message):
    database["all_users"].add(message.from_user.id)
    user_id = message.from_user.id
    user_orders = database["orders"].get(user_id, [])

    if not user_orders:
        await message.answer(
            "📦 Bạn chưa có đơn hàng nào hoặc chưa mua sản phẩm nào.",
            reply_markup=main_reply_kb,
        )
        return

    text = "📦 **LỊCH SỬ ĐƠN HÀNG CỦA BẠN**:\n\n"
    for idx, ord_item in enumerate(user_orders[-10:], 1):
        text += (
            f"--- Đơn #{idx} ({ord_item['time']}) ---\n"
            f"• Loại: `{ord_item['type'].upper()}` x{ord_item['quantity']}\n"
            f"• Tổng tiền: **{ord_item['total']:,} VNĐ**\n"
            f"• Tài khoản:\n"
        )
        for acc in ord_item["accounts"]:
            text += f"`{acc}`\n"
        text += "\n"

    await message.answer(text, parse_mode="Markdown", reply_markup=main_reply_kb)


@router.message(F.text == "📜 Lịch sử giao dịch")
async def btn_lich_su(message: Message):
    database["all_users"].add(message.from_user.id)
    user_id = message.from_user.id
    user_hist = database["history"].get(user_id, [])

    if not user_hist:
        await message.answer(
            "📜 Bạn chưa có giao dịch nạp tiền hoặc biến động số dư nào.",
            reply_markup=main_reply_kb,
        )
        return

    text = "📜 **LỊCH SỬ GIAO DỊCH GẦN ĐÂY**:\n\n"
    for item in user_hist[-10:]:
        text += f"• [{item['time']}] {item['content']} — **{item['amount']:+,} VNĐ**\n"

    await message.answer(text, parse_mode="Markdown", reply_markup=main_reply_kb)


# --- HỆ THỐNG MUA HÀNG & MENU SHOP ---
async def show_shop_menu(message_or_callback):
    inv = database["inventory"]
    p = database["prices"]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            # 1. Hotmail
            [
                InlineKeyboardButton(
                    text=f"📧 Hotmail ({len(inv['hotmail'])} có sẵn - {p['hotmail']}đ)",
                    callback_data="buy_hotmail",
                )
            ],
            # 2. Nhóm Instagram
            [
                InlineKeyboardButton(
                    text=f"📸 IG Clone New ({len(inv['igclonew'])} có sẵn - {p['igclonew']:,}đ)",
                    callback_data="buy_igclonew",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"📸 IG Qua Spam ({len(inv['igdaspam'])} có sẵn - {p['igdaspam']}đ)",
                    callback_data="buy_igdaspam",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"📸 IG Ngâm+Nuôi ({len(inv['igngam'])} có sẵn - {p['igngam']:,}đ)",
                    callback_data="buy_igngam",
                )
            ],
            # 3. Nhóm Facebook
            [
                InlineKeyboardButton(
                    text=f"📘 FB Reg New ({len(inv['fbreg'])} có sẵn - {p['fbreg']:,}đ)",
                    callback_data="buy_fbreg",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"📘 FB Kẹp 8 Page ({len(inv['fb8page'])} có sẵn - {p['fb8page']:,}đ)",
                    callback_data="buy_fb8page",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"📘 FB Kẹp 15 Page ({len(inv['fb15page'])} có sẵn - {p['fb15page']:,}đ)",
                    callback_data="buy_fb15page",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"📘 FB 282 ({len(inv['fb282'])} có sẵn - {p['fb282']}đ)",
                    callback_data="buy_fb282",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"📘 Clone 1-5 Page ({len(inv['clone_1_5'])} có sẵn - {p['clone_1_5']:,}đ)",
                    callback_data="buy_clone_1_5",
                )
            ],
            # 4. Các mặt hàng còn lại (Telegram, Youtube)
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

    text = "🛒 **DANH MỤC SẢN PHẨM - SHOP CLONE RẺ**\n\nVui lòng chọn loại tài khoản bạn muốn mua:"
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(
            text, reply_markup=keyboard, parse_mode="Markdown"
        )
    else:
        await message_or_callback.answer(
            text, reply_markup=keyboard, parse_mode="Markdown"
        )


@router.callback_query(F.data == "shop_menu")
async def callback_shop_menu(callback: CallbackQuery):
    await callback.message.delete()
    await show_shop_menu(callback)


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

    await callback.message.delete()
    await callback.message.answer(
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
        await message.answer(
            f"❌ **Số dư không đủ!**\n"
            f"• Tổng tiền cần trả: **{total_price:,} VNĐ**\n"
            f"• Số dư ví của bạn: **{user_balance:,} VNĐ**\n\n"
            f"Vui lòng nạp thêm tiền để tiếp tục mua hàng.",
            parse_mode="Markdown",
            reply_markup=main_reply_kb,
        )
        await state.clear()
        return

    database["balance"][user_id] = user_balance - total_price
    purchased_accounts = []
    for _ in range(quantity):
        acc = database["inventory"][prod_type].pop(0)
        purchased_accounts.append(acc)

    time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if user_id not in database["orders"]:
        database["orders"][user_id] = []
    database["orders"][user_id].append(
        {
            "type": prod_type,
            "quantity": quantity,
            "total": total_price,
            "accounts": purchased_accounts,
            "time": time_str,
        }
    )

    if user_id not in database["history"]:
        database["history"][user_id] = []
    database["history"][user_id].append(
        {
            "time": time_str,
            "content": f"Mua {quantity} {prod_type.upper()}",
            "amount": -total_price,
        }
    )

    await state.clear()

    acc_text = "\n".join([f"`{acc}`" for acc in purchased_accounts])
    await message.answer(
        f"✅ **GIAO DỊCH THÀNH CÔNG!**\n\n"
        f"• Sản phẩm: `{prod_type.upper()}` x{quantity}\n"
        f"• Tổng thanh toán: **{total_price:,} VNĐ**\n"
        f"• Số dư ví còn lại: **{database['balance'][user_id]:,} VNĐ**\n\n"
        f"📦 **Thông tin tài khoản của bạn:**\n{acc_text}\n\n"
        f"*(Bạn cũng có thể xem lại tại mục 'Đơn hàng')*",
        reply_markup=main_reply_kb,
        parse_mode="Markdown",
    )


# --- NẠP TIỀN & GỬI DUYỆT TỰ ĐỘNG CHO ADMIN ---
async def show_deposit_menu(message_or_callback):
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
    text = "💳 **CHỌN MỨC TIỀN CẦN NẠP**\n\nVui lòng chọn số tiền bạn muốn nạp vào hệ thống:"
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(
            text, reply_markup=keyboard, parse_mode="Markdown"
        )
    else:
        await message_or_callback.answer(
            text, reply_markup=keyboard, parse_mode="Markdown"
        )


@router.callback_query(F.data == "deposit_menu")
async def callback_deposit_menu(callback: CallbackQuery):
    await callback.message.delete()
    await show_deposit_menu(callback)


@router.callback_query(F.data.startswith("dep_"))
async def process_deposit_amount(callback: CallbackQuery):
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
        f"⏳ *Vui lòng chuyển khoản đúng số tiền và nội dung trên. Cần hỗ trợ liên hệ `@truonganh445`.*"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Quay lại", callback_data="back_home")]
        ]
    )

    await callback.message.delete()
    # URL ảnh QR mới theo yêu cầu
    await callback.message.answer_photo(
        photo="https://cdn.phototourl.com/member/2026-10-08-7d18514b-4b87-40ea-9012-3540fccbfeda.jpg",
        caption=text,
        reply_markup=keyboard,
        parse_mode="Markdown",
    )

    pending_id = f"{user.id}_{amount}_{int(asyncio.get_event_loop().time())}"
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
            f"• Nội dung chuyển: `{code_nap}`"
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
    time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if action == "approve":
        current = database["balance"].get(target_user_id, 0)
        database["balance"][target_user_id] = current + amount

        if target_user_id not in database["history"]:
            database["history"][target_user_id] = []
        database["history"][target_user_id].append(
            {
                "time": time_str,
                "content": "Nạp tiền qua chuyển khoản",
                "amount": amount,
            }
        )

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
            "❌ Yêu cầu nạp tiền của bạn đã bị từ chối hoặc không tìm thấy giao dịch. Vui lòng liên hệ @truonganh445 để được hỗ trợ.",
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
            "👋 Chào mừng bạn trở lại **SHOP CLONE RẺ**!\nVui lòng chọn chức năng:",
            reply_markup=main_reply_kb,
        )
        await callback.message.answer(
            "⚡ Bảng điều khiển:", reply_markup=keyboard, parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            "👋 Chào mừng bạn trở lại **SHOP CLONE RẺ**!\nVui lòng chọn chức năng:",
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
