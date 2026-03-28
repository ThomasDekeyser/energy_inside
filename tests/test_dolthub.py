import json
from unittest.mock import patch, Mock
from energy_inside.dolthub import DoltHubClient


def _mock_post_response(operation_name="operations/test-uuid"):
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {
        "query_execution_status": "Success",
        "operation_name": operation_name,
    }
    resp.raise_for_status = Mock()
    return resp


def _mock_poll_response(done=True):
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {
        "_id": "operations/test-uuid",
        "done": done,
        "res_details": {
            "query_execution_status": "Success",
        },
    }
    resp.raise_for_status = Mock()
    return resp


@patch("energy_inside.dolthub.requests")
def test_execute_write(mock_requests):
    mock_requests.post.return_value = _mock_post_response()
    mock_requests.get.return_value = _mock_poll_response(done=True)

    client = DoltHubClient(
        token="test-token", owner="testowner", repo="testrepo"
    )
    result = client.execute_write("INSERT INTO t VALUES (1)")

    # Verify POST was called with correct URL and headers
    call_args = mock_requests.post.call_args
    assert "testowner/testrepo/write/main/main" in call_args[0][0]
    assert call_args[1]["headers"]["authorization"] == "token test-token"
    assert call_args[1]["json"]["query"] == "INSERT INTO t VALUES (1)"

    # Verify poll was called
    poll_args = mock_requests.get.call_args
    assert "operationName=operations/test-uuid" in poll_args[0][0] or \
           poll_args[1].get("params", {}).get("operationName") == "operations/test-uuid"

    assert result["res_details"]["query_execution_status"] == "Success"


@patch("energy_inside.dolthub.time")
@patch("energy_inside.dolthub.requests")
def test_execute_write_polls_until_done(mock_requests, mock_time):
    mock_time.monotonic.side_effect = [0, 0, 1, 2]  # start, check, check, check
    mock_time.sleep = Mock()

    mock_requests.post.return_value = _mock_post_response()
    mock_requests.get.side_effect = [
        _mock_poll_response(done=False),
        _mock_poll_response(done=True),
    ]

    client = DoltHubClient(token="t", owner="o", repo="r")
    result = client.execute_write("INSERT INTO t VALUES (1)")

    assert mock_requests.get.call_count == 2
    assert result["done"] is True
