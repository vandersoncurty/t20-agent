# Diretrizes para agentes — Agente T20 RPG

Agente especialista em **Tormenta 20** (Edição Jogo do Ano + suplementos), em Python com LangChain/LangGraph e Qdrant. O roadmap é o `TODO.MD`; a Fase 1 já está implementada, então não presuma que módulos das fases 2–5 existam.

## Comandos

```bash
uv sync                 # instala deps do pyproject/uv.lock (docling é pesado)
cp .env.example .env    # preencha OPENAI_API_KEY (e QDRANT_API_KEY se houver auth)
docker compose up -d    # Qdrant local; dados em ./qdrant_storage (gitignored)
uv run python -m vector_db  # smoke test: conecta e cria/valida a coleção
```

Verificação antes de concluir uma mudança (nesta ordem):

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src tests
uv run pytest
uv run pytest tests/test_vector_db_client.py::test_ensure_collection_creates_with_configured_dimension
```

Os testes de unidade usam Qdrant in-memory (`QdrantClient(location=":memory:")`); Docker só é necessário para o smoke test.

## Estrutura

- Layout `src/` com pacotes de topo (`ingestion`, `vector_db`, `agent`, `api`), não um pacote único `t20_agent`: importe como `from vector_db.client import ...`. O `pyproject.toml` configura `pythonpath = ["src"]` para o pytest.
- `src/vector_db/client.py`: settings, conexão, checagem de dimensão e criação de coleção. `python -m vector_db` executa o smoke test.
- `src/agent/tools/` e demais módulos das fases seguintes ainda não existem.
- O TODO cita `src/agent/agent/tools/calculator.py`; é typo — use `src/agent/tools/calculator.py`.

## Configuração e Qdrant

- Defaults: `localhost:6333`, coleção `t20_rules`, `text-embedding-3-small` com 1536 dimensões. `QdrantSettings.from_env()` carrega `.env`.
- `EMBEDDING_DIMENSION` é inferida para os modelos OpenAI mapeados; qualquer outro modelo exige a variável explícita.
- A dimensão da coleção deve bater com o modelo de embedding. `ensure_collection` lança `CollectionDimensionMismatchError` em vez de reutilizar uma coleção incompatível; `recreate=True` apaga os pontos existentes.
- Nenhum chunk pode ser gravado sem os metadados `livro`, `capitulo` e `categoria`.

## Convenções

- Documentação e mensagens de erro em português, seguindo `TODO.MD`.
- Stack planejada: Python 3.10+, LangChain/LangGraph, Qdrant, Docling/Unstructured, embeddings/LLM via API (OpenAI/Gemini).
