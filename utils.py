import datetime
import os
from PIL import Image, ImageDraw, ImageFont

def format_num(n):
    return f"{n:,.0f}".replace(',', ' ')

def generate_receipt_image(order_data):
    # Rasm o'lchami va ranglari
    width = 600
    # Xonalar soniga qarab bo'yini hisoblash
    rooms = order_data.get('rooms', [])
    height = 250 + (len(rooms) * 200) + 150
    
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Shriftlar
    try:
        font_path = "C:\\Windows\\Fonts\\arial.ttf"
        font_main = ImageFont.truetype(font_path, 24)
        font_bold = ImageFont.truetype(font_path, 30)
        font_small = ImageFont.truetype(font_path, 18)
    except:
        font_main = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Sarlavha
    draw.rectangle([0, 0, width, 80], fill=(41, 128, 185))
    draw.text((width//2, 40), "RAYYON PARDALAR", font=font_bold, fill=(255, 255, 255), anchor="mm")
    
    y = 110
    draw.text((30, y), f"Mijoz: {order_data.get('client_name')}", font=font_main, fill=(0, 0, 0))
    draw.text((width-30, y), f"Sana: {order_data.get('date')}", font=font_small, fill=(100, 100, 100), anchor="ra")
    
    y += 50
    draw.line([30, y, width-30, y], fill=(200, 200, 200), width=1)
    y += 20
    
    for room in rooms:
        # Xona sarlavhasi
        draw.text((30, y), f"🏠 {room.get('room_name')}", font=font_bold, fill=(41, 128, 185))
        y += 40
        
        detail_lines = []
        if room.get('tyul_on'):
            detail_lines.append(f"Tyul ({room.get('tyul_code')}): {room.get('tyul_metraj'):.2f}m x {format_num(room.get('tyul_price'))}")
        if room.get('part_on'):
            detail_lines.append(f"Parter ({room.get('part_code')}): {room.get('part_metraj'):.2f}m x {format_num(room.get('part_price'))}")
        
        # Tikuv va boshqalar
        if room.get('zash_on'):
            detail_lines.append(f"Zashitka: {format_num(room.get('zash_summa'))}")
            
        for line in detail_lines:
            draw.text((50, y), line, font=font_small, fill=(50, 50, 50))
            y += 25
            
        draw.text((width-30, y), f"Xona jami: {format_num(room.get('jami'))} so'm", font=font_main, fill=(0, 0, 0), anchor="ra")
        y += 40
        draw.line([30, y, width-30, y], fill=(240, 240, 240), width=1)
        y += 20

    y += 20
    draw.rectangle([30, y, width-30, y+60], fill=(41, 128, 185))
    draw.text((width//2, y+30), f"UMUMIY HISOB: {format_num(order_data.get('total_summa'))} SO'M", font=font_bold, fill=(255, 255, 255), anchor="mm")
    
    y += 80
    draw.text((width//2, y), "Bizni tanlaganingiz uchun rahmat!", font=font_small, fill=(100, 100, 100), anchor="mm")
    y += 25
    draw.text((width//2, y), "Telegram: @rayyonpardalar | Instagram: @rayyon_pardalar", font=font_small, fill=(41, 128, 185), anchor="mm")
    
    # Rasmni saqlash
    file_path = f"receipt_{order_data.get('client_name')}_{datetime.datetime.now().strftime('%H%M%S')}.png"
    img.save(file_path)
    return file_path
