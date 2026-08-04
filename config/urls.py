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

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.cars.urls")),
    # TODO(Крок 8): views.py + urls.py для products/customers/waybills/logistics
    # ще не реалізовані — розкоментувати, коли з'являться відповідні urls.py.
    # path("api/", include("apps.products.urls")),
    # path("api/", include("apps.customers.urls")),
    # path("api/", include("apps.waybills.urls")),
    # path("api/", include("apps.logistics.urls")),
]
