import io
import base64
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# --- CONFIGURATION ---
PRINTER_WIDTH = 512  # Standard 80mm
FONT_PATH = "arial.ttf"

def _get_draw_obj():
    img = Image.new('RGB', (PRINTER_WIDTH, 2000), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        fonts = {
            'sm': ImageFont.truetype(FONT_PATH, 20),
            'md': ImageFont.truetype(FONT_PATH, 26),
            'bg': ImageFont.truetype(FONT_PATH, 34),
            'xl': ImageFont.truetype(FONT_PATH, 48),
        }
    except OSError:
        default = ImageFont.load_default()
        fonts = {'sm': default, 'md': default, 'bg': default, 'xl': default}
    return img, draw, fonts

def _draw_line(draw, y, width=2):
    draw.line((0, y, PRINTER_WIDTH, y), fill=0, width=width)
    return y + 15

def _finalize_image(img, y_pos):
    img = img.crop((0, 0, PRINTER_WIDTH, y_pos + 40))
    img = img.convert('1')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def _format_qty(qty):
    """Formats quantity: 1.0 -> 1, 1.50 -> 1.5, 1.05 -> 1.05"""
    try:
        # float to string conversion handles trailing zeros perfectly
        return str(float(qty)).rstrip('0').rstrip('.') if '.' in str(qty) else str(qty)
    except (ValueError, TypeError):
        return str(qty)

def _draw_columns(draw, y, name, qty, price, fonts):
    """Handles the specific 'Name Left | Qty Center | Price Right' alignment."""
    # 1. Name (Left)
    display_name = (name[:18] + '..') if len(name) > 20 else name
    draw.text((10, y), display_name, fill=0, font=fonts['bg'])
    
    # 2. Qty (Center - formatted using _format_qty)
    qty_str = _format_qty(qty)
    # Using 300 for center alignment
    draw.text((300, y), qty_str, fill=0, font=fonts['bg'])
    
    # 3. Price (Right-aligned finishing at x=500)
    if price is not None:
        price_str = f"{int(price):,}".replace(",", " ")
        bbox = draw.textbbox((0, 0), price_str, font=fonts['bg'])
        draw.text((500 - (bbox[2] - bbox[0]), y), price_str, fill=0, font=fonts['bg'])
    
    return y + 50

# --- INDIVIDUAL RECEIPT FUNCTIONS ---

def cashier_receipt(order_id):
    from .models import Order
    order = Order.objects.get(id=order_id)
    img, draw, fonts = _get_draw_obj()
    y = 20

    # Header
    waiter = order.user.name if order.user else "N/A"
    draw.text((10, y), f"Ofitsant: {waiter}", fill=0, font=fonts['bg'])
    y += 50
    draw.text((10, y), f"Stol: {order.table.name}, {order.table.location}", fill=0, font=fonts['md'])
    y += 40
    draw.text((10, y), f"ochilgan vaqt: {order.c_at.strftime('%d/%m/%y %H:%M')}", fill=0, font=fonts['md'])
    y += 30

    draw.text((10, y), f"yopilgan vaqt: {order.u_at.strftime('%d/%m/%y %H:%M')}", fill=0, font=fonts['md'])
    y += 30
    y = _draw_line(draw, y)

    # Column Headers
    draw.text((10, y), "Nomi", fill=0, font=fonts['sm'])
    draw.text((300, y), "Soni", fill=0, font=fonts['sm'])
    draw.text((430, y), "Narxi", fill=0, font=fonts['sm'])
    y += 30

    # Grouping and Drawing Items
    grouped_items = {}
    for item in order.order_items.all():
        n = item.menu_item.name
        if n in grouped_items:
            grouped_items[n]['qty'] += item.quantity
            grouped_items[n]['total'] += (item.quantity * item.menu_item.price)
        else:
            grouped_items[n] = {'qty': item.quantity, 'total': item.quantity * item.menu_item.price}

    for name, data in grouped_items.items():
        y = _draw_columns(draw, y, name, data['qty'], data['total'], fonts)
        draw.line((10, y, PRINTER_WIDTH-10, y), fill=0, width=1)
        y += 10

    # Totals
    y = _draw_line(draw, y)
    draw.text((10,y), f"Jami: {order.subamount}", fill=0, font=fonts['md'])
    y += 40
    draw.text((10,y), f"xizmat haqi: {order.table.commission}% = {order.amount - order.subamount}", fill=0, font=fonts['md'])
    y += 40
    y  = _draw_line(draw, y)
    total_str = f"TO'LOV: {order.amount} UZS"
    draw.text((10, y), total_str, fill=0, font=fonts['xl'])
    y += 65

    return _finalize_image(img, y)

def orderitem_receipt(order_items):
    if not order_items: return ""
    order = order_items[0].order
    img, draw, fonts = _get_draw_obj()
    y = 20

    draw.text((10, y), f"Ofitsant: {order.user.name}", fill=0, font=fonts['bg'])
    y += 50
    draw.text((10, y), f"Stol: {order.table.name}, {order.table.location}", fill=0, font=fonts['bg'])
    y += 60
    draw.text((10, y), f"vaqt: {datetime.now().strftime('%d/%m/%y %H:%M')}", fill=0, font=fonts['md'])
    y += 40
    y = _draw_line(draw, y)

    draw.text((10, y), "BUYURTMALAR:", fill=0, font=fonts['md'])
    y += 40
    y = _draw_line(draw, y)

    for item in order_items:
        y = _draw_columns(draw, y, item.menu_item.name, item.quantity, None, fonts)
        draw.line((10, y, PRINTER_WIDTH-10, y), fill=0, width=1)
        y += 10

    return _finalize_image(img, y)

def cancelled_orderitem_receipt(order_items):
    if not order_items: return ""
    order = order_items[0].order
    img, draw, fonts = _get_draw_obj()
    y = 20

    draw.text((10, y), "!!! BEKOR QILINDI !!!", fill=0, font=fonts['xl'])
    y += 70
    y = _draw_line(draw, y)
    draw.text((10, y), f"Stol: {order.table.name}, {order.table.location}", fill=0, font=fonts['bg'])
    y += 50
    draw.text((10,y), f"ofitsant: {order.user.name}", fill=0, font=fonts['bg'])
    y += 50
    draw.text((10,y), f"vaqt: {datetime.now().strftime('%d/%m/%y %H:%M')}", fill=0, font=fonts['bg'])
    y += 40
    y = _draw_line(draw, y)

    for item in order_items:
        y = _draw_columns(draw, y, item.menu_item.name, item.quantity, None, fonts)
        y += 10

    return _finalize_image(img, y)

def reduced_orderitem_receipt(order_item, reduced_quantity):
    img, draw, fonts = _get_draw_obj()
    y = 20

    draw.text((10, y), "bekor qilindi", fill=0, font=fonts['xl'])
    y += 70
    y = _draw_line(draw, y)
    draw.text((10, y), f"Stol: {order_item.order.table.name}, {order_item.order.table.location}", fill=0, font=fonts['bg'])
    y += 50
    draw.text((10,y), f"ofitsant: {order_item.order.user.name}", fill=0, font=fonts['bg'])
    y += 50
    draw.text((10,y), f"vaqt: {datetime.now().strftime('%d/%m/%y %H:%M')}", fill=0, font=fonts['bg'])
    y += 40
    y = _draw_line(draw, y)


    # Handles the negative prefix correctly for formatted quantity
    y = _draw_columns(draw, y, order_item.menu_item.name, f"-{_format_qty(reduced_quantity)}", None, fonts)
    
    return _finalize_image(img, y)