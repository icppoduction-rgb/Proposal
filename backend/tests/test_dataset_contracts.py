from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import pandas as pd


def _login(client):
    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123456"})
    return response.json()["access_token"]


def _raw_root() -> Path:
    return Path.cwd() / "test-data" / "raw"


def _sync_raw_file(client, token: str, relative_path: str) -> dict:
    response = client.get("/api/datasets/raw-files", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    return next(item for item in response.json() if item["relative_path"] == relative_path)


def test_dataset_registration_and_validation_dispatch(client):
    token = _login(client)
    manifest = {
        "name": "Demo Network Dataset",
        "source_type": "network",
        "file_name": "network.csv",
        "required_columns": ["feature_a", "feature_b"],
        "label_column": "label",
        "timestamp_column": "event_ts",
        "entity_id_column": "entity_id",
        "feature_families": ["network_flow"],
        "mitre_mapping": {},
        "lineage": {"source": "synthetic"},
    }
    upload = client.post(
        "/api/datasets/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"manifest_json": json.dumps(manifest)},
        files={"file": ("network.csv", BytesIO(b"entity_id,event_ts,feature_a,feature_b,label\n1,2026-01-01,1,2,0\n"), "text/csv")},
    )
    assert upload.status_code == 201
    dataset_id = upload.json()["id"]
    validate = client.post(f"/api/datasets/{dataset_id}/validate", headers={"Authorization": f"Bearer {token}"})
    assert validate.status_code == 200
    assert validate.json()["object_id"] == dataset_id


def test_legacy_upload_rejects_existing_file_and_duplicate_dataset_name(client):
    token = _login(client)
    raw_root = _raw_root()
    existing_path = raw_root / "legacy.csv"
    existing_path.write_text("entity_id,event_ts,label\n1,2026-01-01,0\n", encoding="utf-8")

    manifest = {
        "name": "Legacy upload dataset",
        "source_type": "network",
        "file_name": "legacy.csv",
        "required_columns": ["feature_a"],
        "label_column": "label",
        "timestamp_column": "event_ts",
        "entity_id_column": "entity_id",
        "feature_families": ["network_flow"],
        "mitre_mapping": {},
        "lineage": {"source": "legacy-upload"},
    }

    existing_file_upload = client.post(
        "/api/datasets/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"manifest_json": json.dumps(manifest)},
        files={"file": ("legacy.csv", BytesIO(b"entity_id,event_ts,feature_a,label\n1,2026-01-01,1,0\n"), "text/csv")},
    )
    assert existing_file_upload.status_code == 409
    assert "already exists" in existing_file_upload.json()["detail"]

    first_upload = client.post(
        "/api/datasets/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"manifest_json": json.dumps({**manifest, "file_name": "legacy-first.csv"})},
        files={"file": ("legacy-first.csv", BytesIO(b"entity_id,event_ts,feature_a,label\n1,2026-01-01,1,0\n"), "text/csv")},
    )
    assert first_upload.status_code == 201

    duplicate_name_upload = client.post(
        "/api/datasets/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"manifest_json": json.dumps({**manifest, "file_name": "legacy-second.csv"})},
        files={"file": ("legacy-second.csv", BytesIO(b"entity_id,event_ts,feature_a,label\n2,2026-01-02,2,1\n"), "text/csv")},
    )
    assert duplicate_name_upload.status_code == 409
    assert "name already exists" in duplicate_name_upload.json()["detail"]


def test_legacy_register_requires_existing_raw_file_and_blocks_duplicates(client):
    token = _login(client)
    raw_root = _raw_root()

    missing_payload = {
        "name": "Legacy register dataset",
        "source_type": "host",
        "file_name": "missing.csv",
        "required_columns": ["metric"],
        "label_column": "label",
        "timestamp_column": "event_ts",
        "entity_id_column": "entity_id",
        "feature_families": ["process"],
        "mitre_mapping": {},
        "lineage": {"source": "legacy-register"},
    }

    missing = client.post("/api/datasets/register", headers={"Authorization": f"Bearer {token}"}, json=missing_payload)
    assert missing.status_code == 409
    assert "does not exist" in missing.json()["detail"]

    (raw_root / "registered.csv").write_text("entity_id,event_ts,metric,label\n1,2026-01-01,10,0\n", encoding="utf-8")
    created = client.post(
        "/api/datasets/register",
        headers={"Authorization": f"Bearer {token}"},
        json={**missing_payload, "file_name": "registered.csv"},
    )
    assert created.status_code == 201

    synced_raw_file = _sync_raw_file(client, token, "registered.csv")
    assert Path(synced_raw_file["path"]).resolve() == (raw_root / "registered.csv").resolve()

    (raw_root / "registered-copy.csv").write_text("entity_id,event_ts,metric,label\n2,2026-01-02,11,1\n", encoding="utf-8")
    duplicate_name = client.post(
        "/api/datasets/register",
        headers={"Authorization": f"Bearer {token}"},
        json={**missing_payload, "file_name": "registered-copy.csv"},
    )
    assert duplicate_name.status_code == 409
    assert "name already exists" in duplicate_name.json()["detail"]

    duplicate_path = client.post(
        "/api/datasets/register",
        headers={"Authorization": f"Bearer {token}"},
        json={**missing_payload, "name": "Legacy register dataset copy", "file_name": "registered.csv"},
    )
    assert duplicate_path.status_code == 409
    assert "raw file already exists" in duplicate_path.json()["detail"]


def test_upload_session_rejects_limit_and_conflict(client):
    token = _login(client)
    existing = _raw_root() / "already-there.csv"
    existing.write_text("entity_id,event_ts,label\n1,2026-01-01,0\n", encoding="utf-8")

    oversized = client.post(
        "/api/datasets/uploads/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"files": [{"relative_path": "huge.csv", "size_bytes": 100 * 1024 * 1024 * 1024 + 1, "content_type": "text/csv"}]},
    )
    assert oversized.status_code == 400
    assert "100 GB" in oversized.json()["detail"]

    conflict = client.post(
        "/api/datasets/uploads/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"files": [{"relative_path": "already-there.csv", "size_bytes": 10, "content_type": "text/csv"}]},
    )
    assert conflict.status_code == 409


def test_upload_session_saves_nested_raw_files(client):
    token = _login(client)
    relative_path = "customers/2026/customers.csv"
    payload = b"entity_id,event_ts,feature_a,feature_b,label\n1,2026-01-01,1,2,0\n"

    session = client.post(
        "/api/datasets/uploads/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"files": [{"relative_path": relative_path, "size_bytes": len(payload), "content_type": "text/csv"}]},
    )
    assert session.status_code == 201
    session_payload = session.json()
    file_id = session_payload["files"][0]["file_id"]

    upload = client.put(
        f"/api/datasets/uploads/sessions/{session_payload['session_id']}/files/{file_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Chunk-Offset": "0",
            "X-Chunk-Length": str(len(payload)),
            "Content-Type": "application/octet-stream",
        },
        content=payload,
    )
    assert upload.status_code == 200
    assert upload.json()["uploaded_bytes"] == len(payload)

    complete = client.post(
        f"/api/datasets/uploads/sessions/{session_payload['session_id']}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert complete.status_code == 200
    complete_payload = complete.json()
    assert complete_payload["uploaded_files"][0]["relative_path"] == relative_path
    assert any(item["relative_path"] == relative_path for item in complete_payload["raw_files"])
    assert (_raw_root() / "customers" / "2026" / "customers.csv").exists()


def test_upload_session_accepts_res_and_sc_extensions(client):
    token = _login(client)

    session = client.post(
        "/api/datasets/uploads/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "files": [
                {"relative_path": "host/sample.res", "size_bytes": 32, "content_type": "text/plain"},
                {"relative_path": "host/sample.sc", "size_bytes": 64, "content_type": "text/plain"},
            ]
        },
    )
    assert session.status_code == 201
    payload = session.json()
    assert [item["relative_path"] for item in payload["files"]] == ["host/sample.res", "host/sample.sc"]


def test_upload_session_can_be_discarded_after_partial_progress(client):
    token = _login(client)
    relative_path = "incoming/partial.csv"
    payload = b"entity_id,event_ts,label\n1,2026-01-01,0\n"

    session = client.post(
        "/api/datasets/uploads/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"files": [{"relative_path": relative_path, "size_bytes": len(payload), "content_type": "text/csv"}]},
    )
    assert session.status_code == 201
    session_payload = session.json()
    file_id = session_payload["files"][0]["file_id"]
    first_chunk = payload[:10]

    upload = client.put(
        f"/api/datasets/uploads/sessions/{session_payload['session_id']}/files/{file_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Chunk-Offset": "0",
            "X-Chunk-Length": str(len(first_chunk)),
            "Content-Type": "application/octet-stream",
        },
        content=first_chunk,
    )
    assert upload.status_code == 200

    discard = client.delete(
        f"/api/datasets/uploads/sessions/{session_payload['session_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert discard.status_code == 204

    complete = client.post(
        f"/api/datasets/uploads/sessions/{session_payload['session_id']}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert complete.status_code == 404
    assert not (_raw_root() / "incoming" / "partial.csv").exists()


def test_raw_files_listing_and_inspection_support_multiple_formats(client):
    token = _login(client)
    root = _raw_root()
    frame = pd.DataFrame(
        [
            {
                "entity_id": "host-1",
                "event_ts": "2026-01-01T00:00:00",
                "feature_a": 1.0,
                "feature_b": 2.0,
                "label": 1,
            }
        ]
    )
    frame.to_csv(root / "sample.csv", index=False)
    frame.to_csv(root / "sample.tsv", index=False, sep="\t")
    frame.to_parquet(root / "sample.parquet", index=False)
    frame.to_excel(root / "sample.xlsx", index=False)
    (root / "sample.res").write_text(
        "timestamp,cpu_usage,memory_usage,network_received,network_send,storage_read,storage_written\n"
        "1631256556.235,0.25,19312640,15259,15259,378674,18613\n",
        encoding="utf-8",
    )
    (root / "sample.sc").write_text(
        "1631256556434973186 0 30852 apache2 30852 select < res=0 exe=apache2\n"
        "1631256556435833391 0 30852 apache2 30852 clone < res=34 exe=apache2 tid=30853 pid=30852\n",
        encoding="utf-8",
    )

    listed = client.get("/api/datasets/raw-files", headers={"Authorization": f"Bearer {token}"})
    assert listed.status_code == 200
    listed_formats = {item["relative_path"]: item["format"] for item in listed.json()}
    assert listed_formats["sample.csv"] == "csv"
    assert listed_formats["sample.tsv"] == "tsv"
    assert listed_formats["sample.parquet"] == "parquet"
    assert listed_formats["sample.xlsx"] == "xlsx"
    assert listed_formats["sample.res"] == "res"
    assert listed_formats["sample.sc"] == "sc"

    for relative_path in ("sample.csv", "sample.tsv", "sample.parquet", "sample.xlsx"):
        inspect = client.post(
            "/api/datasets/raw-files/inspect",
            headers={"Authorization": f"Bearer {token}"},
            json={"relative_path": relative_path},
        )
        assert inspect.status_code == 200
        payload = inspect.json()
        assert payload["columns"] == ["entity_id", "event_ts", "feature_a", "feature_b", "label"]
        assert payload["suggested_name"].startswith("sample")
        assert "normalization_profile" in payload
        assert "target_columns" in payload

    res_inspect = client.post(
        "/api/datasets/raw-files/inspect",
        headers={"Authorization": f"Bearer {token}"},
        json={"relative_path": "sample.res"},
    )
    assert res_inspect.status_code == 200
    assert res_inspect.json()["columns"] == [
        "timestamp",
        "cpu_usage",
        "memory_usage",
        "network_received",
        "network_send",
        "storage_read",
        "storage_written",
    ]

    sc_inspect = client.post(
        "/api/datasets/raw-files/inspect",
        headers={"Authorization": f"Bearer {token}"},
        json={"relative_path": "sample.sc"},
    )
    assert sc_inspect.status_code == 200
    assert {"timestamp_ns", "process_name", "syscall", "event_ts", "entity_id"} <= set(sc_inspect.json()["columns"])


def test_managed_dataset_registration_persists_feature_set_and_blocks_duplicate_name(client):
    token = _login(client)
    raw_root = _raw_root()
    raw_file_path = raw_root / "managed.csv"
    raw_file_path.write_text("entity_id,event_ts,label\n1,2026-01-01,0\n", encoding="utf-8")

    raw_file = _sync_raw_file(client, token, "managed.csv")
    payload = {
        "name": "Managed telemetry",
        "raw_file_id": raw_file["id"],
        "feature_set": ["network_flow", "dns"],
    }

    created = client.post("/api/datasets/management", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert created.status_code == 201
    created_payload = created.json()
    assert created_payload["name"] == payload["name"]
    assert created_payload["raw_file_id"] == raw_file["id"]
    assert created_payload["feature_set"] == ["dns", "network_flow"]
    assert Path(created_payload["file_path"]).resolve() == raw_file_path.resolve()

    listed = client.get("/api/datasets/management", headers={"Authorization": f"Bearer {token}"})
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    duplicate = client.post("/api/datasets/management", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert duplicate.status_code == 409
    assert "already exists" in duplicate.json()["detail"]


def test_managed_dataset_delete_and_clear_operations(client):
    token = _login(client)
    raw_root = _raw_root()
    (raw_root / "one.csv").write_text("entity_id,event_ts,label\n1,2026-01-01,0\n", encoding="utf-8")
    (raw_root / "two.csv").write_text("entity_id,event_ts,label\n2,2026-01-02,1\n", encoding="utf-8")

    first_raw = _sync_raw_file(client, token, "one.csv")
    second_raw = _sync_raw_file(client, token, "two.csv")

    first = client.post(
        "/api/datasets/management",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "One", "raw_file_id": first_raw["id"], "feature_set": ["process"]},
    )
    second = client.post(
        "/api/datasets/management",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Two", "raw_file_id": second_raw["id"], "feature_set": ["dns"]},
    )
    assert first.status_code == 201
    assert second.status_code == 201

    deleted = client.delete(
        f"/api/datasets/management/{first.json()['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert deleted.status_code == 200

    listed_after_delete = client.get("/api/datasets/management", headers={"Authorization": f"Bearer {token}"})
    assert listed_after_delete.status_code == 200
    assert [item["name"] for item in listed_after_delete.json()] == ["Two"]

    cleared = client.delete("/api/datasets/management", headers={"Authorization": f"Bearer {token}"})
    assert cleared.status_code == 200

    final_list = client.get("/api/datasets/management", headers={"Authorization": f"Bearer {token}"})
    assert final_list.status_code == 200
    assert final_list.json() == []


def test_managed_dataset_validation_creates_legacy_dataset_and_dispatches_task(client):
    token = _login(client)
    raw_root = _raw_root()
    raw_file_path = raw_root / "validate-me.csv"
    raw_file_path.write_text("entity_id,event_ts,label,feature_a\n1,2026-01-01,0,10\n", encoding="utf-8")

    raw_file = _sync_raw_file(client, token, "validate-me.csv")
    registered = client.post(
        "/api/datasets/management",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Validation dataset", "raw_file_id": raw_file["id"], "feature_set": ["network_flow", "dns"]},
    )
    assert registered.status_code == 201
    managed_dataset = registered.json()

    validation = client.post(
        f"/api/datasets/management/{managed_dataset['id']}/validate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert validation.status_code == 200
    assert validation.json()["task_name"] == "normalization.validate_dataset"

    legacy_list = client.get("/api/datasets", headers={"Authorization": f"Bearer {token}"})
    assert legacy_list.status_code == 200
    matching = [item for item in legacy_list.json() if item["name"] == "Validation dataset"]
    assert len(matching) == 1
    assert Path(matching[0]["storage_path"]).resolve() == raw_file_path.resolve()
    assert matching[0]["lineage"]["managed_dataset_id"] == managed_dataset["id"]


def test_raw_file_delete_is_blocked_when_managed_dataset_references_it(client):
    token = _login(client)
    raw_root = _raw_root()
    raw_file_path = raw_root / "protected.csv"
    raw_file_path.write_text("entity_id,event_ts,label\n1,2026-01-01,0\n", encoding="utf-8")

    raw_file = _sync_raw_file(client, token, "protected.csv")
    registered = client.post(
        "/api/datasets/management",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Protected dataset", "raw_file_id": raw_file["id"], "feature_set": ["network_flow"]},
    )
    assert registered.status_code == 201

    delete_single = client.delete(f"/api/datasets/raw-files/{raw_file['id']}", headers={"Authorization": f"Bearer {token}"})
    assert delete_single.status_code == 409
    assert "referenced" in delete_single.json()["detail"]

    delete_all = client.delete("/api/datasets/raw-files", headers={"Authorization": f"Bearer {token}"})
    assert delete_all.status_code == 409
    assert "registered datasets" in delete_all.json()["detail"]
    assert raw_file_path.exists()
