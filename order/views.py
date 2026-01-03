import logging
import socket
from django.conf import settings
import io
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets, permissions, pagination
from rest_framework.exceptions import PermissionDenied
from .models import Order, MenuItem, OrderItem, Reservations
from .filters import OrderFilter
from .serializers import (
    OrderSerializer,
    MenuItemSerializer,
    OrderItemSerializer,
    ReservationsSerializer,
)
from drf_yasg.utils import swagger_auto_schema

# Lazy import Pillow when raster printing is used
def _import_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont
        return Image, ImageDraw, ImageFont
    except Exception:
        return None, None, None

logger = logging.getLogger(__name__)
def generate_kitchen_ticket_for_items(items):
    # ESC/POS bold sequences for kitchen tickets
    BOLD_ON = '\x1bE\x01'
    BOLD_OFF = '\x1bE\x00'

    # Group items by their order so we print one header per order
    orders = {}
    for item in items:
        orders.setdefault(item.order_id, {
            # We'll reload the order from DB with related fields to ensure user/table are present
            'order': None,
            'items': []
        })['items'].append(item)

    from .models import Order as OrderModel

    ticket_lines = []
    for order_id, data in list(orders.items()):
        # reload order with related user and table to ensure relations are available
        try:
            order = OrderModel.objects.select_related('user', 'table').get(pk=order_id)
        except OrderModel.DoesNotExist:
            logger.warning(f"Order {order_id} referenced by OrderItem not found")
            continue
        data['order'] = order
        order_items = data['items']
        # Table model uses `name` and `location` fields
        table_number = getattr(order.table, 'name', order.table_id)
        table_location = getattr(order.table, 'location', '')
        order_time = order.u_at.strftime('%Y-%m-%d %H:%M:%S')
        # Debug: log user_id and resolved user object to investigate missing user
        try:
            logger.debug(f"Order {order.pk} user_id={order.user_id} user_attr_present={getattr(order, 'user', None) is not None}")
            # If user_id exists, do a DB lookup for clarity
            if order.user_id:
                from django.contrib.auth import get_user_model
                U = get_user_model()
                try:
                    user_row = U.objects.filter(pk=order.user_id).values('pk', 'username', 'name').first()
                    logger.debug(f"User lookup for id={order.user_id}: {user_row}")
                except Exception as e:
                    logger.exception(f"Error fetching user {order.user_id} from DB: {e}")
        except Exception:
            logger.debug(f"Order {order.pk} has no user attribute or user is None")

        user = getattr(order.user, 'username', str(order.user))
        
        ticket_lines.append(f"vaqt : {order_time}")
        # Include location if present: "stol: 25, naves"
        stol_line = f"stol: {table_number}"
        if table_location:
            stol_line += f", {table_location}"
        ticket_lines.append(stol_line)
        ticket_lines.append(f"buyurtma : {order.id}")
        ticket_lines.append(f"ishchi : {user}")
        ticket_lines.append("")
        ticket_lines.append("buyurtma(lar):")
        for it in order_items:
            ticket_lines.append(f"  - {BOLD_ON}{it.menu_item.name} x {it.quantity}{BOLD_OFF}")
        ticket_lines.append("\n\n\n\n")

    ticket = "\n" + "\n".join(ticket_lines)
    logger.info(ticket)

    # Send the ticket to the network printer (raw TCP, typically port 9100)
    printer_ip = getattr(settings, 'PRINTER_IP', '192.168.100.51')
    printer_port = getattr(settings, 'PRINTER_PORT', 9100)
    try:
        # Use ESC/POS: initialize printer, send text, then feed and cut.
        # Xprinter 80mm typically accepts ESC/POS on raw TCP (port 9100).
        encoding = getattr(settings, 'PRINTER_ENCODING', 'utf-8')
        # ESC @ initializes the printer
        init_bytes = b"\x1b@"
        # Feed a few lines and full cut (GS V 0) - common cut sequence; may vary by model
        cut_bytes = b"\n\n\n" + b"\x1dV\x00"

        # Apply text size mapping: normal | wide | tall | double
        size_setting = getattr(settings, 'PRINTER_TEXT_SIZE', 'normal')
        _size_map = {
            'normal': b"",
            'wide': b"\x1d\x21\x10",   # double width
            'tall': b"\x1d\x21\x01",   # double height
            'double': b"\x1d\x21\x11", # double width & height
        }
        size_bytes = _size_map.get(size_setting, b"")
        size_reset = b"\x1d\x21\x00" if size_bytes else b""

        payload = init_bytes + size_bytes + ticket.encode(encoding, errors='replace') + size_reset + cut_bytes

        # Use a short timeout to avoid blocking request handling
        with socket.create_connection((printer_ip, printer_port), timeout=5) as s:
            s.sendall(payload)

        logger.info(f"Sent ESC/POS ticket to printer {printer_ip}:{printer_port}")
    except Exception as e:
        logger.exception(f"Failed sending ESC/POS ticket to printer {printer_ip}:{printer_port}: {e}")


def generate_item_removal_receipt(order, removed_items):
    """Generate and send a receipt when order items are removed or reduced.
    
    Args:
        order: Order object
        removed_items: List of dicts with keys: 'name', 'removed_qty', 'price' (per unit)
               Example: [{'name': 'Shurbo', 'removed_qty': 2, 'price': Decimal('5000')}]
    """
    from decimal import Decimal
    
    # ESC/POS inline control sequences
    BOLD_ON = '\x1bE\x01'
    BOLD_OFF = '\x1bE\x00'
    SIZE_TALL = '\x1d\x21\x01'
    SIZE_RESET = '\x1d\x21\x00'
    
    if not removed_items:
        logger.warning("generate_item_removal_receipt called with empty removed_items list")
        return
    
    try:
        # reload order with related user and table
        order = Order.objects.select_related('user', 'table').get(pk=order.pk)
    except Exception:
        pass
    
    restaurant = getattr(settings, 'RESTAURANT_NAME', 'Akramjon-ustoz')
    order_time = order.u_at.strftime('%d.%m.%Y %H:%M')
    table_name = getattr(order.table, 'name', order.table_id)
    user = None
    if getattr(order, 'user', None):
        user = getattr(order.user, 'username', None) or getattr(order.user, 'name', None) or str(order.user)
    
    lines = []
    esc_lines = []
    
    # Header
    hdrs = [
        '*' * 42,
        f"{restaurant}",
        '',
        f"OLIB TASHLASH RAQAMI",
        f"Sana: {order_time}".ljust(24) + f"  Buyurtma № {order.id}",
        f"Stol: {table_name}",
        f"Ofitsiant: {user}",
    ]
    for ln in hdrs:
        lines.append(ln)
        esc_lines.append(BOLD_ON + ln + BOLD_OFF)
    
    sep = '-' * 42
    lines.append(sep)
    esc_lines.append(BOLD_ON + sep + BOLD_OFF)
    
    # Removed items header
    header_line = f"{'Nomi':<24} {'Soni':>8} {'Summasi':>10}"
    lines.append(header_line)
    esc_lines.append(BOLD_ON + header_line + BOLD_OFF)
    
    lines.append(sep)
    esc_lines.append(BOLD_ON + sep + BOLD_OFF)
    
    total_removed_amount = Decimal('0.00')
    
    # Removed items
    for item in removed_items:
        name = item.get('name', 'Unknown Item')
        removed_qty = item.get('removed_qty', 0)
        price = item.get('price', Decimal('0.00'))
        item_total = Decimal(str(price)) * Decimal(str(removed_qty))
        total_removed_amount += item_total
        
        name_part = name[:24].ljust(24)
        qty_part = str(removed_qty).rjust(8)
        amt_part = f"{int(item_total):,}".rjust(10)
        
        plain_line = f"{name_part} {qty_part} {amt_part}"
        esc_line = BOLD_ON + name_part + qty_part + BOLD_OFF + " " + SIZE_TALL + amt_part + SIZE_RESET
        
        lines.append(plain_line)
        esc_lines.append(esc_line)
    
    lines.append(sep)
    esc_lines.append(BOLD_ON + sep + BOLD_OFF)
    
    # Total removed amount
    total_plain = f"Jami o'lib tashlash:".ljust(24) + f"{int(total_removed_amount):,}".rjust(18)
    total_esc = BOLD_ON + SIZE_TALL + f"Jami o'lib tashlash:".ljust(24) + f"{int(total_removed_amount):,}".rjust(18) + SIZE_RESET + BOLD_OFF
    
    lines.append(total_plain)
    esc_lines.append(total_esc)
    lines.append('-' * 42)
    esc_lines.append(BOLD_ON + '-' * 42 + BOLD_OFF)
    
    ticket_plain = "\n" + "\n".join(lines) + "\n\n\n"
    ticket_esc = "\n" + "\n".join(esc_lines) + "\n\n\n"
    
    # Send to printer
    printer_ip = getattr(settings, 'PRINTER_IP', '192.168.100.51')
    printer_port = getattr(settings, 'PRINTER_PORT', 9100)
    encoding = getattr(settings, 'PRINTER_ENCODING', 'utf-8')
    
    try:
        with socket.create_connection((printer_ip, printer_port), timeout=10) as s:
            s.sendall(b"\x1b@")  # initialize
            s.sendall(ticket_esc.encode(encoding))
            s.sendall(b"\n\n\n" + b"\x1dV\x00")  # cut
        logger.info(f"Sent item removal receipt to printer {printer_ip}:{printer_port} for Order {order.pk}")
    except Exception as e:
        logger.exception(f"Failed to send item removal receipt to printer {printer_ip}:{printer_port}: {e}")


def generate_cashier_receipt(order):
    """Generate and send a full cashier receipt for a single Order."""
    from decimal import Decimal
    # reload order with related items, user, table to ensure fresh data
    try:
        order = Order.objects.select_related('user', 'table').prefetch_related('order_items__menu_item').get(pk=order.pk)
    except Exception:
        # fallback to given order
        pass

    # ESC/POS inline control sequences used for text-mode receipts
    SIZE_TALL = '\x1d\x21\x01'
    SIZE_RESET = '\x1d\x21\x00'
    BOLD_ON = '\x1bE\x01'
    BOLD_OFF = '\x1bE\x00'

    # helper to format columns for monospaced receipt
    def fmt_item_line(name, qty, amount, line_width=42):
        # reserve columns: name (left), qty (center/right), amount (right)
        amt_s = f"{amount:,.0f}" if isinstance(amount, (int,)) else f"{amount:.2f}"
        qty_s = str(qty)
        # allocate spaces
        amt_w = 12
        qty_w = 8
        name_w = max(0, line_width - amt_w - qty_w - 2)
        name_part = (name[:name_w]).ljust(name_w)
        qty_part = qty_s.rjust(qty_w)
        amt_part = amt_s.rjust(amt_w)
        plain = f"{name_part} {qty_part} {amt_part}"
        # esc version: name/qty bold; amount tall (not bold)
        esc = BOLD_ON + f"{name_part} {qty_part} "  + amt_part + BOLD_OFF
        return plain, esc

    from decimal import ROUND_HALF_UP
    subtotal = Decimal('0.00')
    lines = []
    esc_lines = []

    restaurant = getattr(settings, 'RESTAURANT_NAME', 'Akramjon-ustoz')
    order_time = order.u_at.strftime('%d.%m.%Y %H:%M')
    table_name = getattr(order.table, 'name', order.table_id)
    table_loc = getattr(order.table, 'location', '')
    user = None
    if getattr(order, 'user', None):
        user = getattr(order.user, 'username', None) or getattr(order.user, 'name', None) or str(order.user)

    # header (stars + name)
    hdrs = [
        '*' * 42,
        f"{restaurant}  -  {restaurant}",
        '',
        "",
        f"Sana: {order_time}".ljust(24) + f"  Buyurtma № {order.id}",
        f"Stol: {table_name}",
        f"Ofitsiant: {user}",
        f"Zal: {table_loc}  Stol: {table_name} ",
    ]
    for ln in hdrs:
        lines.append(ln)
        esc_lines.append(BOLD_ON + ln + BOLD_OFF)
    sep = '-' * 42
    header_cols = 'Nomi'.ljust(24) + 'Soni'.rjust(8) + 'Summasi'.rjust(10)
    lines.append(sep)
    esc_lines.append(BOLD_ON + sep + BOLD_OFF)
    lines.append(header_cols)
    esc_lines.append(BOLD_ON + header_cols + BOLD_OFF)
    lines.append(sep)
    esc_lines.append(BOLD_ON + sep + BOLD_OFF)

    for it in order.order_items.all():
        price = getattr(it.menu_item, 'price', Decimal('0.00'))
        qty = it.quantity
        line_total = (Decimal(price) * Decimal(str(qty))).quantize(Decimal('1.'), rounding=ROUND_HALF_UP) if price == price.to_integral_value() else (Decimal(price) * Decimal(str(qty))).quantize(Decimal('0.01'))
        subtotal += line_total
        plain_line, esc_line = fmt_item_line(it.menu_item.name, qty, line_total)
        lines.append(plain_line)
        esc_lines.append(esc_line)  

    lines.append(sep)
    esc_lines.append(BOLD_ON + sep + BOLD_OFF)

    commission_pct = getattr(getattr(order, 'table', None), 'commission', None)
    amount = getattr(order, 'amount', None)
    if amount is None:
        amount = subtotal
    commission_amount = (amount - subtotal).quantize(Decimal('0.01')) if amount and subtotal else Decimal('0.00')

    tot_plain = f"To'liq summa:".ljust(24) + f"{int(subtotal):,}".rjust(18)
    tot_esc = BOLD_ON + f"To'liq summa:".ljust(24) + SIZE_TALL + f"{int(subtotal):,}".rjust(18) + SIZE_RESET + BOLD_OFF
    lines.append(tot_plain)
    esc_lines.append(tot_esc)
    
    if commission_pct is not None:
        lines.append(f"(Xizmat {commission_pct}%): +{int(commission_amount):,}")
        esc_lines.append(BOLD_ON + f"(Xizmat {commission_pct}%): +{int(commission_amount):,}" + BOLD_OFF)
    lines.append('')
    lines.append('')
    esc_lines.append('')
    esc_lines.append('')
    jam_plain = f"JAMI TO'LOV:".ljust(24) + f"{int(amount):,}".rjust(18)
    jam_esc = BOLD_ON + SIZE_TALL + f"JAMI TO'LOV:".ljust(24) + f"{int(amount):,}".rjust(18) + SIZE_RESET + BOLD_OFF
    lines.append(jam_plain)
    esc_lines.append(jam_esc)
    lines.append('-' * 42)

    ticket_plain = "\n" + "\n".join(lines) + "\n\n\n"
    ticket_esc = "\n" + "\n".join(esc_lines) + "\n\n\n"
    # send to printer using either raster or text ESC/POS
    printer_ip = getattr(settings, 'PRINTER_IP', '192.168.100.51')
    printer_port = getattr(settings, 'PRINTER_PORT', 9100)
    encoding = getattr(settings, 'PRINTER_ENCODING', 'utf-8')

    # If raster printing is enabled, render ticket to image at PRINTER_SCALE and send as ESC/POS raster
    if getattr(settings, 'PRINTER_USE_RASTER', False):
        Image, ImageDraw, ImageFont = _import_pillow()
        if Image is None:
            logger.error('Pillow is not available but PRINTER_USE_RASTER is True. Install Pillow.')
        else:
            try:
                scale = float(getattr(settings, 'PRINTER_SCALE', 1.2))
                base_width = int(getattr(settings, 'PRINTER_RASTER_WIDTH', 576))
                width = max(128, int(base_width * scale))

                # choose font
                font_size = max(10, int(22 * scale))
                try:
                    font = ImageFont.truetype('DejaVuSansMono.ttf', font_size)
                except Exception:
                    font = ImageFont.load_default()

                # render text lines
                lines_text = ticket_plain.split('\n')
                # estimate height
                dummy_img = Image.new('L', (width, 10), 255)
                draw = ImageDraw.Draw(dummy_img)
                line_h = draw.textsize('A', font=font)[1] + 2
                img_h = line_h * (len(lines_text) + 2)
                img = Image.new('L', (width, img_h), 255)
                draw = ImageDraw.Draw(img)
                y = 0
                for ln in lines_text:
                    draw.text((0, y), ln, font=font, fill=0)
                    y += line_h

                # convert to 1-bit
                bw = img.convert('1')

                # send raster
                try:
                    _send_escpos_raster(printer_ip, printer_port, bw)
                    logger.info(f"Sent raster cashier receipt to printer {printer_ip}:{printer_port} for Order {order.pk}")
                    return
                except Exception as e:
                    logger.exception(f"Failed sending raster receipt: {e}")
            except Exception as e:
                logger.exception(f"Error preparing raster receipt: {e}")

    # Fallback to text-mode ESC/POS
    init_bytes = b"\x1b@"
    cut_bytes = b"\n\n\n" + b"\x1dV\x00"
    # Apply text size mapping: normal | wide | tall | double
    size_setting = getattr(settings, 'PRINTER_TEXT_SIZE', 'normal')
    _size_map = {
        'normal': b"",
        'wide': b"\x1d\x21\x10",
        'tall': b"\x1d\x21\x01",
        'double': b"\x1d\x21\x11",
    }
    size_bytes = _size_map.get(size_setting, b"")
    size_reset = b"\x1d\x21\x00" if size_bytes else b""
    try:
        payload = init_bytes + size_bytes + ticket_esc.encode(encoding, errors='replace') + size_reset + cut_bytes
        with socket.create_connection((printer_ip, printer_port), timeout=5) as s:
            s.sendall(payload)
        logger.info(f"Sent cashier receipt to printer {printer_ip}:{printer_port} for Order {order.pk}")
    except Exception as e:
        logger.exception(f"Failed to send cashier receipt to printer {printer_ip}:{printer_port} for Order {order.pk}: {e}")


def _send_escpos_raster(printer_ip, printer_port, pil_image):
    """Send a Pillow 1-bit image to the printer using ESC/POS raster graphics (GS v 0).

    pil_image must be mode '1' (1-bit) with width multiple of 8 or will be padded.
    """
    try:
        from PIL import Image as _PIL_Image
    except Exception:
        _PIL_Image = None

    # ensure mode
    if pil_image.mode != '1':
        pil_image = pil_image.convert('1')

    width, height = pil_image.size
    # pad width to multiple of 8
    pad = (8 - (width % 8)) % 8
    if pad:
        new_width = width + pad
        if _PIL_Image is None:
            raise RuntimeError('Pillow is required for raster printing')
        new_img = _PIL_Image.new('1', (new_width, height), 1)
        new_img.paste(pil_image, (0, 0))
        pil_image = new_img
        width = new_width

    # width in bytes
    width_bytes = width // 8

    # get bitmap data left-to-right, top-to-bottom, most significant bit = left pixel
    data = bytearray()
    pixels = pil_image.load()
    for y in range(height):
        for xb in range(width_bytes):
            byte = 0
            for bit in range(8):
                x = xb * 8 + bit
                pixel = pixels[x, y]
                # in mode '1', pixel is 0 for black, 255 for white -> invert
                if pixel == 0:
                    byte |= (0x80 >> bit)
            data.append(byte)

    # GS v 0: b'\x1d\x76\x30' + m + xL + xH + yL + yH + data
    m = 0
    xL = width_bytes & 0xFF
    xH = (width_bytes >> 8) & 0xFF
    yL = height & 0xFF
    yH = (height >> 8) & 0xFF
    header = b"\x1d\x76\x30" + bytes([m, xL, xH, yL, yH])

    payload = header + bytes(data)

    # send via TCP
    with socket.create_connection((printer_ip, printer_port), timeout=10) as s:
        # initialize
        s.sendall(b"\x1b@")
        s.sendall(payload)
        # cut
        s.sendall(b"\n\n\n" + b"\x1dV\x00")

class OrderPagination(pagination.PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 100

@swagger_auto_schema(tags=['Orders'])
class OrderViewSet(viewsets.ModelViewSet):
    """ API endpoint for Orders """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    pagination_class = OrderPagination
    filterset_fields = ['order_status']
    filterset_class = OrderFilter
    def get_queryset(self):
        """Filter orders for the current user (waiter) or allow filtering by table location and user for others."""
        user = self.request.user
        queryset = Order.objects.all()
        try:
            if hasattr(user, 'role') and user.role == "waiter":
                queryset = queryset.filter(user=user)
            else:
                table_locations = self.request.query_params.getlist('table__location')
                user_ids = self.request.query_params.getlist('user')
                statuses = self.request.query_params.getlist('order_status')
                # Support comma-separated values as fallback
                if len(statuses) == 1 and ',' in statuses[0]:
                    statuses = [s.strip() for s in statuses[0].split(',') if s.strip()]
                if len(table_locations) == 1 and ',' in table_locations[0]:
                    table_locations = [l.strip() for l in table_locations[0].split(',') if l.strip()]
                if len(user_ids) == 1 and ',' in user_ids[0]:
                    user_ids = [u.strip() for u in user_ids[0].split(',') if u.strip()]
                print("table__location from params:", table_locations)
                print("user from params:", user_ids)
                print("order_status from params:", statuses)
                if table_locations:
                    queryset = queryset.filter(table__location__in=table_locations)
                if user_ids:
                    queryset = queryset.filter(user_id__in=user_ids)
                if statuses:
                    queryset = queryset.filter(order_status__in=statuses)
            return queryset.order_by('-c_at')
        except PermissionDenied:
            logger.warning("Unauthenticated user tried to access order list.")
            return Order.objects.none()

    def perform_create(self, serializer):
        """ Associate the order with the logged-in user. """
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        order = self.get_object()
        if order.order_status == "completed" or order.order_status == "pending":
            logger.info(f"Cheque receipt for order {order.id} generated.")
            try:
                generate_cashier_receipt(order)
            except Exception:
                logger.exception(f"Failed generating cashier receipt for order {order.id}")
        return response

@swagger_auto_schema(tags=['MenuItems'])
class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all().order_by('category', 'name')
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticated]

@swagger_auto_schema(tags=['OrderItems'])
class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = OrderPagination
    
    def get_queryset(self):
        """ Filter order items based on the user who owns the parent order. """
        user = self.request.user
        try:
            if user.is_staff:
                return OrderItem.objects.all()
            return OrderItem.objects.filter(order__user=user)
        except PermissionDenied:
            logger.warning("Unauthenticated user tried to access order item list.")
            return OrderItem.objects.none()

    def create(self, request, *args, **kwargs):
        is_many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=is_many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        created_items = serializer.instance if is_many else [serializer.instance]
        generate_kitchen_ticket_for_items(created_items)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        """Handle item update (quantity reduction). Print removal receipt if quantity decreased."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Store original quantity before update
        original_quantity = instance.quantity
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Check if quantity was reduced
        new_quantity = instance.quantity
        if new_quantity < original_quantity:
            reduced_qty = original_quantity - new_quantity
            order = instance.order
            removed_items = [{
                'name': instance.menu_item.name,
                'removed_qty': reduced_qty,
                'price': instance.menu_item.price
            }]
            try:
                generate_item_removal_receipt(order, removed_items)
            except Exception as e:
                logger.exception(f"Failed to print removal receipt for OrderItem {instance.pk}: {e}")
        
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Handle item deletion. Print removal receipt with the deleted item."""
        instance = self.get_object()
        order = instance.order
        removed_items = [{
            'name': instance.menu_item.name,
            'removed_qty': instance.quantity,
            'price': instance.menu_item.price
        }]
        
        # Delete the item
        self.perform_destroy(instance)
        
        # Print removal receipt after deletion
        try:
            generate_item_removal_receipt(order, removed_items)
        except Exception as e:
            logger.exception(f"Failed to print removal receipt after deleting OrderItem: {e}")
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()

@swagger_auto_schema(tags=['Reservations'])
class ReservationsViewSet(viewsets.ModelViewSet):
    """ API endpoint for Reservations """
    queryset = Reservations.objects.all().order_by('-reservation_time')
    serializer_class = ReservationsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """ Filter reservations for the current user unless they are staff. """
        user = self.request.user
        try:
            queryset = Reservations.objects.all()
            if not user.is_staff:
                queryset = queryset.filter(user=user)
            return queryset.order_by('-reservation_time')
        except PermissionDenied:
            logger.warning("Unauthenticated user tried to access reservation list.")
            return Reservations.objects.none()

    def perform_create(self, serializer):
        """ Associate the reservation with the logged-in user. """
        serializer.save(user=self.request.user)
