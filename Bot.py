import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- CẤU HÌNH HỆ THỐNG (ĐÃ CẬP NHẬT CỦA BẠN) ---
TOKEN = "8764217727:AAHRRldohQkBBtSVBl6hk3KHIZW3ShTJS8Y"
ADMIN_ID = 8810248698

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- DATABASE MẪU ---
database = {
    "users": {},  # {user_id: số_dư_vnđ}
    "stats": {"total_sold": 0, "total_revenue": 0},
    "bank_info": {
        "ngan_hang": "VietinBank",
        "stk": "99996218939",
        "chu_tk": "LE QUANG TUAN"
    },
    "kho": {
        "hotmail": [
            "acc_test_1@hotmail.com|pass123", 
            "acc_test_2@hotmail.com|pass456"
        ],
        "ig_clone": [
            "ig_clone_1|abc123xyz"
        ],
        "ig_ngam": [],
        "clone_reg": [],
        "acc_282": [],
        "lien_quan": []
    },
    "prices": {
        "hotmail": 800,
        "ig_clone": 1500,
        "ig_ngam": 2000,
        "clone_reg": 2500,
        "acc_282": 100,
        "lien_quan": 300
    }
}

# --- BÀN PHÍM MENU CHÍNH ---
main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛍 Sản phẩm"), KeyboardButton(text="👛 Ví")],
        [KeyboardButton(text="🛡 Bảo hành"), KeyboardButton(text="💬 Hỗ trợ")],
        [KeyboardButton(text="👤 Tài khoản"), KeyboardButton(text="🪙 Nạp tiền")],
        [KeyboardButton(text="📦 Đơn hàng"), KeyboardButton(text="📜 Lịch sử giao dịch")]
    ],
    resize_keyboard=True
)

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ================= 1. KHU VỰC KHÁCH HÀNG =================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Chào mừng bạn đến với hệ thống bán tài khoản tự động!\n"
        "Vui lòng chọn chức năng trên bàn phím bên dưới 👇",
        reply_markup=main_menu_kb
    )

@dp.message(F.text == "🛍 Sản phẩm")
@dp.message(Command("menu"))
async def show_products(message: types.Message):
    k = database["kho"]
    p = database["prices"]
    
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✉️ Hotmail ({len(k['hotmail'])} tồn) - {p['hotmail']:,}đ", callback_data="buy_hotmail")],
        [InlineKeyboardButton(text=f"📷 IG Clone ({len(k['ig_clone'])} tồn) - {p['ig_clone']:,}đ", callback_data="buy_ig_clone")],
        [InlineKeyboardButton(text=f"📸 IG Ngâm ({len(k['ig_ngam'])} tồn) - {p['ig_ngam']:,}đ", callback_data="buy_ig_ngam")],
        [InlineKeyboardButton(text=f"📦 Clone mới reg ({len(k['clone_reg'])} tồn) - {p['clone_reg']:,}đ", callback_data="buy_clone_reg")],
        [InlineKeyboardButton(text=f"🛡 Acc 282 ({len(k['acc_282'])} tồn) - {p['acc_282']:,}đ", callback_data="buy_acc_282")],
        [InlineKeyboardButton(text=f"⚔️ Liên Quân Random ({len(k['lien_quan'])} tồn) - {p['lien_quan']:,}đ", callback_data="buy_lien_quan")]
    ])
    
    await message.answer(
        "🎁 **THÔNG TIN SẢN PHẨM**\n\nVui lòng chọn sản phẩm bạn muốn mua:",
        reply_markup=inline_kb,
        parse_mode="Markdown"
    )

@dp.message(F.text == "👤 Tài khoản")
@dp.message(F.text == "👛 Ví")
async def show_account(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Không có"
    so_du = database["users"].get(user_id, 0)
    
    text = (
        f"👤 **THÔNG TIN TÀI KHOẢN & VÍ**\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"👤 User: @{username}\n"
        f"🪙 Số dư ví: `{so_du:,} VNĐ`\n"
        f"📦 Tổng doanh số hệ thống đã bán: `{database['stats']['total_sold']} đơn`"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🪙 Nạp tiền")
@dp.message(Command("naptien"))
async def deposit_money(message: types.Message):
    user_id = message.from_user.id
    b = database["bank_info"]
    noi_dung = f"NAP{user_id}"
    
    await message.answer(
        f"🪙 **HƯỚNG DẪN NẠP TIỀN TỰ ĐỘNG**\n\n"
        f"Chuyển khoản chính xác thông tin sau để nạp tự động:\n"
        f"- Ngân hàng: **{b['ngan_hang']}**\n"
        f"- STK: `{b['stk']}`\n"
        f"- Chủ TK: **{b['chu_tk']}**\n"
        f"- Nội dung CK: `{noi_dung}`\n\n"
        f"⏳ Tiền sẽ vào ví ngay sau khi Admin duyệt đơn.",
        parse_mode="Markdown"
    )

@dp.message(F.text == "🛡 Bảo hành")
async def warranty_policy(message: types.Message):
    await message.answer("🛡 **CHÍNH SÁCH BẢO HÀNH**\n\n• Hỗ trợ đổi mới tài khoản lỗi do nhà sản xuất trong vòng 24h đầu.")

@dp.message(F.text == "💬 Hỗ trợ")
async def support_info(message: types.Message):
    await message.answer("💬 Vui lòng liên hệ trực tiếp Admin để được hỗ trợ giải đáp thắc mắc.")

@dp.message(F.text == "📦 Đơn hàng")
@dp.message(F.text == "📜 Lịch sử giao dịch")
async def history_orders(message: types.Message):
    await message.answer("📦 Bạn chưa có giao dịch nào gần đây.")


# ================= 2. HỆ THỐNG MUA HÀNG TỰ ĐỘNG 100% =================

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    product_key = callback.data.replace("buy_", "")
    user_id = callback.from_user.id
    
    if product_key not in database["kho"]:
        await callback.answer("Sản phẩm không tồn tại!", show_alert=True)
        return
    
    kho_hang = database["kho"][product_key]
    gia_tien = database["prices"][product_key]
    so_du_hien_tai = database["users"].get(user_id, 0)
    
    if len(kho_hang) == 0:
        await callback.answer("❌ Sản phẩm này đã tạm hết hàng, vui lòng quay lại sau!", show_alert=True)
        return
        
    if so_du_hien_tai < gia_tien:
        await callback.answer(f"❌ Số dư không đủ! Bạn cần {gia_tien:,} VNĐ nhưng ví chỉ có {so_du_hien_tai:,} VNĐ.", show_alert=True)
        return
        
    database["users"][user_id] = so_du_hien_tai - gia_tien
    tai_khoan_mua = kho_hang.pop(0)
    
    database["stats"]["total_sold"] += 1
    database["stats"]["total_revenue"] += gia_tien
    
    await callback.message.answer(
        f"🎉 **MUA HÀNG THÀNH CÔNG!**\n\n"
        f"📦 Sản phẩm: `{product_key.upper()}`\n"
        f"🔑 Tài khoản:\n`{tai_khoan_mua}`\n\n"
        f"🪙 Đã trừ `{gia_tien:,} VNĐ` vào ví.",
        parse_mode="Markdown"
    )
    await callback.answer("Thành công!")


# ================= 3. KHU VỰC ĐẶC QUYỀN ADMIN =================

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Bạn không có quyền truy cập khu vực này!")
        return
    
    k = database["kho"]
    b = database["bank_info"]
    
    text = (
        f"👑 **BẢNG QUẢN TRỊ ADMIN (ĐẶC QUYỀN)**\n\n"
        f"• Trạng thái Bot: 🟢 Đang hoạt động\n"
        f"• Tổng đơn bán: {database['stats']['total_sold']} | Doanh thu: {database['stats']['total_revenue']:,} VNĐ\n\n"
        f"📦 **Tồn kho hiện tại:**\n"
        f"- Hotmail: {len(k['hotmail'])} | IG Clone: {len(k['ig_clone'])}\n"
        f"- IG Ngâm: {len(k['ig_ngam'])} | Clone Reg: {len(k['clone_reg'])}\n"
        f"- Acc 282: {len(k['acc_282'])} | Liên Quân: {len(k['lien_quan'])}\n\n"
        f"🛠 **Cú pháp Thêm Kho:**\n"
        f"• `/themhotmail [acc|pass]`\n"
        f"• `/themigclone [acc|pass]`\n"
        f"• `/themigngam [acc|pass]`\n"
        f"• `/themclonereg [acc|pass]`\n"
        f"• `/themacs282 [acc|pass]`\n"
        f"• `/themlienquan [acc|pass]`\n\n"
        f"⚙️ **Cấu hình khác:** `/setbank TênNH|STK|ChủTK`\n"
        f"🪙 **Cộng tiền test:** `/cong [user_id] [số_tiền]`"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command(commands=["themhotmail", "themigclone", "themigngam", "themclonereg", "themacs282", "themlienquan"]))
async def add_inventory(message: types.Message):
    if not is_admin(message.from_user.id):
        return
        
    cmd = message.text.split(" ")[0].replace("/", "")
    args = message.text.replace(f"/{cmd}", "").strip()
    
    if not args:
        await message.answer(f"⚠️ Vui lòng nhập thông tin acc đi kèm. Ví dụ: `/{cmd} user|pass`", parse_mode="Markdown")
        return
        
    mapping = {
        "themhotmail": "hotmail",
        "themigclone": "ig_clone",
        "themigngam": "ig_ngam",
        "themclonereg": "clone_reg",
        "themacs282": "acc_282",
        "themlienquan": "lien_quan"
    }
    
    target_kho = mapping.get(cmd)
    if target_kho:
        database["kho"][target_kho].append(args)
        await message.answer(f"✅ Đã thêm vào kho **{target_kho.upper()}** thành công!\n📦 Tổng tồn kho loại này: {len(database['kho'][target_kho])} acc.", parse_mode="Markdown")

@dp.message(Command("setbank"))
async def set_bank_info(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    try:
        args = message.text.replace("/setbank", "").strip()
        parts = args.split("|")
        if len(parts) == 3:
            database["bank_info"]["ngan_hang"] = parts[0].strip()
            database["bank_info"]["stk"] = parts[1].strip()
            database["bank_info"]["chu_tk"] = parts[2].strip()
            await message.answer("✅ Đã cập nhật thông tin Ngân hàng/QR thành công!")
        else:
            await message.answer("⚠️ Sai cú pháp! Dùng: `/setbank TênNH|STK|ChủTK`", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Lỗi: {e}")

@dp.message(Command("cong"))
async def admin_add_money(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    try:
        parts = message.text.split(" ")
        target_user = int(parts[1])
        amount = int(parts[2])
        
        current_bal = database["users"].get(target_user, 0)
        database["users"][target_user] = current_bal + amount
        
        await message.answer(f"✅ Đã cộng `{amount:,} VNĐ` cho user `{target_user}` thành công!")
        try:
            await bot.send_message(target_user, f"🎉 Ví của bạn vừa được cộng `{amount:,} VNĐ` từ hệ thống.")
        except:
            pass
    except Exception:
        await message.answer("⚠️ Sai cú pháp! Dùng: `/cong [user_id] [số_tiền]`")


# --- CHẠY BOT ---
if __name__ == "__main__":
    import asyncio
    print("Bot đang chạy...")
    asyncio.run(dp.start_polling(bot))
