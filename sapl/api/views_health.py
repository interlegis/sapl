import logging
import traceback

from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from sapl.health import check_app, check_db, check_cache

COMMON_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
}


def _format_plain(ok: bool) -> HttpResponse:
    return HttpResponse("OK\n" if ok else "UNHEALTHY\n",
                        status=status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE,
                        content_type="text/plain")


class HealthzView(APIView):
    authentication_classes = []
    permission_classes = []

    logger = logging.getLogger(__name__)

    def get(self, request):
        try:
            ok, msg, ms = check_app()
            payload = {
                "status": "OK" if ok else "UNHEALTHY",
                "checks": {"app": {"ok": ok, "latency_ms": round(ms, 1), "error": msg}},
                "version": settings.SAPL_VERSION,
                "time": timezone.now().isoformat(),
            }
            if request.query_params.get("fmt") == "txt":
                return _format_plain(ok)
            return Response(payload,
                            status=status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE,
                            headers=COMMON_HEADERS)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            return "An internal error has occurred!"



class ReadyzView(APIView):
    authentication_classes = []
    permission_classes = []

    logger = logging.getLogger(__name__)

    def get(self, request):
        try:
            checks = {
                "app": check_app(),
                "db": check_db(),
                "cache": check_cache(),
            }
            payload_checks = {
                name: {"ok": r[0], "latency_ms": round(r[2], 1), "error": r[1]}
                for name, r in checks.items()
            }
            ok = all(r[0] for r in checks.values())
            payload = {
                "status": "ok" if ok else "unhealthy",
                "checks": payload_checks,
                "version": settings.SAPL_VERSION,
                "time": timezone.now().isoformat(),
            }
            if request.query_params.get("fmt") == "txt":
                return _format_plain(ok)
            return Response(payload,
                            status=status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE,
                            headers=COMMON_HEADERS)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            return "An internal error has occurred!"


class AppzVersionView(APIView):
    authentication_classes = []
    permission_classes = []

    logger = logging.getLogger(__name__)

    def get(self, request):
        try:
            payload = {
                'name': 'SAPL',
                'description': 'Sistema de Apoio ao Processo Legislativo',
                'version': settings.SAPL_VERSION,
            }
            if request.query_params.get("fmt") == "txt":
                return HttpResponse(f"{payload['version']} {payload['name']}",
                                    status=status.HTTP_200_OK,
                                    content_type="text/plain")
            return Response(payload,
                            status=status.HTTP_200_OK,
                            headers=COMMON_HEADERS)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            return "An internal error has occurred!"
