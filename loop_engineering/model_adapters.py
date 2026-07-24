"""Explicit, testable HTTPS adapter for external loop-decision models."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .policies import Decision


class ModelAdapterError(ValueError):
    """Raised when a model endpoint or response violates the adapter contract."""


@dataclass(frozen=True)
class HttpResponse:
    """A small, transport-independent HTTP response boundary."""

    status_code: int
    body: str


class HttpTransport(Protocol):
    """Posts JSON without coupling the adapter to a particular HTTP library."""

    def post_json(
        self,
        endpoint: str,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> HttpResponse:
        """Return the status and body for one JSON request."""


class UrllibHttpTransport:
    """Standard-library transport used only when callers do not inject one."""

    def post_json(
        self,
        endpoint: str,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> HttpResponse:
        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                return HttpResponse(response.status, response.read().decode("utf-8"))
        except HTTPError as error:
            return HttpResponse(error.code, error.read().decode("utf-8"))


class HttpModelAdapter:
    """Translate one explicit HTTPS JSON model call into a loop Decision."""

    def __init__(
        self,
        endpoint: str,
        model: str,
        api_key: str,
        transport: HttpTransport | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        if not endpoint.startswith("https://"):
            raise ModelAdapterError("Model endpoint must use HTTPS")
        if not model.strip():
            raise ModelAdapterError("model name must not be empty")
        if timeout_seconds <= 0:
            raise ModelAdapterError("Model timeout must be positive")

        self.endpoint = endpoint
        self.model = model
        self.api_key = api_key
        self.transport = transport if transport is not None else UrllibHttpTransport()
        self.timeout_seconds = timeout_seconds

    def complete(self, input_payload: dict[str, object]) -> Decision:
        """Request and strictly decode one model-supplied loop decision."""

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        response = self.transport.post_json(
            self.endpoint,
            headers,
            {"model": self.model, "input": input_payload},
            self.timeout_seconds,
        )
        if not 200 <= response.status_code < 300:
            raise ModelAdapterError(
                f"Model request returned HTTP status {response.status_code}"
            )
        try:
            payload = json.loads(response.body)
        except json.JSONDecodeError as error:
            raise ModelAdapterError("Model response was not valid JSON") from error
        return self._decision_from_payload(payload)

    @staticmethod
    def _decision_from_payload(payload: object) -> Decision:
        if not isinstance(payload, dict):
            raise ModelAdapterError("Model response must be a JSON object")
        name = payload.get("name")
        parameters = payload.get("parameters")
        if not isinstance(name, str) or not name:
            raise ModelAdapterError("Model response requires a non-empty name")
        if not isinstance(parameters, dict):
            raise ModelAdapterError("Model response requires object parameters")

        numeric_parameters: dict[str, float] = {}
        for key, value in parameters.items():
            if (
                not isinstance(key, str)
                or isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ModelAdapterError(
                    "Model response parameters must use string keys and finite numbers"
                )
            numeric_parameters[key] = float(value)
        return Decision(name=name, parameters=numeric_parameters)
