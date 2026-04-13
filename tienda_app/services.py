from django.shortcuts import get_object_or_404

from .domain.builders import OrdenBuilder
from .domain.logic import CalculadorImpuestos
from .models import Inventario, Libro


class CompraService:
    """
    SERVICE LAYER: Orquesta dominio (Builder), infraestructura (procesador
    inyectado vía Factory) y persistencia.
    """

    def __init__(self, procesador_pago):
        self.procesador_pago = procesador_pago
        self.builder = OrdenBuilder()

    def obtener_detalle_producto(self, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
        return {"libro": libro, "total": total}

    def ejecutar_proceso_compra(self, usuario, lista_productos, direccion=""):
        """
        Flujo explícito tipo tutorial: Builder (lista de productos) + pasarela.
        lista_productos: secuencia de Libro (mismo libro repetido = varias unidades).
        """
        if not lista_productos:
            raise ValueError("Lista de productos vacía.")
        libro = lista_productos[0]
        if any(p.pk != libro.pk for p in lista_productos):
            raise ValueError(
                "Todos los ítems deben ser el mismo libro en este dominio."
            )
        cantidad = len(lista_productos)
        return self.ejecutar_compra(
            libro.pk, cantidad=cantidad, direccion=direccion, usuario=usuario
        )

    def ejecutar_compra(self, libro_id, cantidad=1, direccion="", usuario=None):
        libro = get_object_or_404(Libro, id=libro_id)
        inv = get_object_or_404(Inventario, libro=libro)

        if inv.cantidad < cantidad:
            raise ValueError("No hay suficiente stock para completar la compra.")

        orden = (
            self.builder
            .con_usuario(usuario)
            .con_productos([libro] * cantidad)
            .para_envio(direccion)
            .build()
        )

        pago_exitoso = self.procesador_pago.pagar(orden.total)
        if not pago_exitoso:
            orden.delete()
            raise Exception("La transacción fue rechazada por el banco.")

        inv.cantidad -= cantidad
        inv.save()

        return orden.total


class CompraRapidaService:
    """
    Service Layer para Compra Rápida: mismo patrón que CompraService
    (Builder + procesador inyectado), sin duplicar creación de Orden en la vista.
    """

    def __init__(self, procesador_pago):
        self.procesador_pago = procesador_pago
        self.builder = OrdenBuilder()

    def obtener_detalle_producto(self, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
        return {"libro": libro, "total": total}

    def procesar(self, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        inv = Inventario.objects.filter(libro=libro).first()
        if inv is None:
            raise ValueError("No hay inventario configurado para este libro.")

        if inv.cantidad <= 0:
            raise ValueError("No hay existencias.")

        orden = (
            self.builder
            .con_usuario(None)
            .con_productos([libro])
            .para_envio("")
            .build()
        )

        if not self.procesador_pago.pagar(orden.total):
            orden.delete()
            return None

        inv.cantidad -= 1
        inv.save()
        return orden.total
