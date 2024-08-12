from elasticsearch import Elasticsearch, helpers
import json
import sys

'''
data = {
        'url': text,
        'title': text,
        'depth': integer,
        'content': text,
        'links': [tuple(text,text)]
        'imgs: [tuple(text,text)]
    }
'''

hp_mapping = {
    "properties": {
        "url": {
            "type": "text"
        },
        "title": {
            "type": "text"
        },
        "depth": {
            "type": "integer"   
        },
        "content": {
            "type": "text",
        },
        "links": {
            "type": "text"
        },
        "imgs": {
            "type": "text"
        },
        "content_vector": {
            "type": "dense_vector",
            "dims": 384
        },
        "title_vector": {
            "type": "dense_vector",
            "dims": 384
        }
    }
}

# Load dataset
def read_data():
    with open(f'result.json', 'r' ,encoding='utf-8') as f:
        data = json.load(f)
        for row in data:
            row["title_vector"] = [float(x) for x in row["title_vector"].split(",")]
            row["content_vector"] = [float(x) for x in row["content_vector"].split(",")]
            yield row

def load2_elasticsearch():
    index_name = f'ncu_csie'
    es = Elasticsearch("https://archimickey:20020119@localhost:9200", verify_certs=False)

    
    # Create Index
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name)
    print('Index created!')

    # Put mapping into index
    # print('Mappings created!')
    es.indices.put_mapping(
        index=index_name,  body=hp_mapping)
    print('Mappings created!')

    
    # Import data to elasticsearch
    success, _ = helpers.bulk(
        client=es, actions=read_data(), index=index_name, ignore=400)
    print('success: ', success)
    #print(_)

if __name__ == "__main__":  
    load2_elasticsearch()
