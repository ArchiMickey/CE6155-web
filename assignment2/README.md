1. connect to pinecone
2. create embedding model with SentenceTransformer
3. (optional) tokenize and upload the data to pinecone
4. use `generate_related_query` to get related queries
5. use `generate_fake_query` to get fake queries
6. use `vector_search` to get id and score of the most similar documents
7. use `reciprocal_rank_fusion` to rerank the documents
8. use `generate_hit_results` to get hit results from the reranked documents
9. use `generate_output` to get final response to the user