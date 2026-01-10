from datetime import datetime
from django.db.models import Sum, F

def format_receipt_text(lines):
    """Joins lines and ensures enough spacing for the manual tear or auto-cut."""
    return "\n".join(lines) + "\n\n\n\n\n"

def cashier_receipt(order_id):
    """ Generate a cashier receipt with grouped items. """
    from .models import Order 
    order = Order.objects.get(id=order_id)
    
    # --- GROUPING LOGIC ---
    # We use a dictionary to group items by their name
    grouped_items = {}
    
    for item in order.order_items.all():
        name = item.menu_item.name
        if name in grouped_items:
            grouped_items[name]['qty'] += item.quantity
            grouped_items[name]['total_price'] += (item.quantity * item.menu_item.price)
        else:
            grouped_items[name] = {
                'qty': item.quantity,
                'total_price': item.quantity * item.menu_item.price
            }

    # Header Information
    lines = [
        f"ofitsant: {order.user.name}",
        f"stol: {order.table.name}, {order.table.location} | buyurtma ID: {order.id}",
        f"ochilgan vaqt: {order.c_at.strftime('%d/%m/%y:%H:%M:%S')}",
        f"yopilgan vaqt: {datetime.now().strftime('%d/%m/%y:%H:%M:%S')}",
        "-" * 32,
        f"{'buyurtma nomi':<16}{'soni':^6}{'narxi':>10}",
        "-" * 32
    ]
    
    # Print Grouped Items
    for name, data in grouped_items.items():
        name_display = name[:15] # Truncate for alignment
        qty = str(data['qty'])
        price = f"{int(data['total_price']):,}".replace(",", " ")
        lines.append(f"{name_display:<16}{qty:^6}{price:>10}")
        
    # Totals
    subtotal = f"{int(order.subamount):,}".replace(",", " ")
    service_fee = f"{int(order.amount - order.subamount):,}".replace(",", " ")
    total = f"{int(order.amount):,}".replace(",", " ")
    
    lines.append("-" * 32)
    lines.append(f"jami: {subtotal}")
    lines.append(f"xizmat haqi: {order.table.commission}% = {service_fee}")
    lines.append("-" * 32)
    lines.append(f"To'lov summasi: {total}")
    lines.append("-" * 32)
    
    return format_receipt_text(lines)
def orderitem_receipt(order_items):
    """ Generate kitchen tickets (2nd example in screenshot). """
    if not order_items: return ""
    order = order_items[0].order
    
    lines = [
        f"ofitsant: {order.user.name}",
        f"stol: {order.table.name}, {order.table.location} | buyurtma ID: {order.id}",
        f"ochilgan vaqt: {order.c_at.strftime('%d/%m/%y:%H:%M:%S')}",
        f"yopilgan vaqt: {datetime.now().strftime('%d/%m/%y:%H:%M:%S')}",
        "-" * 32,
        "buyurtmalar:"
    ]
    
    for item in order_items:
        lines.append(f"   {item.menu_item.name:<24}{item.quantity:>4}")
        
    return format_receipt_text(lines)

def cancelled_orderitem_receipt(order_items):
    """ Generate cancelled tickets (3rd example in screenshot). """
    if not order_items: return ""
    order = order_items[0].order
    
    lines = [
        f"ofitsant: {order.user.name}",
        f"stol: {order.table.name}, {order.table.location} | buyurtma ID: {order.id}",
        f"ochilgan vaqt: {order.c_at.strftime('%d/%m/%y:%H:%M:%S')}",
        f"yopilgan vaqt: {datetime.now().strftime('%d/%m/%y:%H:%M:%S')}",
        "-" * 32,
        "bekor qilindi:",
        "-" * 32,
        "buyurtmalar:"
    ]
    
    for item in order_items:
        lines.append(f"   {item.menu_item.name:<24}{item.quantity:>4}")
        
    return format_receipt_text(lines)