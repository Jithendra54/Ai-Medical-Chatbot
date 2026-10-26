import os
import unittest
from unittest.mock import patch

from app import app


class CareGuideTestCase(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_homepage_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CareGuide', response.data)
        self.assertIn(b'Virtual assistant', response.data)

    def test_health_endpoint_has_mode(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json['mode'], ('demo', 'grok', 'ollama'))

    def test_rejects_missing_messages(self):
        response = self.client.post('/api/chat', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_rejects_overlong_message(self):
        response = self.client.post('/api/chat', json={
            'messages': [{'role': 'user', 'content': 'x' * 2001}]
        })
        self.assertEqual(response.status_code, 400)

    def test_emergency_phrase_returns_fast_safety_message(self):
        with patch.dict(os.environ, {'XAI_API_KEY': ''}):
            response = self.client.post('/api/chat', json={
                'messages': [{'role': 'user', 'content': 'I am having chest pain right now'}]
            })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['emergency'])
        self.assertIn('112', response.json['reply'])

    def test_demo_mode_returns_explicit_demo_reply(self):
        with patch.dict(os.environ, {'AI_PROVIDER': 'demo', 'XAI_API_KEY': ''}):
            response = self.client.post('/api/chat', json={
                'messages': [{'role': 'user', 'content': 'What can help with a mild cold?'}]
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['mode'], 'demo')
        self.assertIn('rest', response.json['reply'].lower())

    def test_security_headers_are_set(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
        self.assertIn('frame-ancestors', response.headers.get('Content-Security-Policy', ''))


if __name__ == '__main__':
    unittest.main()
