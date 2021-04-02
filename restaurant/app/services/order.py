class Order(object):

    orders = []
    order_id = 0

    @classmethod
    def add_order(cls, ordered_item, reply_to=None):
        ordered_item["id"] = cls.order_id
        ordered_item["restaurant_status"] = "pending"
        ordered_item["reply_to"] = reply_to
        cls.orders.append(ordered_item)
        cls.order_id += 1
        return cls.remove_keys(ordered_item, ["reply_to"])

    @classmethod
    def get_all_orders(cls):
        return list(map(lambda x: cls.remove_keys(x, ["reply_to"]), cls.orders))

    @staticmethod
    def remove_keys(input_dict, keys: list):
        return dict([(k, v) for k, v in input_dict.items() if k not in keys])

    @classmethod
    def get_order_by_id(cls, order_id):
        a = [x for x in cls.orders if x["id"] == int(order_id)]
        return cls.remove_keys(a[0], ["reply_to"]) if len(a) else {}

    @classmethod
    def update_order_status_by_id(cls, order_id, order_status):
        for i, j in enumerate(cls.orders):
            if j["id"] == int(order_id):
                j["restaurant_status"] = order_status
                return cls.orders[i]
        return {}
