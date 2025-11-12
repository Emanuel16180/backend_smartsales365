from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # APIs por app
    path('api/users/', include('apps.users.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/sales/', include('apps.sales.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/ai/', include('apps.ai.urls')),

    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/catalog/', include('apps.products.urls')),
    path('api/v1/sales/', include('apps.sales.urls')),
    path('api/v1/ai/', include('apps.ai.urls')),
    path('api/v1/reports/', include('apps.reports.urls')),
]
