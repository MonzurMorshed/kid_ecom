from django.urls import path
from custom_admin.views import revenue_chart_data  # ✅ 'apps.' ছাড়া direct import

app_name = 'api'

urlpatterns = [
    path('revenue-chart/', revenue_chart_data, name='revenue_chart_data'),
]