from feeder_utilities.dependencies import rabbitmq
from amqp.exceptions import NotFound


class FeederHealth:

    def __init__(self, app_name, rabbitmq_url, queue_name, rpc_queue_name, error_queue_name):
        self.app_name = app_name
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.rpc_queue_name = rpc_queue_name
        self.error_queue_name = error_queue_name

    def generate_health_msg(self):
        error_queue_count = 0
        queue_size = rabbitmq.get_queue_count(self.rabbitmq_url, self.queue_name)
        rpc_queue_size = rabbitmq.get_queue_count(self.rabbitmq_url, self.rpc_queue_name)
        # Error queue may not exist if no errors
        try:
            error_queue_count = rabbitmq.get_queue_count(self.rabbitmq_url, self.error_queue_name)
        except NotFound as e:
            error_queue_count = None
        health = {"app": self.app_name,
                  "status": "OK",
                  "queue_size": queue_size,
                  "rpc_queue_size": rpc_queue_size,
                  "error_queue_size": error_queue_count}
        if error_queue_count and error_queue_count > 0:
            health['status'] = "BAD"
        return health
