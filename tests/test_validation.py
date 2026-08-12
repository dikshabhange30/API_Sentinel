from app.schemas import APIRequestCreate
import pytest


def test_valid_api_request():
    request = APIRequestCreate(
        endpoint="/test",
        response_time=120.5,
        method="GET",
        status_code=200,
        ip_address="127.0.0.1"
    )

    assert request.endpoint == "/test"
    assert request.response_time == 120.5
    assert request.method == "GET"
    assert request.status_code == 200
    assert request.ip_address == "127.0.0.1"

def test_negative_response_time():
    with pytest.raises(ValueError):
        APIRequestCreate(
            endpoint="/test",
            response_time=-50,
            method="GET",
            status_code=200,
            ip_address="127.0.0.1"
        )

def test_invalid_status_code():
    with pytest.raises(ValueError):
        APIRequestCreate(
            endpoint="/test",
            response_time=120.5,
            method="GET",
            status_code=700,
            ip_address="127.0.0.1"
        )

def test_empty_endpoint():
    with pytest.raises(ValueError):
        APIRequestCreate(
            endpoint="",
            response_time=120.5,
            method="GET",
            status_code=200,
            ip_address="127.0.0.1"
        )

def test_invalid_method():
    with pytest.raises(ValueError):
        APIRequestCreate(
            endpoint="/test",
            response_time=120.5,
            method="BANANA",
            status_code=200,
            ip_address="127.0.0.1"
        )