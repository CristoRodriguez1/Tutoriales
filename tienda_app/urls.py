from django.urls import path
from .api.views import CompraAPIView, LibroListAPIView
from .views import CompraRapidaView, CompraView, InventarioListView

urlpatterns = [
    # Usamos .as_view() para habilitar la CBV
    path('compra/<int:libro_id>/', CompraView.as_view(), name='finalizar_compra'),
    path('compra-rapida/<int:libro_id>/', CompraRapidaView.as_view(), name='compra_rapida'),
    path('inventario/', InventarioListView.as_view(), name='inventario_html'),
    path('api/v1/libros/', LibroListAPIView.as_view(), name='api_libros'),
    path('api/v1/comprar/', CompraAPIView.as_view(), name='api_comprar'),
]