import pytest
from tools.phase_05_search import semantic_common


def test_production_embedding_uses_only_dedicated_environment_key(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('OPENAI_API_KEY', 'unused-staging-key')
    monkeypatch.setenv('PRODUCTION_OPENAI_API_KEY', 'dedicated-fake-key')
    monkeypatch.setattr(semantic_common, 'load_env_value', lambda name: pytest.fail('production dotenv discovery forbidden'))
    assert semantic_common.OpenAIEmbeddingsClient().api_key == 'dedicated-fake-key'


def test_production_embedding_refuses_generic_key_fallback(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('OPENAI_API_KEY', 'unused-staging-key')
    monkeypatch.delenv('PRODUCTION_OPENAI_API_KEY', raising=False)
    monkeypatch.setattr(semantic_common, 'load_env_value', lambda name: pytest.fail('production dotenv discovery forbidden'))
    with pytest.raises(SystemExit, match='PRODUCTION_OPENAI_API_KEY'):
        semantic_common.OpenAIEmbeddingsClient()
