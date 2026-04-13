from django.shortcuts import render
from django.http import HttpResponse
from django.views import View

from .infra.factories import PaymentFactory
from .models import Libro
from .services import CompraRapidaService, CompraService


class CompraView(View):
    """
    CBV: Vista Basada en Clases.
    Actúa como un "Portero": recibe la petición y delega al servicio.
    """

    template_name = 'tienda_app/compra.html'

    def setup_service(self):
        gateway = PaymentFactory.get_processor()
        return CompraService(procesador_pago=gateway)

    def get(self, request, libro_id):
        servicio = self.setup_service()
        contexto = servicio.obtener_detalle_producto(libro_id)
        return render(request, self.template_name, contexto)

    def post(self, request, libro_id):
        servicio = self.setup_service()
        try:
            total = servicio.ejecutar_compra(libro_id, cantidad=1)
            return render(
                request,
                self.template_name,
                {
                    'mensaje_exito': f"¡Gracias por su compra! Total: ${total}",
                    'total': total,
                },
            )
        except (ValueError, Exception) as e:
            return render(request, self.template_name, {'error': str(e)}, status=400)


class CompraRapidaView(View):
    """
    Paso 3: la vista delega en el Service Layer.
    """

    template_name = 'tienda_app/compra_rapida.html'

    def setup_service(self):
        gateway = PaymentFactory.get_processor()
        return CompraRapidaService(procesador_pago=gateway)

    def get(self, request, libro_id):
        servicio = self.setup_service()
        contexto = servicio.obtener_detalle_producto(libro_id)
        return render(request, self.template_name, contexto)

    def post(self, request, libro_id):
        servicio = self.setup_service()
        try:
            total = servicio.procesar(libro_id)
            if total is None:
                return HttpResponse("Error en el pago.", status=400)
            return HttpResponse(f"Comprado via Service Layer. Total: ${total}")
        except ValueError as e:
            return HttpResponse(str(e), status=400)


class InventarioListView(View):
    """
    Vista HTML de inventario (evidencia tutorial 3: mismo stock que descuenta la API).
    """

    template_name = 'tienda_app/inventario.html'

    def get(self, request):
        rows = []
        for libro in Libro.objects.select_related('inventario').order_by('id'):
            inv = getattr(libro, 'inventario', None)
            rows.append({'libro': libro, 'stock': inv.cantidad if inv else 0})
        return render(request, self.template_name, {'rows': rows})
