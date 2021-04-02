class Order(object):

    order_list = []
    order_id = -1

    @classmethod
    def add_order(cls, item):
        cls.order_id += 1
        new_order = {
            "order_id": cls.order_id,
            "status": "Pending",
            "item": item,
            "saga_stage": 1,
            "saga_stage_status": "pending"
        }
        cls.order_list.append(new_order)
        return cls.remove_keys(new_order)

    @classmethod
    def get_all_orders(cls):
        return list(map(lambda x: cls.remove_keys(x), cls.order_list))

    @classmethod
    def get_order_by_id(cls, order_id, full=False):
        temp = [x for x in cls.order_list if x["order_id"] == int(order_id)]
        if len(temp):
            return cls.remove_keys(temp[0]) if not full else temp[0]
        return {}

    @staticmethod
    def remove_keys(input_dict, keys: list = ["saga_stage", "saga_stage_status"]):
        return dict([(k, v) for k, v in input_dict.items() if k not in keys])

    @classmethod
    def update_saga_props(cls, order_id, stage, status):
        print(f"updating saga properties of order id: {order_id} with stage: {stage} and it's status: {status}")
        for i, j in enumerate(cls.order_list):
            if j["order_id"] == int(order_id):
                j["saga_stage"] = stage
                j["saga_stage_status"] = status
                return cls.order_list[i]
        return {}
