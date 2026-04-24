import datetime
import os
from PIL import Image, ImageDraw, ImageFont

def format_num(n):
    return f"{n:,.0f}".replace(',', ' ')

def generate_receipt_image(order_data):
    # Rasm o'lchami va ranglari (High Resolution: 1200px)
    width = 1200
    rooms = order_data.get('rooms', [])
    # Bo'yini hisoblash (Double the original spacing)
    height = 500 + (len(rooms) * 400) + 300
    
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Shriftlar (Segoe UI high resolution)
    try:
        font_path = "C:\\Windows\\Fonts\\segoeui.ttf"
        font_path_bold = "C:\\Windows\\Fonts\\seguisb.ttf"
        font_main = ImageFont.truetype(font_path, 45)
        font_bold = ImageFont.truetype(font_path_bold, 60)
        font_small = ImageFont.truetype(font_path, 32)
        font_footer = ImageFont.truetype(font_path, 28)
    except:
        try:
            font_path = "C:\\Windows\\Fonts\\arial.ttf"
            font_main = ImageFont.truetype(font_path, 45)
            font_bold = ImageFont.truetype(font_path, 60, index=1) # Bold if possible
            font_small = ImageFont.truetype(font_path, 32)
            font_footer = ImageFont.truetype(font_path, 28)
        except:
            font_main = ImageFont.load_default()
            font_bold = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_footer = ImageFont.load_default()

    # Sarlavha (Premium Blue Gradient Style)
    header_color = (41, 128, 185)
    draw.rectangle([0, 0, width, 160], fill=header_color)
    draw.text((width//2, 80), "RAYYON PARDALAR", font=font_bold, fill=(255, 255, 255), anchor="mm")
    
    y = 220
    # Mijoz va Sana
    draw.text((60, y), f"Mijoz: {order_data.get('client_name')}", font=font_main, fill=(0, 0, 0))
    draw.text((width-60, y), f"Sana: {order_data.get('date')}", font=font_small, fill=(100, 100, 100), anchor="ra")
    
    y += 100
    draw.line([60, y, width-60, y], fill=(200, 200, 200), width=2)
    y += 50
    
    for room in rooms:
        # Xona sarlavhasi
        draw.text((60, y), f"🏠 {room.get('room_name')}", font=font_bold, fill=(41, 128, 185))
        y += 80
        
        detail_lines = []
        if room.get('tyul_on'):
            detail_lines.append(f"• Tyul ({room.get('tyul_code')}): {room.get('tyul_metraj'):.2f}m x {format_num(room.get('tyul_price'))}")
        if room.get('part_on'):
            detail_lines.append(f"• Parter ({room.get('part_code')}): {room.get('part_metraj'):.2f}m x {format_num(room.get('part_price'))}")
        
        # Tikuv va boshqalar
        if room.get('zash_on'):
            detail_lines.append(f"• Zashitka: {format_num(room.get('zash_summa'))}")
            
        for line in detail_lines:
            draw.text((100, y), line, font=font_small, fill=(50, 50, 50))
            y += 50
            
        y += 20
        draw.text((width-60, y), f"Xona jami: {format_num(room.get('jami'))} so'm", font=font_main, fill=(0, 0, 0), anchor="ra")
        y += 80
        draw.line([60, y, width-60, y], fill=(240, 240, 240), width=2)
        y += 50

    y += 40
    # Umumiy hisob (Highlighted box)
    box_height = 120
    draw.rectangle([60, y, width-60, y+box_height], fill=header_color)
    draw.text((width//2, y + box_height//2), f"UMUMIY HISOB: {format_num(order_data.get('total_summa'))} SO'M", font=font_bold, fill=(255, 255, 255), anchor="mm")
    
    y += box_height + 80
    draw.text((width//2, y), "Bizni tanlaganingiz uchun rahmat!", font=font_small, fill=(100, 100, 100), anchor="mm")
    y += 60
    draw.text((width//2, y), "Telegram: @rayyonpardalar | Instagram: @rayyon_pardalar", font=font_footer, fill=(41, 128, 185), anchor="mm")
    
    # Rasmni saqlash
    # Ensure receipts directory exists
    archive_dir = "receipts"
    os.makedirs(archive_dir, exist_ok=True)
    
    file_name = f"receipt_{order_data.get('client_name')}_{datetime.datetime.now().strftime('%H%M%S')}.png"
    file_path = os.path.join(archive_dir, file_name)
    img.save(file_path)
    return file_path
