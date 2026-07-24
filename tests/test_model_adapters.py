import pytest

from loop_engineering.model_adapters import (
    HttpModelAdapter,
    HttpResponse,
    ModelAdapterError,
)


class FakeTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def post_json(self, endpoint, headers, payload, timeout_seconds):
        self.calls.append(
            {
                "endpoint": endpoint,
                "headers": headers,
                "payload": payload,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.response


def test_adapter_posts_explicit_json_and_optional_authorization() -> None:
    transport = FakeTransport(
        HttpResponse(200, '{"name": "increment", "parameters": {"amount": 2}}')
    )
    adapter = HttpModelAdapter(
        "https://models.example.test/decide",
        "study-model",
        "secret-value",
        transport,
        timeout_seconds=3.0,
    )

    decision = adapter.complete({"state": {"goal": 2.0}})

    assert decision.name == "increment"
    assert decision.parameters == {"amount": 2.0}
    assert transport.calls == [
        {
            "endpoint": "https://models.example.test/decide",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer secret-value",
            },
            "payload": {"model": "study-model", "input": {"state": {"goal": 2.0}}},
            "timeout_seconds": 3.0,
        }
    ]


def test_adapter_omits_authorization_without_key() -> None:
    transport = FakeTransport(
        HttpResponse(200, '{"name": "increment", "parameters": {"amount": 1}}')
    )
    adapter = HttpModelAdapter("https://models.example.test", "model", "", transport)

    adapter.complete({})

    assert transport.calls[0]["headers"] == {"Content-Type": "application/json"}


def test_adapter_rejects_insecure_endpoint_and_invalid_model_or_timeout() -> None:
    with pytest.raises(ModelAdapterError, match="HTTPS"):
        HttpModelAdapter("http://models.example.test", "model", "")
    with pytest.raises(ModelAdapterError, match="model"):
        HttpModelAdapter("https://models.example.test", "", "")
    with pytest.raises(ModelAdapterError, match="timeout"):
        HttpModelAdapter("https://models.example.test", "model", "", timeout_seconds=0)


@pytest.mark.parametrize(
    "response",
    [
        HttpResponse(500, "service failed"),
        HttpResponse(200, "not-json"),
        HttpResponse(200, '{"name": "", "parameters": {}}'),
        HttpResponse(200, '{"name": "increment", "parameters": {"amount": true}}'),
    ],
)
def test_adapter_rejects_invalid_responses_without_exposing_key(response) -> None:
    adapter = HttpModelAdapter(
        "https://models.example.test",
        "model",
        "secret-value",
        FakeTransport(response),
    )

    with pytest.raises(ModelAdapterError) as error:
        adapter.complete({})

    assert "secret-value" not in str(error.value)

