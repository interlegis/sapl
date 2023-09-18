import json
import logging

from django.core.management.base import BaseCommand
from sapl.base.models import AuditLog

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, **options):
        print("Backfilling AuditLog JSON Field...")
        logs = AuditLog.objects.filter(data__isnull=True)
        error_counter = 0
        if logs:
            update_list = []
            for log in logs:
                try:
                    obj = log.object[1:-1] \
                        if log.object.startswith('[') else log.object
                    data = json.loads(obj)
                    log.data = data
                except Exception as e:
                    error_counter += 1
                    logging.error(e)
                    log.data = None
                else:
                    update_list.append(log)
                if len(update_list) == 1000:
                    AuditLog.objects.bulk_update(update_list, ['data'])
                    update_list = []
            if update_list:
                AuditLog.objects.bulk_update(update_list, ['data'])
        print(f"Logs backfilled: {len(logs) - error_counter}")
        print(f"Logs with errors: {error_counter}")
        print("Finished backfilling")


