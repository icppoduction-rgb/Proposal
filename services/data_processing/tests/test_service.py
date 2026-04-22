from __future__ import annotations

import json
import os
import socket
import time
from pathlib import Path

import dpkt
import pandas as pd
from fastapi.testclient import TestClient

from cybersec_platform.db.session import get_settings


def _build_client(tmp_path: Path) -> TestClient:
    raw_root = tmp_path / "raw"
    tmp_root = tmp_path / "tmp"
    raw_root.mkdir(parents=True, exist_ok=True)
    tmp_root.mkdir(parents=True, exist_ok=True)
    os.environ["RAW_DATA_PATH"] = str(raw_root)
    os.environ["TMP_PATH"] = str(tmp_root)
    get_settings.cache_clear()

    from services.data_processing.app.main import app

    return TestClient(app)


def _write_pcap(path: Path) -> None:
    dns = dpkt.dns.DNS(id=1)
    dns.qd = [dpkt.dns.DNS.Q(name="example.com")]
    udp = dpkt.udp.UDP(sport=5353, dport=53, data=bytes(dns))
    udp.ulen = len(udp)
    ip = dpkt.ip.IP(
        src=socket.inet_aton("10.0.0.1"),
        dst=socket.inet_aton("8.8.8.8"),
        p=dpkt.ip.IP_PROTO_UDP,
        ttl=64,
    )
    ip.data = udp
    ip.len = len(ip)
    ethernet = dpkt.ethernet.Ethernet(
        src=b"\xaa\xaa\xaa\xaa\xaa\xaa",
        dst=b"\xbb\xbb\xbb\xbb\xbb\xbb",
        type=dpkt.ethernet.ETH_TYPE_IP,
        data=ip,
    )

    with path.open("wb") as file:
        writer = dpkt.pcap.Writer(file)
        writer.writepkt(bytes(ethernet), ts=time.time())


def test_csv_editor_supports_patch_delete_and_save(tmp_path: Path):
    client = _build_client(tmp_path)
    csv_path = Path(os.environ["RAW_DATA_PATH"]) / "sample.csv"
    csv_path.write_text("name,score,flag\nalice,1,true\nbob,2,false\n", encoding="utf-8")

    created = client.post("/editor-sessions", json={"file_path": str(csv_path), "page_size": 10})
    assert created.status_code == 201
    session_id = created.json()["session_id"]

    page = client.get(f"/editor-sessions/{session_id}", params={"page": 1})
    assert page.status_code == 200
    assert page.json()["rows"][0]["values"]["name"] == "alice"

    patched = client.patch(
        f"/editor-sessions/{session_id}/cells",
        json={"patches": [{"row_index": 0, "column": "score", "value": "42"}]},
    )
    assert patched.status_code == 200

    deleted_rows = client.post(f"/editor-sessions/{session_id}/rows/delete", json={"row_indices": [1]})
    assert deleted_rows.status_code == 200

    deleted_columns = client.post(f"/editor-sessions/{session_id}/columns/delete", json={"columns": ["flag"]})
    assert deleted_columns.status_code == 200

    saved = client.post(f"/editor-sessions/{session_id}/save")
    assert saved.status_code == 200
    assert saved.json()["row_count"] == 1

    content = csv_path.read_text(encoding="utf-8").splitlines()
    assert content == ["name,score", "alice,42"]


def test_res_editor_supports_patch_and_save(tmp_path: Path):
    client = _build_client(tmp_path)
    res_path = Path(os.environ["RAW_DATA_PATH"]) / "sample.res"
    res_path.write_text(
        "timestamp,cpu_usage,memory_usage\n1631256556.235,0.25,19312640\n1631256557.235,0.50,19312641\n",
        encoding="utf-8",
    )

    created = client.post("/editor-sessions", json={"file_path": str(res_path), "page_size": 10})
    assert created.status_code == 201
    assert created.json()["dataset_format"] == "res"
    assert created.json()["read_only"] is False
    session_id = created.json()["session_id"]

    patched = client.patch(
        f"/editor-sessions/{session_id}/cells",
        json={"patches": [{"row_index": 0, "column": "cpu_usage", "value": "0.75"}]},
    )
    assert patched.status_code == 200

    saved = client.post(f"/editor-sessions/{session_id}/save")
    assert saved.status_code == 200

    content = res_path.read_text(encoding="utf-8").splitlines()
    assert content[0] == "timestamp,cpu_usage,memory_usage"
    assert content[1] == "1631256556.235,0.75,19312640"


def test_preview_supports_parquet_xlsx_json_and_sheet_switch(tmp_path: Path):
    client = _build_client(tmp_path)
    raw_root = Path(os.environ["RAW_DATA_PATH"])

    frame = pd.DataFrame([{"name": "alice", "score": 1}, {"name": "bob", "score": 2}])
    parquet_path = raw_root / "sample.parquet"
    frame.to_parquet(parquet_path, index=False)

    workbook_path = raw_root / "sample.xlsx"
    with pd.ExcelWriter(workbook_path) as writer:
        frame.to_excel(writer, sheet_name="First", index=False)
        pd.DataFrame([{"event": "login", "count": 3}]).to_excel(writer, sheet_name="Second", index=False)

    json_path = raw_root / "sample.json"
    json_path.write_text(json.dumps([{"name": "alice", "score": 1}, {"name": "bob", "score": 2}]), encoding="utf-8")

    for target_path, expected_format in (
        (parquet_path, "parquet"),
        (json_path, "json"),
    ):
        response = client.post("/editor-sessions", json={"file_path": str(target_path), "page_size": 10})
        assert response.status_code == 201
        session_id = response.json()["session_id"]
        page = client.get(f"/editor-sessions/{session_id}", params={"page": 1})
        assert page.status_code == 200
        assert page.json()["dataset_format"] == expected_format
        assert page.json()["rows"][0]["values"]["name"] == "alice"

    workbook_session = client.post("/editor-sessions", json={"file_path": str(workbook_path), "page_size": 10})
    assert workbook_session.status_code == 201
    session_id = workbook_session.json()["session_id"]

    first_sheet = client.get(f"/editor-sessions/{session_id}", params={"page": 1})
    assert first_sheet.status_code == 200
    assert first_sheet.json()["active_sheet"] == "First"
    assert first_sheet.json()["rows"][0]["values"]["name"] == "alice"

    second_sheet = client.get(f"/editor-sessions/{session_id}", params={"page": 1, "sheet_name": "Second"})
    assert second_sheet.status_code == 200
    assert second_sheet.json()["active_sheet"] == "Second"
    assert second_sheet.json()["rows"][0]["values"]["event"] == "login"


def test_json_ndjson_and_nested_rejection(tmp_path: Path):
    client = _build_client(tmp_path)
    raw_root = Path(os.environ["RAW_DATA_PATH"])

    ndjson_path = raw_root / "sample.ndjson"
    ndjson_path.write_text('{"name":"alice","score":1}\n{"name":"bob","score":2}\n', encoding="utf-8")

    nested_json_path = raw_root / "nested.json"
    nested_json_path.write_text(json.dumps([{"name": "alice", "payload": {"nested": True}}]), encoding="utf-8")

    ndjson_response = client.post("/editor-sessions", json={"file_path": str(ndjson_path), "page_size": 10})
    assert ndjson_response.status_code == 201

    nested_response = client.post("/editor-sessions", json={"file_path": str(nested_json_path), "page_size": 10})
    assert nested_response.status_code == 400
    assert "Nested JSON values" in nested_response.json()["detail"]


def test_pcap_is_preview_only(tmp_path: Path):
    client = _build_client(tmp_path)
    pcap_path = Path(os.environ["RAW_DATA_PATH"]) / "sample.pcap"
    _write_pcap(pcap_path)

    created = client.post("/editor-sessions", json={"file_path": str(pcap_path), "page_size": 10})
    assert created.status_code == 201
    assert created.json()["dataset_format"] == "pcap"
    assert created.json()["read_only"] is True
    session_id = created.json()["session_id"]

    page = client.get(f"/editor-sessions/{session_id}", params={"page": 1})
    assert page.status_code == 200
    assert page.json()["rows"]

    save = client.post(f"/editor-sessions/{session_id}/save")
    assert save.status_code == 409
    assert "preview-only" in save.json()["detail"]


def test_sc_is_preview_only(tmp_path: Path):
    client = _build_client(tmp_path)
    sc_path = Path(os.environ["RAW_DATA_PATH"]) / "sample.sc"
    sc_path.write_text(
        "1631256556434973186 0 30852 apache2 30852 select < res=0 exe=apache2\n"
        "1631256556435833391 0 30852 apache2 30852 clone < res=34 exe=apache2 tid=30853 pid=30852\n",
        encoding="utf-8",
    )

    created = client.post("/editor-sessions", json={"file_path": str(sc_path), "page_size": 10})
    assert created.status_code == 201
    assert created.json()["dataset_format"] == "sc"
    assert created.json()["read_only"] is True
    session_id = created.json()["session_id"]

    page = client.get(f"/editor-sessions/{session_id}", params={"page": 1})
    assert page.status_code == 200
    assert page.json()["rows"][0]["values"]["process_name"] == "apache2"
    assert page.json()["rows"][0]["values"]["syscall"] == "select"

    save = client.post(f"/editor-sessions/{session_id}/save")
    assert save.status_code == 409
    assert "preview-only" in save.json()["detail"]
