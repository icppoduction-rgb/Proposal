from __future__ import annotations


def test_get_ru_language_pack(client):
    response = client.get("/api/i18n/ru")

    assert response.status_code == 200
    payload = response.json()
    assert payload["nav"]["overview"]
    assert payload["login"]["language"]["ru"] == "RU"
