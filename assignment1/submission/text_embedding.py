import json
from sentence_transformers import SentenceTransformer
import torch


def add_text_vector(data, model):
    batch_size = 100
    title_vectors = []
    content_vectors = []
    for i in range(0, len(data), batch_size):
        title_batch = [d["title"] for d in data[i:i+batch_size]]
        content_batch = [d["content"] for d in data[i:i+batch_size]]
        title_embeddings = model.encode(title_batch)
        contnet_embeddings = model.encode(content_batch)
        
        for j in range(len(title_batch)):
            title_vectors.append(title_embeddings[j])
            content_vectors.append(contnet_embeddings[j])

    assert len(title_vectors) == len(content_vectors) == len(data)
    for v, c, d in zip(title_vectors, content_vectors, data):
        d["title_vector"] = ",".join([str(x) for x in v])
        d["content_vector"] = ",".join([str(x) for x in c])

if __name__ == "__main__":
    with open("result_raw.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    model = SentenceTransformer("all-MiniLM-L6-v2")
    if torch.cuda.is_available():
        print("Using GPU")
        model = model.to("cuda")
    add_text_vector(data, model)
    
    # development的時候避免overwrite了原本的result.json
    # with open("result_vector.json", "w") as f:
    #     json.dump(data, f, ensure_ascii=False, indent=4)
    with open("result.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)