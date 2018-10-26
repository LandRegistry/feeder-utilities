from unittest import TestCase
from unittest.mock import patch, MagicMock
from feeder_utilities import feeder_rpc_client
import sys


class TestFeederRpcClient(TestCase):

    @patch('feeder_utilities.feeder_rpc_client.Queue')
    def setUp(self, mock_queue):
        TestCase.setUp(self)
        self.connection = MagicMock()
        self.exchange = MagicMock()
        self.routing_key = MagicMock()
        self.client = feeder_rpc_client.FeederRpcClient(self.connection, self.exchange, self.routing_key)

    def test_on_response_correlation_match(self):
        self.assertIsNone(self.client.response)
        message = MagicMock()
        message.properties = {"correlation_id": "aardvark"}
        message.payload = {"a": "payload"}
        self.client.correlation_id = "aardvark"
        self.client.on_response(message)
        self.assertEqual({"a": "payload"}, self.client.response)

    def test_on_response_correlation_no_match(self):
        self.assertIsNone(self.client.response)
        message = MagicMock()
        message.properties = {"correlation_id": "notaardvark"}
        message.payload = {"a": "payload"}
        self.client.correlation_id = "aardvark"
        self.client.on_response(message)
        self.assertIsNone(self.client.response)

    def test_call_not_allowed(self):
        with self.assertRaises(Exception) as exc:
            self.client.call("acab")
        self.assertEqual(str(exc.exception), "Method 'acab' not allowed")

    @patch('feeder_utilities.feeder_rpc_client.Producer')
    @patch('feeder_utilities.feeder_rpc_client.Consumer')
    def test_call_ok(self, mock_consumer, mock_producer):
        self.connection.drain_events = self.mock_drain
        response = self.client.call("health")
        mock_producer.return_value.__enter__.return_value.publish.assert_called()
        self.assertEqual({"a": "payload"}, response)

    def mock_drain(self):
        message = MagicMock()
        message.properties = {"correlation_id": self.client.correlation_id}
        message.payload = {"a": "payload"}
        self.client.on_response(message)


class TestFeederRpcClientMain(TestCase):

    @patch('feeder_utilities.feeder_rpc_client.FeederRpcClient')
    @patch('feeder_utilities.feeder_rpc_client.Connection')
    @patch("feeder_utilities.feeder_rpc_client.argparse.ArgumentParser")
    def test_main_ok(self, mock_arg_parse, mock_connection, mock_rpc_client):
        mock_rpc_client.return_value.call.return_value = {"a": "response", "success": True}
        mock_arg_parse.return_value.parse_args.return_valye.method = "health"
        feeder_rpc_client.main()
        mock_rpc_client.return_value.call.assert_called()

    @patch('feeder_utilities.feeder_rpc_client.FeederRpcClient')
    @patch('feeder_utilities.feeder_rpc_client.Connection')
    @patch("feeder_utilities.feeder_rpc_client.argparse.ArgumentParser")
    def test_main_fail(self, mock_arg_parse, mock_connection, mock_rpc_client):
        mock_rpc_client.return_value.call.return_value = {"a": "response", "success": False}
        mock_arg_parse.return_value.parse_args.return_value.method = "health"
        with self.assertRaises(SystemExit) as cm:
            feeder_rpc_client.main()
        self.assertEqual(cm.exception.code, 1)
        mock_rpc_client.return_value.call.assert_called()

    @patch('feeder_utilities.feeder_rpc_client.FeederRpcClient')
    @patch('feeder_utilities.feeder_rpc_client.Connection')
    @patch("feeder_utilities.feeder_rpc_client.argparse.ArgumentParser")
    def test_main_health_fail(self, mock_arg_parse, mock_connection, mock_rpc_client):
        mock_rpc_client.return_value.call.return_value = {
            "a": "response", "success": True, "result": {"status": "BAD"}}
        mock_arg_parse.return_value.parse_args.return_value.method = "health"
        with self.assertRaises(SystemExit) as cm:
            feeder_rpc_client.main()
        self.assertEqual(cm.exception.code, 1)
        mock_rpc_client.return_value.call.assert_called()
