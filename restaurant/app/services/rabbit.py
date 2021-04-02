import json

import pika

from pika.adapters.asyncio_connection import AsyncioConnection
from pika.channel import Channel
from pika.connection import Connection

from .order import Order


class RabbitClient:

    connection: Connection = None
    channel: Channel = None
    queue_name = "restaurant_queue"
    exchange_name = "saga"
    confirmed = 0
    published = 0
    published_message = {}
    failed_index = []
    succeeded_index = []

    @classmethod
    def get_rabbit_details(cls):
        return {
            "queue_name": cls.queue_name,
            "confirmed": cls.confirmed,
            "published": cls.published,
            "published_message": cls.published_message,
            "failed_index": cls.failed_index,
            "succeeded_index": cls.succeeded_index
        }

    @classmethod
    def connect(cls, hostname="localhost", queue_name=queue_name):
        print(' [*] Connecting to server ...', flush=True)
        print(f' [*] Hostname: {hostname} ...', flush=True)
        print(f' [*] Queue name: {queue_name} ...', flush=True)
        cls.connection = AsyncioConnection(
            pika.URLParameters("amqp://guest:guest@localhost:5672"),
            on_open_callback=cls.on_connection_open,
            on_open_error_callback=cls.on_connection_open_error,
            on_close_callback=cls.on_connection_closed
        )

    @classmethod
    def on_connection_open(cls, connection: Connection):
        print(f"on successful connection open", flush=True)
        cls.connection = connection
        cls.channel = connection.channel(on_open_callback=cls.on_channel_open)

    @classmethod
    def on_channel_open(cls, channel: Channel):
        print(f"channel successful established")
        cls.channel = channel
        cls.channel.exchange_declare(exchange=cls.exchange_name, callback=cls.on_exchange_declare_ok)

    @classmethod
    def on_exchange_declare_ok(cls, method_frame):
        print("exchange declared ok")
        cls.channel.queue_declare(queue=cls.queue_name, callback=cls.on_queue_declare_ok)

    @classmethod
    def on_queue_declare_ok(cls, method_frame):
        print(f"queue declared ok")
        cls.channel.queue_bind(cls.queue_name, cls.exchange_name, 'check.order.availability',
                               callback=cls.on_queue_bind_ok)

    @classmethod
    def on_queue_bind_ok(cls, method_frame):
        print("on queue bind ok")
        cls.channel.basic_consume(queue=cls.queue_name, on_message_callback=cls.on_message, auto_ack=True)

    @classmethod
    def on_message(cls, ch, method: pika.spec.Basic.Deliver, props: pika.BasicProperties, body):
        print(f"Received normal message: {json.loads(body)}")
        if method.routing_key == "check.order.availability":
            Order.add_order(json.loads(body), props.reply_to)

    @classmethod
    def on_connection_open_error(cls, connection, exception):
        print(f"{exception} exception occurred while opening connection", flush=True)
        cls.connection = connection

    @classmethod
    def on_connection_closed(cls, connection, exception):
        print(f"{exception} exception occurred while closing connection", flush=True)
        cls.connection = connection

    @classmethod
    def on_ack_nack(cls, method_frame):
        confirmation_type = method_frame.method.NAME.split('.')[1].lower()
        if confirmation_type == "ack":
            cls.confirmed += 1
            print(f"confirmed for delivery tag: {method_frame.method.delivery_tag}")
            cls.succeeded_index.append(method_frame.method.delivery_tag)
        else:
            print(f"failed to publish for delivery tag: {method_frame.method.delivery_tag}")
            cls.failed_index.append(method_frame.method.delivery_tag)

    @classmethod
    def publish_message(cls, message, exchange_name, routing_key):
        if cls.channel is not None:
            print(f"publishing message: {message} to routing_key: {routing_key} in exchange: {exchange_name}")
            cls.channel.confirm_delivery(ack_nack_callback=cls.on_ack_nack)
            cls.channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2
                ),
                mandatory=True
            )
        else:
            print("channel is None", flush=True)
