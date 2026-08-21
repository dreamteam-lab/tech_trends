"""Tests for raw response storage."""

import json

import boto3
import pytest

from tech_trends.storage.raw import save_raw_response


def test_save_raw_response_writes_json_to_local_storage(
    tmp_path,
    monkeypatch,
) -> None:
    """Save the complete response in the expected local directory."""

    monkeypatch.setenv("RAW_STORAGE_BACKEND", "local")

    data = {
        "name": "react",
        "description": "Библиотека интерфейсов",
        "versions": ["19.2.7", "19.2.8"],
    }

    output_path = save_raw_response(
        data=data,
        data_dir=tmp_path,
        source="npm",
        query="react",
        page=0,
    )

    assert output_path.exists()

    relative_path = output_path.relative_to(tmp_path)

    assert relative_path.parts[:2] == ("raw", "npm")
    assert len(relative_path.parts) == 6
    assert output_path.name.startswith("react_")
    assert output_path.name.endswith("_page_0.json")

    saved_data = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert saved_data == data


def test_save_raw_response_makes_query_safe_for_filename(
    tmp_path,
    monkeypatch,
) -> None:
    """Remove unsafe characters from the query used in a filename."""

    monkeypatch.setenv("RAW_STORAGE_BACKEND", "local")

    output_path = save_raw_response(
        data={"name": "@nestjs/core"},
        data_dir=tmp_path,
        source="npm",
        query="@NestJS/Core",
        page=2,
    )

    assert output_path.name.startswith("nestjs_core_")
    assert output_path.name.endswith("_page_2.json")
    assert not list(output_path.parent.glob("*.tmp"))


def test_save_raw_response_uploads_json_to_s3(
    tmp_path,
    monkeypatch,
) -> None:
    """Upload the complete response to the Bronze S3 bucket."""

    uploaded_objects = []
    client_settings = {}

    class FakeS3Client:
        def put_object(self, **kwargs) -> None:
            uploaded_objects.append(kwargs)

    def fake_boto3_client(
        service_name: str,
        *,
        endpoint_url: str,
    ) -> FakeS3Client:
        client_settings["service_name"] = service_name
        client_settings["endpoint_url"] = endpoint_url

        return FakeS3Client()

    monkeypatch.setenv("RAW_STORAGE_BACKEND", "s3")
    monkeypatch.setenv(
        "S3_ENDPOINT_URL",
        "http://seaweedfs:8333",
    )
    monkeypatch.setenv(
        "S3_BRONZE_BUCKET",
        "tech-trends-bronze",
    )
    monkeypatch.setattr(
        boto3,
        "client",
        fake_boto3_client,
    )

    data = {
        "name": "react",
        "downloads": 123,
    }

    output_uri = save_raw_response(
        data=data,
        data_dir=tmp_path,
        source="npm",
        query="react",
        page=0,
    )

    assert client_settings == {
        "service_name": "s3",
        "endpoint_url": "http://seaweedfs:8333",
    }

    assert len(uploaded_objects) == 1

    uploaded_object = uploaded_objects[0]

    assert uploaded_object["Bucket"] == "tech-trends-bronze"
    assert uploaded_object["Key"].startswith("npm/")
    assert uploaded_object["Key"].endswith("_page_0.json")
    assert uploaded_object["ContentType"] == "application/json"
    assert json.loads(
        uploaded_object["Body"].decode("utf-8")
    ) == data

    assert output_uri == (
        f"s3://tech-trends-bronze/{uploaded_object['Key']}"
    )


def test_save_raw_response_rejects_unknown_backend(
    tmp_path,
    monkeypatch,
) -> None:
    """Reject an unsupported raw storage backend."""

    monkeypatch.setenv(
        "RAW_STORAGE_BACKEND",
        "unknown",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported RAW_STORAGE_BACKEND: unknown",
    ):
        save_raw_response(
            data={"name": "react"},
            data_dir=tmp_path,
            source="npm",
            query="react",
            page=0,
        )


def test_s3_storage_requires_endpoint(
    tmp_path,
    monkeypatch,
) -> None:
    """Require an S3 endpoint when the S3 backend is enabled."""

    monkeypatch.setenv("RAW_STORAGE_BACKEND", "s3")
    monkeypatch.delenv(
        "S3_ENDPOINT_URL",
        raising=False,
    )

    with pytest.raises(
        ValueError,
        match="S3_ENDPOINT_URL must be set",
    ):
        save_raw_response(
            data={"name": "react"},
            data_dir=tmp_path,
            source="npm",
            query="react",
            page=0,
        )
