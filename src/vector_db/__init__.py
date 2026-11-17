"""Conexão com o Qdrant e configuração de coleções."""

from vector_db.client import (
    CollectionDimensionMismatchError,
    QdrantConnectionError,
    QdrantSettings,
    check_connection,
    ensure_collection,
    get_client,
    get_collection_dimension,
    initialize_collection,
)

__all__ = [
    "CollectionDimensionMismatchError",
    "QdrantConnectionError",
    "QdrantSettings",
    "check_connection",
    "ensure_collection",
    "get_client",
    "get_collection_dimension",
    "initialize_collection",
]
