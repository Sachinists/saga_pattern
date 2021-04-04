import json

from .constants import OrderStatus, SagaStatus, RoutingKey
from .order import Order
from .rabbit import RabbitClient


class SagaOrchestrator(object):
    """
        checks availability with restaurant
            -   pending (publish is yet to happen) (scenario when we received the BLOCKED connection callback)
            -   waiting (restaurant is yet to accept and send reply)
            -   done
        delivery
            -   pending (publish is yet to happen) (scenario when we received the BLOCKED connection callback)
            -   waiting (delivery is yet to accept and reply)
            -   done
    """

    @classmethod
    def begin_saga(cls, order_details):
        """checks restaurant -> payment interface"""
        print(f"Saga Begins for order id: {order_details['order_id']}", flush=True)
        if not RabbitClient.get_rabbit_connection_status():
            Order.update_saga_props(order_details["order_id"], 1, SagaStatus.WAITING.value)
            order_details = Order.remove_keys(order_details, ["saga_stage", "saga_stage_status", "status"])
            RabbitClient.publish_message(json.dumps(order_details), "restaurant_queue", RoutingKey.ORDER_CHECK.value)
        else:
            print(f"rabbit connection is blocked, please try again later")
            Order.update_saga_props(order_details["order_id"], 1, SagaStatus.PENDING.value)

    @classmethod
    def received_saga_message(cls, message):
        """Main orchestrator must atomically consume replies, update its state, and send command messages."""
        try:
            order_id = message["order_id"]
            if message["reply_from"] == "restaurant_service":
                # This must be done in transaction
                restaurant_status = message["restaurant_status"]
                if restaurant_status == "accepted":
                    cls.order_accepted_by_restaurant(order_id)
                else:
                    cls.order_rejected_by_restaurant(order_id)
            elif message["reply_from"] == "delivery_service":
                delivery_status = message["delivery_status"]
                if delivery_status == "accepted":
                    cls.order_accepted_by_delivery(order_id)
                else:
                    cls.order_rejected_by_delivery(order_id)
                print(f"saga completed for order id: {order_id}")
        except Exception as e:
            print(f"exception occurred: {e}")

    @classmethod
    def order_accepted_by_restaurant(cls, order_id):
        """this method will be called when order is accepted by restaurant and now, delivery service is contacted"""

        Order.update_saga_props(order_id, 1, SagaStatus.DONE.value)
        Order.update_status(order_id, OrderStatus.ACCEPTED.value)
        cls.call_delivery_service(Order.get_order_by_id(order_id))

    @classmethod
    def order_rejected_by_restaurant(cls, order_id):
        print(f"restaurant failed to accept the order. there is no point proceeding ahead.")
        Order.update_saga_props(order_id, 1, SagaStatus.DONE.value)
        Order.update_status(order_id, OrderStatus.CANCELLED.value)

    @classmethod
    def order_accepted_by_delivery(cls, order_id):
        Order.update_saga_props(order_id, 2, SagaStatus.DONE.value)
        Order.update_status(order_id, OrderStatus.ON_WAY.value)

    @classmethod
    def order_rejected_by_delivery(cls, order_id):
        print(f"delivery service rejected for order id: {order_id}")
        Order.update_saga_props(order_id, 2, SagaStatus.DONE.value)
        Order.update_status(order_id, OrderStatus.WAITING_FOR_DELIVERY.value)

    @classmethod
    def call_delivery_service(cls, order_details):
        print(f"Beginning saga step 2 for order id: {order_details['order_id']}", flush=True)
        if not RabbitClient.get_rabbit_connection_status():
            Order.update_saga_props(order_details["order_id"], 2, SagaStatus.WAITING.value)
            order_details = Order.remove_keys(order_details, ["saga_stage", "saga_stage_status", "status"])
            RabbitClient.publish_message(json.dumps(order_details), "delivery_queue", RoutingKey.DELIVERY_CHECK.value)
        else:
            print(f"rabbit connection is blocked, please try again later")
            Order.update_saga_props(order_details["order_id"], 2, SagaStatus.PENDING.value)
