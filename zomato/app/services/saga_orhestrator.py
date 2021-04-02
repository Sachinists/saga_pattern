import json

from .order import Order
from .rabbit import RabbitClient


class SagaOrchestrator(object):
    """
        checks availability with restaurant
            -   pending (publish is yet to happen) (scenario when we received the BLOCKED connection callback)
            -   waiting (restaurant is yet to accept and send reply)
            -   done
        payment
            -   pending (publish is yet to happen) (scenario when we received the BLOCKED connection callback)
            -   waiting (bank is yet to accept and reply)
            -   done
    """

    @classmethod
    def begin_saga(cls, order_details):
        """checks restaurant -> payment interface"""
        print(f"Saga Begins for order id: {order_details['order_id']}", flush=True)
        if not RabbitClient.get_rabbit_connection_status():
            Order.update_saga_props(order_details["order_id"], 1, "waiting")
            order_details = Order.remove_keys(order_details, ["saga_stage", "saga_stage_status", "status"])
            RabbitClient.publish_message(json.dumps(order_details), queue_name="restaurant_queue",
                                         routing_key="check.order.availability")
        else:
            print(f"rabbit connection is blocked, please try again later")
            Order.update_saga_props(order_details["order_id"], 1, "pending")

    @classmethod
    def first_step(cls):
        pass
