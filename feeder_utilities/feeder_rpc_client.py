import argparse
import sys
from kombu import Connection, Producer, Consumer, Queue, uuid

ALLOWED_METHODS = ['health', 'integrity_check', 'integrity_fix', 'dump_error_queue', 'requeue_errors', 'delete_errors']


class FeederRpcClient(object):

    def __init__(self, connection, exchange, routing_key):
        self.connection = connection
        self.callback_queue = Queue(uuid(), exclusive=True, auto_delete=True)
        self.exchange = exchange
        self.routing_key = routing_key
        self.response = None
        self.correlation_id = None

    def on_response(self, message):
        if message.properties['correlation_id'] == self.correlation_id:
            self.response = message.payload

    def call(self, method):
        if method not in ALLOWED_METHODS:
            raise Exception("Method '{}' not allowed".format(method))
        self.response = None
        self.correlation_id = uuid()
        with Producer(self.connection) as producer:
            producer.publish(
                {'method': method},
                exchange=self.exchange,
                routing_key=self.routing_key,
                declare=[self.callback_queue],
                reply_to=self.callback_queue.name,
                correlation_id=self.correlation_id,
            )
        with Consumer(self.connection,
                      on_message=self.on_response,
                      queues=[self.callback_queue], no_ack=True):
            while self.response is None:
                self.connection.drain_events()
        return self.response


def main():

    parser = argparse.ArgumentParser(description='Send feeder RPC commands')
    parser.add_argument('-m', help='method to call on feeder, one of {}'.format(ALLOWED_METHODS), dest='method',
                        required=True)
    parser.add_argument('-c', help='rabbitmq connection string', dest='connection', required=True)
    parser.add_argument('-x', help='rabbitmq exchange name', dest='exchange', required=True)
    parser.add_argument('-r', help='rabbitmq routing key', dest='routing_key', required=True)
    args = parser.parse_args()
    connection = Connection(args.connection)
    feeder_rpc = FeederRpcClient(connection, args.exchange, args.routing_key)
    print("Sending method request to feeder")
    response = feeder_rpc.call(args.method)
    print("Response from feeder was:")
    print(response)
    if not response['success']:
        sys.exit(1)
    if args.method == 'health' and response['result']['status'] != "OK":
        sys.exit(1)


if __name__ == '__main__':
    main()
