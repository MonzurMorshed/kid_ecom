from django.urls import path
from . import views

urlpatterns = [
    path('orders/',                                    views.order_list,            name='order_list'),
    path('orders/<int:pk>/',                           views.order_detail,          name='order_detail'),
    path('orders/<int:pk>/update/',                    views.order_update,          name='order_update'),
    path('orders/<int:pk>/cancel/',                    views.order_cancel,          name='order_cancel'),
    path('orders/<int:pk>/delete/',                    views.order_soft_delete,     name='order_delete'),
    path('orders/<int:pk>/restore/',                   views.order_restore,         name='order_restore'),
    path('orders/<int:pk>/permanent-delete/',          views.order_permanent_delete,name='order_permanent_delete'),
    path('orders/<int:pk>/invoice/',                   views.order_invoice,         name='order_invoice'),
    path('orders/trash/',                              views.order_trash,           name='order_trash'),
    path('orders/export/',                             views.order_export,          name='order_export'),
    path('orders/import/',                             views.order_import,          name='order_import'),
    path('orders/sample-csv/',                         views.order_sample_csv,      name='order_sample_csv'),
]