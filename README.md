# feeder-utilities

This repository contains a pip installable package for common server and client feeder utilities

## Quick start

```
pip3 install git+https://github.com/LandRegistry/feeder-utilities.git@<version/commit/branch/other ref>
```

## Usage (client)

The client can be used directly from command line:

```
usage: feeder-rpc-client [-h] -m METHOD -c CONNECTION -x EXCHANGE -r
                         ROUTING_KEY

Send feeder RPC commands

optional arguments:
  -h, --help      show this help message and exit
  -m METHOD       method to call on feeder, one of ['health',
                  'integrity_check', 'integrity_fix', 'dump_error_queue',
                  'requeue_errors', 'delete_errors']
  -c CONNECTION   rabbitmq connection string
  -x EXCHANGE     rabbitmq exchange name
  -r ROUTING_KEY  rabbitmq routing key
```

Alternatively it can be used within python:

```
from feeder_utilities.feeder_rpc_client import FeederRpcClient


client = FeederRpcClient(<rabbitmq connection string>, <rabbitmq exchange>, <rabbitmq routing key>)
response = client.call(<method>)
```
Response will be the JSON from the method

## Usage (server)

The included worker can be used to listen to two separate queues at the same time and response differently to each queue.  A generic RPC processing class is available for general feeder usage.

```
from feeder_app_name import config
from feeder_app_name.extensions import setup_loggers, logger
from feeder_app_name.process_message import MessageProcessor
# Custom module for the checking of database integrity, will vary with each feeder.  Should have one method `def check_integrity(max_entry):`
from feeder_app_name.utilities import integrity_check
from kombu import Connection, Exchange, Queue, binding
from feeder_utilities.dependencies.rabbitmq import Worker
from feeder_utilities.rpc_message_processor import RpcMessageProcessor


def run():
    setup_loggers()


    exchange = Exchange(config.EXCHANGE_NAME, type=config.EXCHANGE_TYPE)
    queues = [Queue(config.QUEUE_NAME, exchange,
                    bindings=[binding(exchange, routing_key=key) for key in config.ROUTING_KEYS])]

    rpc_exchange = Exchange(config.RPC_EXCHANGE_NAME, type='direct')
    rpc_queues = [Queue(config.RPC_QUEUE_NAME, rpc_exchange,
                        bindings=[binding(rpc_exchange, routing_key=config.RPC_ROUTING_KEY)])]


    with Connection(config.RABBIT_URL, heartbeat=4) as conn:
        try:
            message_processor = MessageProcessor(logger)
            rpc_message_processor = RpcMessageProcessor(logger, config.APP_NAME, integrity_check, config.RABBIT_URL,
                                                        config.QUEUE_NAME, config.RPC_QUEUE_NAME,
                                                        config.ERROR_QUEUE_NAME, config.REGISTER_URL,
                                                        config.ROUTING_KEYS[0])
            worker = Worker(
                logger,
                conn,
                queues,
                rpc_queues,
                message_processor.process_message,
                rpc_message_processor.process_rpc_message)
            logger.info("Running worker...")
            worker.run()
        except KeyboardInterrupt:
            logger.debug('KeyboardInterrupt')
        except Exception as e:
            logger.exception('Unhandled Exception: %s', repr(e))
```

### Available methods in RpcMessageProcessor

The default processor provides the following functions and example results:

- health - `{'status': '<BAD/OK>', 'error_queue_size': 0, 'rpc_queue_size': 0, 'app': '<app name>', 'queue_size': 0}`
- integrity_check - `{'missing_entries': [1,2,3,4]}`
- integrity_fix - `{'entries_not_found': [], 'republished_entries': []}`
- dump_error_queue - `{'error_messages': [{'headers': {<MESSAGE HEADERS>}, 'body': {<MESSAGE BODY>}}]}`
- requeue_errors - `{'error_messages': [{'headers': {<MESSAGE HEADERS>}, 'body': {<MESSAGE BODY>}}]}`
- delete_errors - `{'error_messages': [{'headers': {<MESSAGE HEADERS>}, 'body': {<MESSAGE BODY>}}]}`

Responses are in the basic form (using health as example)
```
{
    'success': True, # status of method
    'error': None, # populated with error if one occurred
    'result': { # result dependant on method called
        'status': 'BAD', 'error_queue_size': 1, 'rpc_queue_size': 0, 'app': 'maintain-feeder', 'queue_size': 0
    }
}
```

## Other useful things

Register client: feeder_utilities/dependencies/register.py
Rabbitmq utilities: feeder_utilities/dependencies/rabbitmq.py

## Unit tests

Unit tests are run as follows:
```
python setup.py nosetests
```
