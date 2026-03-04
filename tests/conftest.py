"""
Patch OAuth2Session before any test module imports absens_demo.requests.
The module runs OAuth token-fetching at import time, so we intercept it here.
"""
from unittest.mock import MagicMock, patch

_mock_oauth = MagicMock()
_mock_oauth.fetch_token.return_value = {"access_token": "test_token"}

with patch("requests_oauthlib.OAuth2Session", return_value=_mock_oauth):
    import absens_demo.requests  # noqa: F401 — force import while OAuth is mocked
