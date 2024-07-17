import pytest
from moovitamix_data_connector.moovitamix_api_connector import MoovitamixApiConnector


@pytest.mark.parametrize(
    "dummy_moovitamix_api_connector, expected",
    [
        # working url
        (
            MoovitamixApiConnector(base_url="https://example.com", api_key=None), True
        ),
        # non working url
        (
            MoovitamixApiConnector(base_url="https://thisisanonexistenturl.com", api_key=None), False
        )
    ],
    ids=["working url", "non working url"]
)
def test_check_connection(dummy_moovitamix_api_connector: MoovitamixApiConnector, expected: bool):
    actual = dummy_moovitamix_api_connector.check_connection()
    assert actual is expected
