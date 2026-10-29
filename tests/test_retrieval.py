from app.data import itens
from app.retrieval import IndiceCardapio


def test_busca_encontra_o_item_certo(embedder):
    indice = IndiceCardapio(itens(), embedder)
    primeiro, _ = indice.buscar("pizza calabresa cebola", k=3)[0]
    assert primeiro["id"] == "P02"


def test_busca_respeita_k(embedder):
    assert len(IndiceCardapio(itens(), embedder).buscar("chocolate", k=4)) == 4


def test_cache_de_embeddings_e_reaproveitado(embedder, tmp_path):
    cache = tmp_path / "emb.json"
    IndiceCardapio(itens(), embedder, cache=cache)
    assert cache.exists()

    class SemChamadas(type(embedder)):
        def embed_documentos(self, textos):
            raise AssertionError("deveria ter usado o cache")

    IndiceCardapio(itens(), SemChamadas(), cache=cache)  # não levanta erro
