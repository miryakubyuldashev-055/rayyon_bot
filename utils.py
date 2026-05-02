import datetime
import os
from PIL import Image, ImageDraw, ImageFont

def format_num(n):
    return f"{n:,.0f}".replace(',', ' ')

def generate_receipt_image(order_data):
    # Rasm o'lchami va ranglari (High Resolution: 1200px)
    width = 1200
    rooms = order_data.get('rooms', [])
    # Bo'yini hisoblash (Increased height for REALLY large fonts)
    height = 1100 + (len(rooms) * 1100) + 700
    
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Shriftlar (Segoe UI high resolution)
    try:
        font_path = "C:\\Windows\\Fonts\\segoeui.ttf"
        font_path_bold = "C:\\Windows\\Fonts\\seguisb.ttf"
        font_main = ImageFont.truetype(font_path, 150)
        font_bold = ImageFont.truetype(font_path_bold, 180)
        font_small = ImageFont.truetype(font_path, 110)
        font_footer = ImageFont.truetype(font_path, 90)
    except:
        try:
            font_path = "C:\\Windows\\Fonts\\arial.ttf"
            font_main = ImageFont.truetype(font_path, 150)
            font_bold = ImageFont.truetype(font_path, 180, index=1)
            font_small = ImageFont.truetype(font_path, 110)
            font_footer = ImageFont.truetype(font_path, 90)
        except:
            font_main = ImageFont.load_default()
            font_bold = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_footer = ImageFont.load_default()

    # Sarlavha (Premium Blue Gradient Style)
    header_color = (41, 128, 185)
    draw.rectangle([0, 0, width, 300], fill=header_color)
    draw.text((width//2, 150), "RAYYON PARDALAR", font=font_bold, fill=(255, 255, 255), anchor="mm")
    
    y = 380
    # Mijoz va Sana
    draw.text((60, y), f"Mijoz: {order_data.get('client_name')}", font=font_main, fill=(0, 0, 0))
    draw.text((width-60, y+20), f"Sana: {order_data.get('date')}", font=font_small, fill=(100, 100, 100), anchor="ra")
    
    y += 200
    draw.line([60, y, width-60, y], fill=(200, 200, 200), width=6)
    y += 120
    
    for room in rooms:
        # Xona sarlavhasi
        draw.text((60, y), f"🏠 {room.get('room_name')}", font=font_bold, fill=(41, 128, 185))
        y += 200
        
        detail_lines = []
        if room.get('tyul_on'):
            detail_lines.append(f"• Tyul ({room.get('tyul_code')}): {room.get('tyul_metraj'):.2f}m x {format_num(room.get('tyul_price'))}")
        if room.get('part_on'):
            detail_lines.append(f"• Parter ({room.get('part_code')}): {room.get('part_metraj'):.2f}m x {format_num(room.get('part_price'))}")
        
        # Tikuv va boshqalar
        if room.get('zash_on'):
            detail_lines.append(f"• Zashitka: {format_num(room.get('zash_summa'))}")
            
        for line in detail_lines:
            draw.text((80, y), line, font=font_small, fill=(50, 50, 50))
            y += 150
            
        y += 80
        draw.text((width-60, y), f"Xona jami: {format_num(room.get('jami'))} so'm", font=font_main, fill=(0, 0, 0), anchor="ra")
        y += 200
        draw.line([60, y, width-60, y], fill=(240, 240, 240), width=4)
        y += 140

    y += 60
    # Umumiy hisob (Highlighted box)
    box_height = 300
    draw.rectangle([40, y, width-40, y+box_height], fill=header_color)
    draw.text((width//2, y + box_height//2), f"UMUMIY: {format_num(order_data.get('total_summa'))} SO'M", font=font_bold, fill=(255, 255, 255), anchor="mm")
    
    y += box_height + 180
    draw.text((width//2, y), "Bizni tanlaganingiz uchun rahmat!", font=font_small, fill=(100, 100, 100), anchor="mm")
    y += 180
    draw.text((width//2, y), "Telegram: @rayyonpardalar | Instagram: @rayyon_pardalar", font=font_footer, fill=(41, 128, 185), anchor="mm")
    
    # Rasmni saqlash
    # Ensure receipts directory exists
    archive_dir = "receipts"
    os.makedirs(archive_dir, exist_ok=True)
    
    file_name = f"receipt_{order_data.get('client_name')}_{datetime.datetime.now().strftime('%H%M%S')}.png"
    file_path = os.path.join(archive_dir, file_name)
    img.save(file_path)
    return file_path
