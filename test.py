import unittest
from unittest.mock import patch, MagicMock
from app import app


class TestCrud(unittest.TestCase):
    """Test case for CRUD operations and metrics endpoints."""

    def setUp(self):
        """Set up test client and reset metrics."""
        self.app = app.test_client()
        self.app.testing = True

    def _parse_metrics(self, response_data):
        """Helper method to parse metrics response."""
        metrics = {}
        for line in response_data.decode('utf-8').splitlines():
            if line and not line.startswith('#'):
                parts = line.split(' ')
                if len(parts) == 2:
                    metrics[parts[0]] = float(parts[1])
        return metrics

    def test_latency_endpoint(self):
        """Test latency endpoint."""
        response = self.app.get('/latency')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Latency endpoint', response.data)

        metrics_response = self.app.get('/metrics')
        metrics = self._parse_metrics(metrics_response.data)
        self.assertIn('request_count', metrics)
        self.assertGreater(metrics['request_count'], 0)

    def test_error_endpoint(self):
        """Test error endpoint."""
        response = self.app.get("/error")
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Database error occurred", response.data)

        metrics_response = self.app.get('/metrics')
        metrics = self._parse_metrics(metrics_response.data)
        self.assertIn('error_rate', metrics)
        self.assertGreater(metrics['error_rate'], 0)

    def test_timeout_endpoint(self):
        """Test timeout endpoint."""
        response = self.app.get('/timeout')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'End after 2sec', response.data)

        metrics_response = self.app.get('/metrics')
        metrics = self._parse_metrics(metrics_response.data)
        self.assertIn('request_count', metrics)
        self.assertIn('pass_rate', metrics)
        self.assertGreater(metrics['request_count'], 0)
        self.assertGreater(metrics['pass_rate'], 0)

    def test_timeout5_endpoint(self):
        """Test timeout5 endpoint."""
        response = self.app.get('/timeout5')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'End after 5sec', response.data)

        metrics_response = self.app.get('/metrics')
        metrics = self._parse_metrics(metrics_response.data)
        self.assertIn('request_count', metrics)
        self.assertIn('pass_rate', metrics)
        self.assertGreater(metrics['request_count'], 0)
        self.assertGreater(metrics['pass_rate'], 0)

    def test_mstimeout_endpoint(self):
        """Test ms timeout endpoint."""
        response = self.app.get('/mstimeout')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'End after 200ms', response.data)

        metrics_response = self.app.get('/metrics')
        metrics = self._parse_metrics(metrics_response.data)
        self.assertIn('request_count', metrics)
        self.assertIn('pass_rate', metrics)
        self.assertGreater(metrics['request_count'], 0)
        self.assertGreater(metrics['pass_rate'], 0)

    def test_metrics_endpoint(self):
        """Test metrics endpoint."""
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'request_latency_seconds_count', response.data)
        self.assertIn(b'request_count_total', response.data)
        self.assertIn(b'error_rate_total', response.data)
        self.assertIn(b'pass_rate_total', response.data)

    @patch("app.db_connection")
    def test_get_endpoint(self, mock_db_connection):
        """Test get endpoint with mocked database connection."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, 16)]
        mock_db_connection.cursor.return_value.__enter__.return_value = mock_cursor
        response = self.app.get('/get')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [[1, 16]])

        metrics_response = self.app.get('/metrics')
        metrics = self._parse_metrics(metrics_response.data)
        self.assertIn('request_count', metrics)
        self.assertGreater(metrics['request_count'], 0)
        self.assertIn('pass_rate', metrics)
        self.assertGreater(metrics['pass_rate'], 0)

    @patch("app.db_connection")
    def test_add_endpoint(self, mock_db_connection):
        """Test add endpoint with mocked database connection."""
        mock_db_connection.cursor.return_value.__enter__.return_value = MagicMock()
        response = self.app.post('/add', json={"item_id": 1, "data": "test"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json(), {"message": "Added"})

        metrics_response = self.app.get('/metrics')
        metrics = self._parse_metrics(metrics_response.data)
        self.assertIn('request_count', metrics)
        self.assertGreater(metrics['request_count'], 0)
        self.assertIn('pass_rate', metrics)
        self.assertGreater(metrics['pass_rate'], 0)

    @patch("app.db_connection")
    def test_modify_endpoint(self, mock_db_connection):
        """Test modify endpoint with mocked database connection."""
        mock_db_connection.cursor.return_value.__enter__.return_value = MagicMock()
        response = self.app.put('/put/1', json={"data": "test updated"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"message": "Modified"})

        metrics_response = self.app.get('/metrics')
        metrics = self._parse_metrics(metrics_response.data)
        self.assertIn('request_count', metrics)
        self.assertGreater(metrics['request_count'], 0)
        self.assertIn('pass_rate', metrics)
        self.assertGreater(metrics['pass_rate'], 0)

    @patch("app.db_connection")
    def test_delete_endpoint(self, mock_db_connection):
        """Test delete endpoint with mocked database connection."""
        mock_db_connection.cursor.return_value.__enter__.return_value = MagicMock()
        response = self.app.delete('/delete/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"message": "Deleted"})

        metrics_response = self.app.get('/metrics')
        metrics = self._parse_metrics(metrics_response.data)
        self.assertIn('request_count', metrics)
        self.assertGreater(metrics['request_count'], 0)
        self.assertIn('pass_rate', metrics)
        self.assertGreater(metrics['pass_rate'], 0)


if __name__ == "__main__":
    unittest.main()
