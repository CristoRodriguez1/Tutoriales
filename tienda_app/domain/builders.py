from decimal import Decimal

from .logic import CalculadorImpuestos
from ..models import Orden


class OrdenBuilder:
    """
    Patrón Builder: construye una Orden paso a paso (fluent interface).
    Encapsula totales con IVA y validaciones; la vista no arma el modelo a mano.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self._usuario = None
        self._libro = None
        self._cantidad = 1
        self._direccion = ""

    def con_usuario(self, usuario):
        self._usuario = usuario
        return self

    def con_libro(self, libro):
        self._libro = libro
        return self

    def con_productos(self, productos):
        """
        Variante al estilo del tutorial (lista de ítems con .precio).
        En este dominio cada orden tiene un solo título de libro; la lista puede
        repetir el mismo Libro para representar varias unidades.
        """
        items = list(productos)
        if not items:
            raise ValueError("Datos insuficientes para crear la orden.")
        first = items[0]
        if any(getattr(p, "pk", None) != first.pk for p in items):
            raise ValueError(
                "Varios libros distintos en la misma orden no están soportados; "
                "una orden = un libro (use varias unidades repitiendo el mismo ítem)."
            )
        self._libro = first
        self._cantidad = len(items)
        return self

    def con_cantidad(self, cantidad):
        self._cantidad = cantidad
        return self

    def para_envio(self, direccion):
        self._direccion = direccion
        return self

    def build(self) -> Orden:
        if not self._libro:
            raise ValueError("Datos insuficientes para crear la orden.")

        total_unitario = CalculadorImpuestos.obtener_total_con_iva(self._libro.precio)
        total = Decimal(str(total_unitario)) * self._cantidad

        orden = Orden.objects.create(
            usuario=self._usuario,
            libro=self._libro,
            total=total,
            direccion_envio=self._direccion,
        )
        self.reset()
        return orden
