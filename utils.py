import datetime
import os
from PIL import Image, ImageDraw, ImageFont

def format_num(n):
    return f"{n:,.0f}".replace(',', ' ')

def get_bubble_size(draw, text, font):
    # calculate exact width and height of text block
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def generate_receipt_image(order_data):
    # Vaqtinchalik katta fon (balandligi 5000 px)
    width = 900
    tmp_height = 6000
    img = Image.new('RGB', (width, tmp_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Shriftlar
    try:
        font_path = "C:\\Windows\\Fonts\\segoeui.ttf"
        font_main = ImageFont.truetype(font_path, 40)
        font_bold = ImageFont.truetype("C:\\Windows\\Fonts\\seguisb.ttf", 45)
        font_small = ImageFont.truetype(font_path, 35)
    except:
        font_main = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        font_small = ImageFont.load_default()

    def draw_bubble(text, x, y, font, align='left', bg_color=(0, 153, 255), text_color=(255, 255, 255), padding=25):
        tw, th = get_bubble_size(draw, text, font)
        
        if align == 'center':
            actual_x = width // 2 - tw // 2
        elif align == 'right':
            actual_x = x - tw
        else:
            actual_x = x
            
        bubble_xy = [actual_x - padding, y - padding, actual_x + tw + padding, y + th + padding]
        
        # Draw rounded rectangle bubble
        try:
            draw.rounded_rectangle(bubble_xy, radius=18, fill=bg_color)
        except AttributeError:
            draw.rectangle(bubble_xy, fill=bg_color)
            
        draw.multiline_text((actual_x, y), text, font=font, fill=text_color, spacing=15)
        return bubble_xy[3] # pastga qaytish joyi y
        
    y = 50
    # Sana va Vaqt
    date_str = order_data.get('date', '')
    if ' ' in date_str:
        d, t = date_str.split(' ', 1)
        draw.multiline_text((width - 40, y), f"{d}\n{t}", font=font_small, fill=(0, 0, 0), anchor="ra", align="center")
    
    # Mijoz Bubble
    y = draw_bubble(f"Mijoz: {order_data.get('client_name')}", 0, y + 20, font_bold, align='center') + 50
    
    rooms = order_data.get('rooms', [])
    for room in rooms:
        h, w = room.get('height'), room.get('width')
        if h and w:
            y = draw_bubble(f"Xonaning razmeri Bo'yi: {h} Eni: {w}", 40, y, font_main, align='left') + 15
        
        r_name = room.get('room_name')
        if r_name:
            y = draw_bubble(f"Xonaning nomi: {r_name}", 40, y, font_main, align='left') + 40
        
        # Mahsulotlar (Katta Bubble)
        mah = "Mahsulotlar\n"
        room_text = room.get('text', '')
        # Asosiy mahsulotlarni ajratish
        lines = room_text.split('\n')
        clean_lines = []
        for l in lines[1:]: # skip title
            if l.strip() != "" and not l.startswith("Xona jami"):
                # Clean up symbols for cleaner receipt look
                l_clean = l.strip().replace("×", "x")
                clean_lines.append(l_clean)
                
        mah += "\n".join(clean_lines)
        y = draw_bubble(mah, 40, y, font_main, align='left') + 40

    # Umumiy Hisobot Va Kontaktlar
    y = draw_bubble(f"Jami summa : {format_num(order_data.get('total_summa'))} so'm", 0, y, font_bold, align='center') + 60
    
    y = draw_bubble("Tel: +998 77 340 11 41", 0, y, font_main, align='center') + 40
    y = draw_bubble("Instagram : @rayyon_pardalar", 40, y, font_main, align='left') + 20
    y = draw_bubble("Telegram : @rayyonpardalar", 40, y, font_main, align='left') + 60
    y = draw_bubble("Bizni tanlaganinggiz uchun raxmat !", 0, y, font_main, align='center') + 80
    
    # 5000 lik rasmni haqiqiy y uzuligida qirqib olish (Crop)
    img = img.crop((0, 0, width, int(y)))
    
    # Saqlash
    archive_dir = "receipts"
    os.makedirs(archive_dir, exist_ok=True)
    file_name = f"receipt_{order_data.get('client_name')}_{datetime.datetime.now().strftime('%H%M%S')}.png"
    file_path = os.path.join(archive_dir, file_name)
    img.save(file_path)
    return file_path
