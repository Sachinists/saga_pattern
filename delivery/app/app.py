import asyncio
import json
import threading
import signal

from flask import Flask, request, jsonify

from services.order import Order
from services.rabbit import RabbitClient

signal.signal(signal.SIGINT, signal.SIG_DFL)
app = Flask(__name__)


def thread_function():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        RabbitClient.connect()
        loop.run_forever()
    except KeyboardInterrupt:
        print('Interrupted! terminating flask app', flush=True)
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')


@app.route('/ping')
def ping():
    return 'Welcome to delivery application!', 200


@app.route('/publish/<message>', methods=['POST'])
def publish(message):
    RabbitClient.publish_message(message, queue_name="delivery_queue")
    return "Successfully processed message: %s" % message, 201


@app.route('/rabbit')
def rabbit_details():
    return RabbitClient.get_rabbit_details(), 200


@app.route('/orders')
def get_all_orders():
    return jsonify(Order.get_all_orders()), 200


@app.route('/order/<order_id>')
def get_order_by_id(order_id):
    res = Order.get_order_by_id(order_id)
    return res, 200 if res else 404


@app.route('/order/<res_id>/<status>', methods=['PUT'])
def update_order(res_id, status):
    # test commit
    response = Order.update_order_status_by_id(res_id, status)
    if response:
        reply_to = response["reply_to"]
        response = Order.remove_keys(response, ["id", "reply_to"])
        response["reply_from"] = "delivery_service"
        if reply_to:
            RabbitClient.publish_message(message=json.dumps(response), routing_key=reply_to, exchange_name="")
    return response, 200 if response else 204


@app.route('/order/<item>', methods=['POST'])
def add_order(item):
    oi = {"order_id": None, "item": item}
    return Order.add_order(ordered_item=oi), 201


if __name__ == '__main__':
    thread = threading.Thread(target=thread_function, name="rabbit-thread")
    thread.start()
    try:
        app.run('0.0.0.0', port=5002, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print('Interrupted! terminating flask app', flush=True)
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
