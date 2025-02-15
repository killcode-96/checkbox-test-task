import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_create_receipt(client, auth_header):
    response = await client.post(
        "/receipts/",
        json={
            "products": [
                {"name": "Product 1", "price": 10.0, "quantity": 2},
                {"name": "Product 2", "price": 20.0, "quantity": 1},
            ],
            "payment": {"type": "cash", "amount": 40.0},
        },
        headers=auth_header,
    )
    assert response.status_code == 200


@pytest.mark.asyncio(loop_scope="session")
async def test_list_receipts(client, auth_header, create_test_receipt):
    response = await client.get("/receipts/", headers=auth_header)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_get_receipt(client, auth_header, create_test_receipt):
    receipt_id = create_test_receipt["id"]

    response = await client.get(f"/receipts/{receipt_id}/", headers=auth_header)
    assert response.status_code == 200
    assert response.json()["id"] == receipt_id
