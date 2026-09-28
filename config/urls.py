"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import hashlib
import io

from django.conf import settings
from django.contrib import admin
from django.core.management import call_command
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.urls import include, path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsManagerOrHead

# ОДНОРАЗОВИЙ локальний бекап прод-БД (2026-09-28) — видалити разом з
# усіма новими імпортами вище одразу після використання.
# export_backup_token_view (сесія + IsManagerOrHead) віддає похідний від
# уже наявного SECRET_KEY токен — жодного нового секрету в коді немає;
# export_backup_view (без сесії, для простого `curl`) перевіряє той самий
# похідний токен у query-параметрі.


def _backup_token() -> str:
    return hashlib.sha256(settings.SECRET_KEY.encode()).hexdigest()


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsManagerOrHead])
def export_backup_token_view(request):
    return JsonResponse({"token": _backup_token()})


def export_backup_view(request):
    if request.GET.get("token") != _backup_token():
        return HttpResponseForbidden()
    buffer = io.StringIO()
    call_command(
        "dumpdata",
        exclude=["contenttypes", "auth.permission", "admin.logentry", "sessions.session"],
        indent=2,
        stdout=buffer,
    )
    return HttpResponse(buffer.getvalue(), content_type="application/json")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.cars.urls")),
    path("api/", include("apps.products.urls")),
    path("api/", include("apps.customers.urls")),
    path("api/", include("apps.waybills.urls")),
    path("api/", include("apps.logistics.urls")),
    path("api/system/export-backup-token/", export_backup_token_view),
    path("api/system/export-backup/", export_backup_view),
]
