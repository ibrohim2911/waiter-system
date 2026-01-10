import time
from django.core.management.base import BaseCommand
from order.models import PrintJob, Printer 
from escpos.printer import Network 

class Command(BaseCommand):
    help = 'Process print jobs queue'

    def handle(self, *args, **options):
        self.stdout.write("Started Print Worker...")

        while True:
            # Get pending jobs (FIFO)
            pending_jobs = PrintJob.objects.filter(status='pending').order_by('c_at')

            for job in pending_jobs:
                # Refresh from DB to ensure it wasn't cancelled while we were waiting
                job.refresh_from_db()
                if job.status == 'cancelled':
                    continue

                try:
                    self.stdout.write(f"Printing Job {job.id} on {job.printer.ip_address}...")
                    
                    # --- CONNECTION ---
                    # Timeout is low (5s) so we don't block the loop for too long
                    p = Network(job.printer.ip_address, port=job.printer.port or 9100)
                    
                    # --- PRINTING ---
                    # Using CP866 or similar for Cyrillic/Uzbek characters if needed
                    # p.codepage = 'cp866' 
                    
                    p.text(job.payload.encode('utf-8').decode('utf-8'))
                    p.cut(mode='FULL', feed=True)
                    
                    # --- SUCCESS ---
                    job.status = 'printed'
                    job.save()
                    self.stdout.write(self.style.SUCCESS(f"Job {job.id} Success"))

                except Exception as e:
                    # --- FAILURE ---
                    # We do NOT mark as 'failed' permanently, we leave as 'pending'
                    # so it retries when printer comes back online.
                    self.stdout.write(self.style.ERROR(f"Printer Offline: {e}"))
                    
                    # Optional: Store error message
                    job.error_message = str(e)
                    job.save()
                    
                    # Break the inner loop to wait before retrying (prevents CPU spam)
                    break 

            # Sleep 5 seconds before checking for new jobs again
            time.sleep(5)