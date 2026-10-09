from functools import lru_cache

from django.conf import settings


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=settings.EMBEDDING_MODEL, cache_dir=settings.EMBEDDING_CACHE_DIR)


def embed_passages(texts):
    return [[float(x) for x in vector] for vector in _model().passage_embed(texts)]


def embed_query(text):
    return [float(x) for x in next(iter(_model().query_embed(text)))]
