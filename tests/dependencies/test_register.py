from unittest import TestCase
from unittest.mock import MagicMock
from feeder_utilities.dependencies import register
from feeder_utilities.exceptions import RegisterException


class TestRegister(TestCase):

    def test_max_entry_ok(self):
        mock_requests = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"total-entries": 1}
        mock_requests.get.return_value = mock_response
        response = register.Register("register_url", "routing_key", mock_requests).max_entry()
        self.assertEqual(response, 1)

    def test_max_entry_500(self):
        mock_requests = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"total-entries": 1}
        mock_requests.get.return_value = mock_response
        with self.assertRaises(RegisterException) as exc:
            register.Register("register_url", "routing_key", mock_requests).max_entry()
        self.assertRegex(str(exc.exception), r".*Unable to retrieve register information.*")

    def test_max_entry_invalid(self):
        mock_requests = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"total-lywrong": 1}
        mock_requests.get.return_value = mock_response
        with self.assertRaises(RegisterException) as exc:
            register.Register("register_url", "routing_key", mock_requests).max_entry()

        self.assertRegex(str(exc.exception), r".*Register response not recognised, did not contain 'total-entries'.*")

    def test_republish_entries_ok(self):
        mock_requests = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"some-kind": "of-response"}
        mock_requests.post.return_value = mock_response
        response = register.Register("register_url", "routing_key", mock_requests).republish_entries([1])
        self.assertEqual(response, {"some-kind": "of-response"})

    def test_republish_entries_500(self):
        mock_requests = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"some-kind": "of-response"}
        mock_requests.post.return_value = mock_response
        with self.assertRaises(RegisterException) as exc:
            register.Register("register_url", "routing_key", mock_requests).republish_entries([1])
        self.assertRegex(str(exc.exception), r".*Unable to republish enties.*")
