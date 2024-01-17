import unittest

from src.app import create_app
from src.core import constants


class TestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

    def test_provision_data(self) -> None:
        rv = self.client.post('/user_update', headers= {
            "x-secret-key": constants.OPERATION_AUTH_KEY
        })
        print(rv.data)


if __name__ == '__main__':
    unittest.main()
