import asyncio
import hashlib
import hmac
import logging
import os
import unittest

from fastapi import HTTPException

from app import github_webhook


class FakeRequest:
    def __init__(self, body, signature=None, headers=None):
        self._body = body
        self.headers = {}
        if signature is not None:
            self.headers["x-hub-signature-256"] = signature
        if headers:
            self.headers.update(headers)

    async def body(self):
        return self._body

    async def json(self):
        return {
            "action": "opened",
            "repository": {"full_name": "example/repository"},
        }


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
        with self.assertLogs("app", level=logging.INFO) as logs:
            response = asyncio.run(
                github_webhook(
                    FakeRequest(
                        self.body,
                        self.signature(),
                        {
                            "x-github-delivery": "delivery-123",
                            "x-github-event": "pull_request",
                        },
                    )
                )
            )

        self.assertEqual(response, {"status": "received"})
        self.assertIn("GitHub webhook received", logs.output[0])
        self.assertIn("delivery-123", logs.output[0])
        self.assertIn("pull_request", logs.output[0])
        self.assertIn("example/repository", logs.output[0])
        self.assertNotIn(self.body.decode(), logs.output[0])

    def test_missing_signature_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            asyncio.run(github_webhook(FakeRequest(self.body)))

        self.assertEqual(context.exception.status_code, 401)
    def test_invalid_signature_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            asyncio.run(github_webhook(FakeRequest(self.body, "sha256=invalid")))

        self.assertEqual(context.exception.status_code, 401)
