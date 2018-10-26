from feeder_utilities.health import FeederHealth
from feeder_utilities.exceptions import RpcMessageProcessingException
from feeder_utilities.dependencies.rabbitmq import ErrorQueueClient
from feeder_utilities.dependencies import rabbitmq
from feeder_utilities.dependencies.register import Register


class RpcMessageProcessor:

    def __init__(self, logger, app_name, integrity_check, rabbitmq_url, queue_name, rpc_queue_name, error_queue_name,
                 register_url, routing_key):
        self.logger = logger
        self.app_name = app_name
        self.integrity_check = integrity_check
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.rpc_queue_name = rpc_queue_name
        self.error_queue_name = error_queue_name
        self.register_url = register_url
        self.routing_key = routing_key

    def startup_integrity_check(self, requests):
        self.logger.info("Checking database integrity")
        max_entry = Register(self.register_url, self.routing_key, requests).max_entry()
        missing_entries = self.integrity_check.check_integrity(max_entry)
        result = None
        if missing_entries:
            self.logger.error("Detected missing_entries: {}".format(missing_entries))
            self.logger.error("Requesting missing_entries from register")
            result = Register(self.register_url,
                              self.routing_key, requests).republish_entries(missing_entries)
        return result

    def process_rpc_message(self, body, message, requests):
        self.logger.info("Processing rpc message")

        reply_to = message.properties.get('reply_to', None)
        correlation_id = message.properties.get('correlation_id', None)

        if not reply_to or not correlation_id:
            self.logger.error("Message must have reply_to and correlation_id")
            message.reject()
        else:
            try:
                rpc_response = None
                if 'method' not in body or not body['method']:
                    raise RpcMessageProcessingException("Message body must contain method name")
                if body['method'] == 'health':
                    self.logger.info("Processing health check message")
                    rpc_result = FeederHealth(self.app_name, self.rabbitmq_url, self.queue_name, self.rpc_queue_name,
                                              self.error_queue_name).generate_health_msg()
                    if 'status' in rpc_result and rpc_result['status'] == 'BAD':
                        self.logger.error("Feeder reporting BAD status: {}".format(rpc_result))
                elif body['method'] == 'integrity_check':
                    self.logger.info("Detecting gaps in entry sequence")
                    max_entry = Register(self.register_url, self.routing_key, requests).max_entry()
                    rpc_result = {"missing_entries": self.integrity_check.check_integrity(max_entry)}
                    if rpc_result["missing_entries"]:
                        self.logger.error("Detected missing_entries: {}".format(rpc_result))
                elif body['method'] == 'integrity_fix':
                    self.logger.info("Fixing database integrity")
                    max_entry = Register(self.register_url, self.routing_key, requests).max_entry()
                    missing_entries = self.integrity_check.check_integrity(max_entry)
                    if missing_entries:
                        self.logger.error("Detected missing_entries: {}".format(missing_entries))
                        self.logger.error("Requesting missing_entries from register")
                        rpc_result = Register(self.register_url,
                                              self.routing_key, requests).republish_entries(missing_entries)
                    else:
                        self.logger.info("No missing entries detected")
                        rpc_result = {"entries_not_found": [], "republished_entries": []}
                elif body['method'] == 'dump_error_queue':
                    self.logger.info("Dumping contents of error queue")
                    rpc_result = {
                        "error_messages": ErrorQueueClient(self.logger, self.rabbitmq_url, self.queue_name,
                                                           self.error_queue_name).retrieve_messages()}
                    self.logger.info("Dumping {} error messages".format(len(rpc_result)))
                elif body['method'] == 'requeue_errors':
                    self.logger.info("Requeuing contents of error queue")
                    rpc_result = {
                        "requeued_messages": ErrorQueueClient(self.logger, self.rabbitmq_url, self.queue_name,
                                                              self.error_queue_name).requeue_messages()}
                    self.logger.info("Requeued {} error messages".format(len(rpc_result)))
                elif body['method'] == 'delete_errors':
                    self.logger.info("Deleting contents of error queue")
                    rpc_result = {
                        "deleted_messages": ErrorQueueClient(self.logger, self.rabbitmq_url, self.queue_name,
                                                             self.error_queue_name).delete_messages()}
                    self.logger.info("Deleted {} error messages".format(len(rpc_result)))
                else:
                    raise RpcMessageProcessingException("Unknown method '{}'".format(body['method']))

                rpc_response = {"success": True, "result": rpc_result, "error": None}
                self.logger.info("Publishing rpc response message")
                rabbitmq.publish_message(self.logger, rpc_response, self.rabbitmq_url, '', reply_to,
                                         correlation_id=correlation_id)
                message.ack()

            except Exception as e:
                self.logger.exception("Failed to process rpc message")
                rpc_response = {
                    "success": False,
                    "result": None,
                    "error": {
                        "error_message": "Exception occured: {}".format(
                            repr(e))}}
                rabbitmq.publish_message(self.logger, rpc_response, self.rabbitmq_url, '', reply_to,
                                         correlation_id=correlation_id)
                self.logger.error("Failure message sent to queue '{}'".format(reply_to))
                message.reject()
