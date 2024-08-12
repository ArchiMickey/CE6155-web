from elasticsearch import Elasticsearch
import torch
from sentence_transformers import SentenceTransformer
import json
import sys
from pprint import pprint


def text_to_vector(text, model):
    query_embedding = model.encode(text)
    query_embedding = [float(x) for x in query_embedding]
    return query_embedding


def query(query, es, query_vector=None, size=1):
    index_name = f"ncu_csie"

    # Query DSL
    search_params = {
        "size": size,
        "query": {
            "bool": {
                "filter": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title", "content", "url", "imgs"],
                            "type": "phrase"
                        }
                    },
                ],
                "should": [
                    {
                        "match_phrase": {
                            "title": {
                                "query": query,
                                "boost": 3,
                            }
                        }
                    },
                    {
                        "match_phrase": {
                            "content": {
                                "query": query,
                                "boost": 4,
                            }
                        }
                    },
                    {
                        "match_phrase": {
                            "imgs": {
                                "query": query,
                                "boost": 10,
                            }
                        }
                    },
                    {
                        "match": {
                            "url": {
                                "query": query,
                                "boost": 5,
                                "operator": "and",
                            }
                        }
                    },
                    {
                        "knn": {
                            "field": "title_vector",
                            "query_vector": query_vector,
                            "num_candidates": 10,
                            "boost": 3,
                        }
                    },
                    {
                        "knn": {
                            "field": "content_vector",
                            "query_vector": query_vector,
                            "num_candidates": 10,
                            "boost": 1,
                        }
                    },
                ],
            }
        },
        # "sort": [
        #     {"depth": "asc"},
        # ],
    }

    # Search document
    result = es.search(index=index_name, body=search_params)

    return result["hits"]["hits"]


if __name__ == "__main__":
    es = Elasticsearch(
        "https://archimickey:20020119@localhost:9200", verify_certs=False
    )
    MODEL_NAME = "all-MiniLM-L6-v2"
    print(f"Loading model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    if torch.cuda.is_available():
        print("Using GPU")
        model = model.to("cuda")

    while True:
        q = input("Enter query:")
        if not q:
            break
        print("Results of query '%s':" % q)
        q_vector = text_to_vector(q, model)
        results = query(q, es, q_vector, size=10)

        for res in results:
            title, url = res["_source"]["title"], res["_source"]["url"]
            score = res["_score"]
            print(f"{title}: {url}")
