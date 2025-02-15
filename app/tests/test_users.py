import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_create_user(client):
    response = await client.post(
        "/users/signup/",
        json={
            "full_name": "Test User",
            "username": "test_user",
            "password": "test_password",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "full_name": "Test User",
        "username": "test_user",
        "id": response.json()["id"],
    }


@pytest.mark.asyncio(loop_scope="session")
async def test_login_for_access_token(client, create_test_user):
    response = await client.post(
        "/users/signin/",
        json={"username": f"{create_test_user.username}", "password": "test_password"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert response.json()["token_type"] == "bearer"
