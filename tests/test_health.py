from unittest import TestCase
from unittest.mock import patch
from feeder_utilities import health
from amqp.exceptions import NotFound


class TestFeederHealth(TestCase):

    @patch('feeder_utilities.health.rabbitmq')
    def test_no_error_queue(self, mock_rabbit):
        feeder_health = health.FeederHealth("none", "of", "this", "matters", "much")
        mock_rabbit.get_queue_count.side_effect = [1, 1, NotFound()]
        response = feeder_health.generate_health_msg()
        self.assertEqual(response, {'app': 'none',
                                    'error_queue_size': None,
                                    'queue_size': 1,
                                    'rpc_queue_size': 1,
                                    'status': 'OK'})

    @patch('feeder_utilities.health.rabbitmq')
    def test_empty_error_queue(self, mock_rabbit):
        feeder_health = health.FeederHealth("none", "of", "this", "matters", "much")
        mock_rabbit.get_queue_count.side_effect = [1, 1, 0]
        response = feeder_health.generate_health_msg()
        self.assertEqual(response, {'app': 'none',
                                    'error_queue_size': 0,
                                    'queue_size': 1,
                                    'rpc_queue_size': 1,
                                    'status': 'OK'})

    @patch('feeder_utilities.health.rabbitmq')
    def test_not_empty_error_queue(self, mock_rabbit):
        feeder_health = health.FeederHealth("none", "of", "this", "matters", "much")
        mock_rabbit.get_queue_count.side_effect = [1, 1, 1]
        response = feeder_health.generate_health_msg()
        self.assertEqual(response, {'app': 'none',
                                    'error_queue_size': 1,
                                    'queue_size': 1,
                                    'rpc_queue_size': 1,
                                    'status': 'BAD'})
