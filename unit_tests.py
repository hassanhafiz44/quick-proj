import os
import logging
import tempfile
import unittest
from flaskr import create_app, db

class BlogSearchTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app({
            'TESTING': True,
            'DATABASE': self.db_path,
        })
        self.client = self.app.test_client()
        self.assertLogs('flaskr', level='INFO')

        with self.app.app_context():
            db.init_db()
            self._insert_data()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def _insert_data(self):
        conn = db.get_db()
        # Insert two users
        conn.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            ("alice", "a")
        )
        conn.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            ("bob", "b")
        )
        # Insert two posts
        conn.execute(
            "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
            ("Hello from Alice", "Alice writes about testing.", 1)
        )
        conn.execute(
            "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
            ("The Guide", "Bob writes about deployment.", 2)
        )
        conn.commit()

    # note: vague testing as what is returned is direct HTML
    
    def test_search_by_username(self):
        response = self.client.get('/?q=alice')
        self.assertIn(b"Hello from Alice", response.data)
        self.assertIn(b"username:", response.data) # vaguely contains


    def test_search_by_title(self):
        response = self.client.get('/?q=Guide')
        self.assertIn(b"The Guide", response.data)
        self.assertIn(b"title:", response.data) # vaguely contains
        self.assertNotIn(b"body:", response.data) # vaguely not contains


    def test_search_by_body(self):
        response = self.client.get('/?q=deployment')
        self.assertIn(b"The Guide", response.data)
        self.assertIn(b"body:", response.data) # vaguely contains
        self.assertNotIn(b"title:", response.data) # vaguely not contains

if __name__ == '__main__':
    unittest.main()