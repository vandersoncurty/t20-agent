"""Conexão com o Qdrant e criação/validação de coleções.

A dimensão do vetor precisa corresponder ao modelo de embedding usado na
indexação. O módulo falha com erro explícito quando a coleção existente tem
dimensão diferente da configurada, em vez de reutilizá-la silenciosamente.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final, overload

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

DEFAULT_COLLECTION: Final = "t20_rules"
DEFAULT_EMBEDDING_MODEL: Final = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIMENSION: Final = 1536

# Dimensões dos modelos mais comuns. Modelos não listados exigem
# EMBEDDING_DIMENSION explícito no ambiente.
EMBEDDING_DIMENSIONS: Final[dict[str, int]] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


class QdrantConnectionError(RuntimeError):
    """O Qdrant não respondeu na configuração informada."""


class CollectionDimensionMismatchError(RuntimeError):
    """A coleção existente usa uma dimensão diferente da configurada."""

    def __init__(
        self,
        collection_name: str,
        existing_dimension: int,
        expected_dimension: int,
    ) -> None:
        self.collection_name = collection_name
        self.existing_dimension = existing_dimension
        self.expected_dimension = expected_dimension
        super().__init__(
            f"A coleção '{collection_name}' tem vetores de dimensão "
            f"{existing_dimension}, mas a configuração espera {expected_dimension}. "
            "Use outra coleção, ajuste EMBEDDING_DIMENSION ou recrie a coleção."
        )


@dataclass(frozen=True, slots=True)
class QdrantSettings:
    """Configuração do Qdrant e do modelo de embedding."""

    host: str
    port: int
    collection_name: str
    embedding_model: str
    embedding_dimension: int
    api_key: str | None = None

    @classmethod
    def from_env(cls) -> QdrantSettings:
        """Carrega a configuração do `.env`/variáveis de ambiente."""
        load_dotenv()

        model = os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
        dimension = _env_int("EMBEDDING_DIMENSION", None)
        if dimension is None:
            try:
                dimension = EMBEDDING_DIMENSIONS[model]
            except KeyError as exc:
                raise ValueError(
                    f"Modelo de embedding desconhecido: '{model}'. "
                    "Defina EMBEDDING_DIMENSION no ambiente."
                ) from exc

        if dimension <= 0:
            raise ValueError("EMBEDDING_DIMENSION deve ser maior que zero.")

        return cls(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=_env_int("QDRANT_PORT", 6333),
            collection_name=os.getenv("QDRANT_COLLECTION", DEFAULT_COLLECTION),
            embedding_model=model,
            embedding_dimension=dimension,
            api_key=os.getenv("QDRANT_API_KEY") or None,
        )


@overload
def _env_int(name: str, default: int) -> int: ...


@overload
def _env_int(name: str, default: None = None) -> int | None: ...


def _env_int(name: str, default: int | None = None) -> int | None:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} deve ser um número inteiro, recebido: {raw!r}") from exc


def get_client(
    settings: QdrantSettings | None = None,
    *,
    timeout: int = 15,
) -> QdrantClient:
    """Cria o cliente HTTP do Qdrant (sem abrir conexão imediata)."""
    settings = settings or QdrantSettings.from_env()
    return QdrantClient(
        host=settings.host,
        port=settings.port,
        api_key=settings.api_key,
        timeout=timeout,
    )


def check_connection(
    client: QdrantClient,
    settings: QdrantSettings | None = None,
) -> None:
    """Valida que o Qdrant responde, com mensagem de erro contextualizada."""
    try:
        client.get_collections()
    except Exception as exc:
        target = f"{settings.host}:{settings.port}" if settings else "Qdrant"
        raise QdrantConnectionError(
            f"Não foi possível conectar ao Qdrant em {target}: {exc}"
        ) from exc


def get_collection_dimension(client: QdrantClient, collection_name: str) -> int:
    """Retorna a dimensão dos vetores de uma coleção existente."""
    info = client.get_collection(collection_name)
    vectors = info.config.params.vectors
    if isinstance(vectors, VectorParams):
        return vectors.size
    raise ValueError(
        f"A coleção '{collection_name}' usa vetores nomeados; "
        "este projeto espera um único vetor sem nome."
    )


def ensure_collection(
    client: QdrantClient,
    collection_name: str,
    vector_size: int,
    *,
    distance: Distance = Distance.COSINE,
    recreate: bool = False,
) -> bool:
    """Garante que a coleção exista com a dimensão correta.

    Retorna ``True`` se a coleção foi criada e ``False`` se já existia.
    Com ``recreate=True``, uma coleção existente é apagada e recriada,
    descartando os pontos atuais.
    """
    if vector_size <= 0:
        raise ValueError("vector_size deve ser maior que zero.")

    exists = client.collection_exists(collection_name)
    if exists and recreate:
        client.delete_collection(collection_name)
        exists = False

    if exists:
        existing_dimension = get_collection_dimension(client, collection_name)
        if existing_dimension != vector_size:
            raise CollectionDimensionMismatchError(collection_name, existing_dimension, vector_size)
        return False

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=distance),
    )
    return True


def initialize_collection(
    settings: QdrantSettings | None = None,
    *,
    client: QdrantClient | None = None,
    recreate: bool = False,
) -> tuple[QdrantClient, bool]:
    """Conecta ao Qdrant e garante a coleção configurada."""
    settings = settings or QdrantSettings.from_env()
    client = client or get_client(settings)
    created = ensure_collection(
        client,
        settings.collection_name,
        settings.embedding_dimension,
        recreate=recreate,
    )
    return client, created


def main() -> None:
    """Smoke test: ``python -m vector_db``."""
    settings = QdrantSettings.from_env()
    client = get_client(settings)
    try:
        check_connection(client, settings)
        _, created = initialize_collection(settings, client=client)
    finally:
        client.close()

    status = "criada" if created else "já existia"
    print(
        f"Qdrant OK em {settings.host}:{settings.port}. "
        f"Coleção '{settings.collection_name}' {status} "
        f"(dimensão {settings.embedding_dimension})."
    )
