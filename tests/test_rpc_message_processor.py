from unittest import TestCase
from unittest.mock import patch, MagicMock
from feeder_utilities import rpc_message_processor
from feeder_utilities.exceptions import RpcMessageProcessingException


class TestRpcMessageProcessor(TestCase):

    def save_message(self, logger, rpc_response, rabbitmq_url, exchange, reply_to,
                     correlation_id=None, queue_name=None):
        self.rpc_response = rpc_response

    def test_process_rpc_message_no_reply(self):
        mock_logger = MagicMock()
        proc = rpc_message_processor.RpcMessageProcessor(mock_logger, "app_name", "integrity_check", "rabbitmq_url",
                                                         "queue_name", "rpc_queue_name", "error_queue_name",
                                                         "register_url", "routing_key")
        mock_message = MagicMock()
        mock_message.properties.get.side_effect = [None, "correlation"]
        proc.process_rpc_message({}, mock_message, MagicMock())
        mock_message.reject.assert_called()

    @patch("feeder_utilities.rpc_message_processor.rabbitmq")
    def test_process_rpc_message_no_method(self, mock_rabbit):
        mock_logger = MagicMock()
        proc = rpc_message_processor.RpcMessageProcessor(mock_logger, "app_name", "integrity_check", "rabbitmq_url",
                                                         "queue_name", "rpc_queue_name", "error_queue_name",
                                                         "register_url", "routing_key")
        mock_message = MagicMock()
        mock_message.properties.get.side_effect = ["reply-to", "correlation"]
        mock_rabbit.publish_message = self.save_message
        proc.process_rpc_message({}, mock_message, MagicMock())
        mock_message.reject.assert_called()
        self.assertEqual(self.rpc_response,
                         {"success": False,
                          "result": None,
                          'error': {'error_message': 'Exception occured: '
                                    "RpcMessageProcessingException('Message body must "
                                    "contain method name')"}})

    @patch("feeder_utilities.rpc_message_processor.rabbitmq")
    def test_process_rpc_message_unknown_method(self, mock_rabbit):
        mock_logger = MagicMock()
        proc = rpc_message_processor.RpcMessageProcessor(mock_logger, "app_name", "integrity_check", "rabbitmq_url",
                                                         "queue_name", "rpc_queue_name", "error_queue_name",
                                                         "register_url", "routing_key")
        mock_message = MagicMock()
        mock_message.properties.get.side_effect = ["reply-to", "correlation"]
        mock_rabbit.publish_message = self.save_message
        proc.process_rpc_message({"method": "rhubarb"}, mock_message, MagicMock())
        mock_message.reject.assert_called()
        self.assertEqual(self.rpc_response,
                         {"success": False,
                          "result": None,
                          'error': {'error_message': 'Exception occured: '
                                    'RpcMessageProcessingException("Unknown method '
                                    '\'rhubarb\'")'}})

    @patch("feeder_utilities.rpc_message_processor.FeederHealth")
    @patch("feeder_utilities.rpc_message_processor.rabbitmq")
    def test_process_rpc_message_health_ok(self, mock_rabbit, mock_health):
        mock_logger = MagicMock()
        proc = rpc_message_processor.RpcMessageProcessor(mock_logger, "app_name", "integrity_check", "rabbitmq_url",
                                                         "queue_name", "rpc_queue_name", "error_queue_name",
                                                         "register_url", "routing_key")
        mock_message = MagicMock()
        mock_message.properties.get.side_effect = ["reply-to", "correlation"]
        mock_rabbit.publish_message = self.save_message
        mock_health.return_value.generate_health_msg.return_value = {"status": "OK"}
        proc.process_rpc_message({"method": "health"}, mock_message, MagicMock())
        self.assertEqual(self.rpc_response,
                         {"success": True,
                          "result": {'status': 'OK'},
                          'error': None})

    @patch("feeder_utilities.rpc_message_processor.FeederHealth")
    @patch("feeder_utilities.rpc_message_processor.rabbitmq")
    def test_process_rpc_message_health_bad(self, mock_rabbit, mock_health):
        mock_logger = MagicMock()
        proc = rpc_message_processor.RpcMessageProcessor(mock_logger, "app_name", "integrity_check", "rabbitmq_url",
                                                         "queue_name", "rpc_queue_name", "error_queue_name",
                                                         "register_url", "routing_key")
        mock_message = MagicMock()
        mock_message.properties.get.side_effect = ["reply-to", "correlation"]
        mock_rabbit.publish_message = self.save_message
        mock_health.return_value.generate_health_msg.return_value = {"status": "BAD"}
        proc.process_rpc_message({"method": "health"}, mock_message, MagicMock())
        self.assertEqual(self.rpc_response,
                         {"success": True,
                          "result": {'status': 'BAD'},
                          'error': None})

    @patch("feeder_utilities.rpc_message_processor.Register")
    @patch("feeder_utilities.rpc_message_processor.rabbitmq")
    def test_process_rpc_message_integrity_check(self, mock_rabbit, mock_register):
        mock_logger = MagicMock()
        mock_integrity = MagicMock()
        proc = rpc_message_processor.RpcMessageProcessor(mock_logger, "app_name", mock_integrity, "rabbitmq_url",
                                                         "queue_name", "rpc_queue_name", "error_queue_name",
                                                         "register_url", "routing_key")
        mock_message = MagicMock()
        mock_message.properties.get.side_effect = ["reply-to", "correlation"]
        mock_rabbit.publish_message = self.save_message
        mock_register.return_value.max_entry.return_value = 2
        mock_integrity.check_integrity.return_value = [1, 2]
        proc.process_rpc_message({"method": "integrity_check"}, mock_message, MagicMock())
        self.assertEqual(self.rpc_response,
                         {"success": True,
                          "result": {'missing_entries': [1, 2]},
                          'error': None})

    @patch("feeder_utilities.rpc_message_processor.Register")
    @patch("feeder_utilities.rpc_message_processor.rabbitmq")
    def test_process_rpc_message_integrity_fix(self, mock_rabbit, mock_register):
        mock_logger = MagicMock()
        mock_integrity = MagicMock()
        proc = rpc_message_processor.RpcMessageProcessor(mock_logger, "app_name", mock_integrity, "rabbitmq_url",
                                                         "queue_name", "rpc_queue_name", "error_queue_name",
                                                         "register_url", "routing_key")
        mock_message = MagicMock()
        mock_message.properties.get.side_effect = ["reply-to", "correlation"]
        mock_rabbit.publish_message = self.save_message
        mock_register.return_value.max_entry.return_value = 2
        mock_register.return_value.republish_entries.return_value = {
            "entries_not_found": [], "republished_entries": [1, 2]}
        mock_integrity.check_integrity.return_value = [1, 2]
        proc.process_rpc_message({"method": "integrity_fix"}, mock_message, MagicMock())
        self.assertEqual(self.rpc_response,
                         {"success": True,
                          "result": {'entries_not_found': [], 'republished_entries': [1, 2]},
                          'error': None})

    @patch("feeder_utilities.rpc_message_processor.Register")
    @patch("feeder_utilities.rpc_message_processor.rabbitmq")
    def test_process_rpc_message_integrity_fix_none(self, mock_rabbit, mock_register):
        mock_logger = MagicMock()
        mock_integrity = MagicMock()
        proc = rpc_message_processor.RpcMessageProcessor(mock_logger, "app_name", mock_integrity, "rabbitmq_url",
                                                         "queue_name", "rpc_queue_name", "error_queue_name",
                                                         "register_url", "routing_key")
        mock_message = MagicMock()
        mock_message.properties.get.side_effect = ["reply-to", "correlation"]
        mock_rabbit.publish_message = self.save_message
        mock_register.return_value.max_entry.return_value = 2
        mock_integrity.check_integrity.return_value = []
        proc.process_rpc_message({"method": "integrity_fix"}, mock_message, MagicMock())
        self.assertEqual(self.rpc_response,
                         {"success": True,
                          "result": {'entries_not_found': [], 'republished_entries': []},
                          'error': None})

    @patch("feeder_utilities.rpc_message_processor.ErrorQueueClient")
    @patch("feeder_utilities.rpc_message_processor.rabbitmq")
    def test_process_rpc_message_dump_error_queue(self, mock_rabbit, mock_err_client):
        mock_logger = MagicMock()
        proc = rpc_message_processor.RpcMessageProcessor(mock_logger, "app_name", "integrity_check", "rabbitmq_url",
                                                         "queue_name", "rpc_queue_name", "error_queue_name",
                                                         "register_url", "routing_key")
        mock_message = MagicMock()
        mock_message.properties.get.side_effect = ["reply-to", "correlation"]
        mock_rabbit.publish_message = self.save_message
        mock_err_client.return_value.retrieve_messages.return_value = []
        proc.process_rpc_message({"method": "dump_error_queue"}, mock_message, MagicMock())
        self.assertEqual(self.rpc_response,
                         {"success": True,
                          "result": {'error_messages': []},
                          'error': None})

    @patch("feeder_utilities.rpc_message_processor.ErrorQueueClient")
    @patch("feeder_utilities.rpc_message_processor.rabbitmq")
    def test_process_rpc_message_requeue_errors(self, mock_rabbit, mock_err_client):
        mock_logger = MagicMock()
        proc = rpc_message_processor.RpcMessageProcessor(mock_logger, "app_name", "integrity_check", "rabbitmq_url",
                                                         "queue_name", "rpc_queue_name", "error_queue_name",
                                                         "register_url", "routing_key")
        mock_message = MagicMock()
        mock_message.properties.get.side_effect = ["reply-to", "correlation"]
        mock_rabbit.publish_message = self.save_message
        mock_err_client.return_value.requeue_messages.return_value = []
        proc.process_rpc_message({"method": "requeue_errors"}, mock_message, MagicMock())
        self.assertEqual(self.rpc_response,
                         {"success": True,
                          "result": {'requeued_messages': []},
                          'error': None})

    @patch("feeder_utilities.rpc_message_processor.ErrorQueueClient")
    @patch("feeder_utilities.rpc_message_processor.rabbitmq")
    def test_process_rpc_message_delete_errors(self, mock_rabbit, mock_err_client):
        mock_logger = MagicMock()
        proc = rpc_message_processor.RpcMessageProcessor(mock_logger, "app_name", "integrity_check", "rabbitmq_url",
                                                         "queue_name", "rpc_queue_name", "error_queue_name",
                                                         "register_url", "routing_key")
        mock_message = MagicMock()
        mock_message.properties.get.side_effect = ["reply-to", "correlation"]
        mock_rabbit.publish_message = self.save_message
        mock_err_client.return_value.delete_messages.return_value = []
        proc.process_rpc_message({"method": "delete_errors"}, mock_message, MagicMock())
        self.assertEqual(self.rpc_response,
                         {"success": True,
                          "result": {'deleted_messages': []},
                          'error': None})

    @patch("feeder_utilities.rpc_message_processor.Register")
    def test_startup_integrity_check(self, mock_register):
        mock_logger = MagicMock()
        mock_integrity = MagicMock()
        proc = rpc_message_processor.RpcMessageProcessor(mock_logger, "app_name", mock_integrity, "rabbitmq_url",
                                                         "queue_name", "rpc_queue_name", "error_queue_name",
                                                         "register_url", "routing_key")
        mock_register.return_value.max_entry.return_value = 2
        mock_register.return_value.republish_entries.return_value = {
            "entries_not_found": [], "republished_entries": [1, 2]}
        mock_integrity.check_integrity.return_value = [1, 2]
        result = proc.startup_integrity_check(MagicMock())
        self.assertEqual(result, {'entries_not_found': [], 'republished_entries': [1, 2]})
