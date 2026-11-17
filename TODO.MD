# TODO - Desenvolvimento do Agente T20 RPG

## Fase 1: Setup e Infraestrutura Base
- [x] Criar o arquivo `.env.example` com as variáveis necessárias (`QDRANT_HOST`, `QDRANT_PORT`, `OPENAI_API_KEY`).
- [x] Configurar o arquivo `requirements.txt` ou `pyproject.toml` com as dependências (`langchain`, `langchain-openai`, `qdrant-client`, `docling`, `pydantic`).
- [x] Subir e validar a instância local do Qdrant via Docker.
- [x] Criar o módulo de conexão com o Qdrant (`src/vector_db/client.py`) garantindo a criação da coleção com a dimensão correta dos embeddings.

## Fase 2: Pipeline de Ingestão de Dados (ETL)
- [ ] Desenvolver o script de parsing de PDF para Markdown estruturado (`src/ingestion/parser.py`) usando Docling/Unstructured.
- [ ] Implementar o particionamento semântico usando `MarkdownHeaderTextSplitter` do LangChain (`src/ingestion/splitter.py`).
- [ ] Criar o script de injeção de metadados (`livro`, `capitulo`, `categoria`) nos chunks.
- [ ] Escrever o script de carga inicial para popular o Qdrant com o Livro Básico (Jogo do Ano) e suplementos.

## Fase 3: Camada de Recuperação (Retrieval)
- [ ] Implementar o retriever básico por similaridade com filtros de metadados no Qdrant.
- [ ] Configurar busca híbrida (pontuação densa + esparsa/BM25) se aplicável.
- [ ] Integrar um modelo de Reranking para refinar os trechos recuperados.

## Fase 4: Construção do Agente (LangGraph)
- [ ] Definir o State do grafo (`src/agent/state.py`) contendo mensagens, contexto recuperado e histórico.
- [ ] Criar a ferramenta (Tool) de busca de regras no Qdrant (`src/agent/tools/rules_search.py`).
- [ ] Criar a ferramenta (Tool) de cálculo mecânico (CD de magias, custos de PM) (`src/agent/agent/tools/calculator.py`).
- [ ] Implementar o fluxo do LangGraph com nós de decisão, recuperação e geração de resposta (`src/agent/graph.py`).

## Fase 5: Interface e Validação
- [ ] Desenvolver uma interface CLI interativa simples em Python para testar perguntas e respostas.
- [ ] Criar um dataset de validação com 20 perguntas complexas de regras de Tormenta 20 para testar alucinações e precisão das fontes.