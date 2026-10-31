import asyncio
import hashlib
import hmac
import os
import unittest

from fastapi import HTTPException

from app import github_webhook


class FakeRequest:
    def __init__(self, body, signature=None):
        self._body = body
        self.headers = {}
        if signature is not None:
            self.headers["x-hub-signature-256"] = signature

    async def body(self):
        return self._body

    async def json(self):
        return {"action": "opened"}


class WebhookAuthenticationTests(unittest.TestCase):
    secret = "test-secret"
    body = b'{"action":"opened"}'

    def setUp(self):
        os.environ["GITHUB_WEBHOOK_SECRET"] = self.secret

    def tearDown(self):
        os.environ.pop("GITHUB_WEBHOOK_SECRET", None)

    def signature(self):
        digest = hmac.new(
            self.secret.encode("utf-8"),
            self.body,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={digest}"

    def test_valid_signature_is_accepted(self):
        response = asyncio.run(
            github_webhook(FakeRequest(self.body, self.signature()))
        )

        self.assertEqual(response, {"status": "received"})

    def test_missing_signature_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            asyncio.run(github_webhook(FakeRequest(self.body)))

        self.assertEqual(context.exception.status_code, 401)
    def test_invalid_signature_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            asyncio.run(github_webhook(FakeRequest(self.body, "sha256=invalid")))

        self.assertEqual(context.exception.status_code, 401)
