import time
import socket
import io
import base64
from PIL import Image
from django.core.management.base import BaseCommand
from order.models import PrintJob
from escpos.printer import Network 

class Command(BaseCommand):
    help = 'Process print jobs as high-quality images'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Started Image-Based Print Worker..."))

        while True:
            pending_jobs = PrintJob.objects.filter(status='pending').order_by('c_at')

            for job in pending_jobs:
                job.refresh_from_db()
                if job.status != 'pending':
                    continue

                p = None
                try:
                    # 1. Physical Check
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    if sock.connect_ex((job.printer.ip_address, int(job.printer.port or 9100))) != 0:
                        raise ConnectionError("Printer Unreachable")
                    sock.close()

                    # 2. Decode Base64 Payload to Image
                    image_bytes = base64.b64decode(job.payload)
                    img = Image.open(io.BytesIO(image_bytes))

                    # 3. Print
                    p = Network(job.printer.ip_address, port=int(job.printer.port or 9100))
                    self.stdout.write(f"Printing Image Job {job.id}...")
                    
                    # Use bitImageRaster for better compatibility with thermal printers
                    p.image(img, impl="bitImageRaster")
                    p.cut()

                    # 4. Success Sync
                    time.sleep(1.5)
                    job.status = 'printed'
                    job.save()
                    self.stdout.write(self.style.SUCCESS(f"Job {job.id} Success"))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Print Error: {e}"))
                    break 

                finally:
                    if p:
                        try: p.device.close()
                        except: pass

            time.sleep(2)