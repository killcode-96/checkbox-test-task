import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_get_receipt_public(client, create_test_receipt):
    public_url = create_test_receipt["public_url"]
    response = await client.get(public_url)
    assert response.status_code == 200
