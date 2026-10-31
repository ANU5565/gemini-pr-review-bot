import asyncio
import hashlib
import hmac
import json
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
        return json.loads(self._body)


class WebhookAuthenticationTests(unittest.TestCase):
    secret = "test-secret"
    body = json.dumps(
        {
            "action": "opened",
            "repository": {"full_name": "example/repository"},
            "pull_request": {"number": 42},
        },
        separators=(",", ":"),
    ).encode()

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

        self.assertEqual(
            response,
            {
                "status": "accepted",
                "event": "pull_request",
                "action": "opened",
            },
        )
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

    def test_unsupported_event_is_ignored(self):
        body = b'{"action":"created"}'
        with self.assertLogs("app", level=logging.INFO) as logs:
            response = asyncio.run(
                github_webhook(
                    FakeRequest(
                        body,
                        self.signature_for(body),
                        {"x-github-event": "issues"},
                    )
                )
            )

        self.assertEqual(
            response,
            {"status": "ignored", "reason": "unsupported_event"},
        )
        self.assertIn("Ignoring unsupported", logs.output[0])

    def test_malformed_json_is_rejected(self):
        body = b"{not-json"
        with self.assertRaises(HTTPException) as context:
            asyncio.run(
                github_webhook(
                    FakeRequest(body, self.signature_for(body), {"x-github-event": "pull_request"})
                )
            )

        self.assertEqual(context.exception.status_code, 400)

    def test_invalid_pull_request_payload_is_rejected(self):
        body = b'{"action":"opened","repository":{"full_name":"example/repository"}}'
        with self.assertRaises(HTTPException) as context:
            asyncio.run(
                github_webhook(
                    FakeRequest(body, self.signature_for(body), {"x-github-event": "pull_request"})
                )
            )

        self.assertEqual(context.exception.status_code, 400)

    def signature_for(self, body):
        digest = hmac.new(
            self.secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={digest}"
