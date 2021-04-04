from enum import Enum


class OrderStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    CANCELLED = "cancelled"
    ON_WAY = "on_it's_way"
    WAITING_FOR_DELIVERY = "waiting_for_delivery"


class SagaStatus(Enum):
    PENDING = "pending"
    DONE = "done"
    WAITING = "waiting"


class RoutingKey(Enum):
    ORDER_CHECK = "check.order.availability"
    DELIVERY_CHECK = "check.delivery.availability"
