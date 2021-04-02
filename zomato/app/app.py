import asyncio
import threading
import signal

from flask import Flask, request, jsonify

from services.saga_orhestrator import SagaOrchestrator
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
    return 'Welcome to Zomato application!', 200


@app.route('/order/<item>', methods=['POST'])
def order(item):
    od = Order.add_order(item)
    SagaOrchestrator.begin_saga(od)
    return od, 201


@app.route('/order-details/<order_id>')
def order_details(order_id):
    res = Order.get_order_by_id(order_id)
    return res, 200 if res else 404


@app.route('/order-details-full/<order_id>')
def order_details_with_saga(order_id):
    res = Order.get_order_by_id(order_id, True)
    return res, 200 if res else 404


@app.route('/orders')
def all_order():
    return jsonify(Order.get_all_orders()), 200


@app.route('/rabbit')
def rabbit_details():
    return RabbitClient.get_rabbit_details(), 200


@app.route('/rabbit-toggle', methods=['PUT'])
def rabbit_toggle():
    return RabbitClient.block_rabbit_connection(), 200


if __name__ == '__main__':
    thread = threading.Thread(target=thread_function, name="rabbit-thread")
    thread.start()
    try:
        app.run('0.0.0.0', port=5000, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print('Interrupted! terminating flask app', flush=True)
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
