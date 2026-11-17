from collections.abc import Iterator

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import Distance

from vector_db.client import (
    CollectionDimensionMismatchError,
    QdrantSettings,
    ensure_collection,
    get_collection_dimension,
)


@pytest.fixture
def client() -> Iterator[QdrantClient]:
    qdrant = QdrantClient(location=":memory:")
    try:
        yield qdrant
    finally:
        qdrant.close()


def test_ensure_collection_creates_with_configured_dimension(
    client: QdrantClient,
) -> None:
    created = ensure_collection(client, "rules", 1536, distance=Distance.COSINE)

    assert created is True
    assert get_collection_dimension(client, "rules") == 1536


def test_ensure_collection_is_idempotent(client: QdrantClient) -> None:
    ensure_collection(client, "rules", 1536)

    assert ensure_collection(client, "rules", 1536) is False


def test_ensure_collection_rejects_dimension_mismatch(
    client: QdrantClient,
) -> None:
    ensure_collection(client, "rules", 1536)

    with pytest.raises(CollectionDimensionMismatchError) as exc_info:
        ensure_collection(client, "rules", 3072)

    assert exc_info.value.existing_dimension == 1536
    assert exc_info.value.expected_dimension == 3072


def test_ensure_collection_recreate_replaces_dimension(
    client: QdrantClient,
) -> None:
    ensure_collection(client, "rules", 1536)

    assert ensure_collection(client, "rules", 3072, recreate=True) is True
    assert get_collection_dimension(client, "rules") == 3072


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QDRANT_HOST", "qdrant.local")
    monkeypatch.setenv("QDRANT_PORT", "6334")
    monkeypatch.setenv("QDRANT_COLLECTION", "test_rules")
    monkeypatch.setenv("QDRANT_API_KEY", "secret")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-large")
    monkeypatch.delenv("EMBEDDING_DIMENSION", raising=False)

    settings = QdrantSettings.from_env()

    assert settings.host == "qdrant.local"
    assert settings.port == 6334
    assert settings.collection_name == "test_rules"
    assert settings.api_key == "secret"
    assert settings.embedding_dimension == 3072


def test_settings_require_dimension_for_unknown_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EMBEDDING_MODEL", "modelo-inexistente")
    monkeypatch.delenv("EMBEDDING_DIMENSION", raising=False)

    with pytest.raises(ValueError, match="EMBEDDING_DIMENSION"):
        QdrantSettings.from_env()
