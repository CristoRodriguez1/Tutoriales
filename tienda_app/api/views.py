from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from tienda_app.infra.factories import PaymentFactory
from tienda_app.models import Libro
from tienda_app.services import CompraService

from .serializers import LibroSerializer, OrdenInputSerializer


class LibroListAPIView(ListAPIView):
    """GET /api/v1/libros/ — catálogo con stock (mismo modelo que la vista HTML de inventario)."""

    queryset = Libro.objects.select_related('inventario').order_by('id')
    serializer_class = LibroSerializer


class CompraAPIView(APIView):
    """
    Endpoint para procesar compras via JSON.
    POST /api/v1/comprar/
    Payload: {"libro_id": 1, "direccion_envio": "Calle 123", "cantidad": 1}
    """

    def get(self, request):
        # GET amigable para evidencia en navegador (tutorial 04: URL pública en AWS).
        return Response(
            {
                "servicio": "comprar",
                "instrucciones": "Enviar POST con JSON: libro_id, direccion_envio; cantidad opcional (default 1).",
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = OrdenInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        datos = serializer.validated_data

        try:
            gateway = PaymentFactory.get_processor()
            servicio = CompraService(procesador_pago=gateway)
            usuario = request.user if request.user.is_authenticated else None
            resultado = servicio.ejecutar_compra(
                libro_id=datos['libro_id'],
                cantidad=datos.get('cantidad', 1),
                direccion=datos['direccion_envio'],
                usuario=usuario,
            )

            return Response(
                {
                    'estado': 'exito',
                    'mensaje': f'Orden creada. Total: {resultado}',
                },
                status=status.HTTP_201_CREATED,
            )

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_409_CONFLICT)
        except Exception:
            return Response({'error': 'Error interno'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)