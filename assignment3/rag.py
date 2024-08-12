# import modules

from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import textwrap
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter


class RAGSystem:
    def __init__(self, genapi):
        print("Loading Pinecone...")
        self.pc = Pinecone(api_key="60ec97ef-7862-4555-aa8c-8f8b3f7989e2")
        self.index_name = "retrieval-augmentation-generation"
        self.index = self.pc.Index(self.index_name)
        print("Loading Embedding Model...")
        self.embed_model = SentenceTransformer("aspire/acge_text_embedding")
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=20,
            length_function=self.tiktoken_len,
            separators=["\n\n", "\n", " ", ""],
        )
        self.genapi = genapi

    def tiktoken_len(self, text):
        tokens = self.tokenizer.encode(text, disallowed_special=())
        return len(tokens)

    def generate_related_query(self, qeury, num_results=4):
        prompt = textwrap.dedent(
            f"""
            You are a helpful assistant that can generate multiple search queries based on a given search query. 
            Please enerate multiple search queries related to: {qeury},
            OUTPUT: ({num_results} queries):
            """
        )
        response = self.genapi.generate_content(prompt)
        return response.text

    def generate_fake_answer(self, qeury):
        query_prompt = textwrap.dedent(
            f"""
            You are a helpful assistant of 資訊工程學系 in 國立中央大學(NCU). Please write a passage to answer the qustion. Your answer should be in sentences only and with the same language as the query.
            Question: {qeury}
            Passage:
        """
        )
        response = self.genapi.generate_content(query_prompt)
        return response.text.strip()

    def vector_search(self, query, top_k=100):
        embed_query = self.embed_model.encode(query)
        matches = self.index.query(vector=embed_query.tolist(), top_k=top_k)
        return {ret["id"]: ret["score"] for ret in matches.matches}

    def reciprocal_rank_fusion(self, search_results, k=60):
        fused_results = {}

        for query, results in search_results.items():
            for rank, (doc_id, score) in enumerate(results.items()):
                if doc_id not in fused_results:
                    fused_results[doc_id] = 0
                fused_results[doc_id] += 1 / (rank + k)

        reranked_results = {
            doc_id: score
            for doc_id, score in sorted(
                fused_results.items(), key=lambda x: x[1], reverse=True
            )
        }
        return reranked_results

    def generate_hit_results(self, results, num_results=3):
        retrival_data = []
        searching_ids = list(results.keys())[:num_results]
        result = self.index.fetch(searching_ids)
        for id in searching_ids:
            retrival_data.append(result["vectors"][id].metadata)
        hit_results = []
        for i, data in enumerate(retrival_data):
            r = ""
            r += f"'''No.{i+1} {data['title']}: {data['source']}\n"
            r += f"No.{i+1} data: {data['text']}'''\n"
            hit_results.append(r)
        return hit_results

    def generate_output(self, query, hit_result):
        prompt = textwrap.dedent(
            """QUESTION: '{query}'
            PASSAGE: '{relevant_passage}'
            You are a great assistant. There are a total of several pieces of searched information here. Please extract the relevant parts of each piece of information based on the user's question and organize it into complete and understandable content and reply to the user. Please extract the information one by one with the given order. You should use the language of input to answer this question. Make sure there are no omission, and provide the source URL of all pieces of information.
            OUTPUT: (Information extracted with all {length} pieces of information in order.)
            """
        ).format(query=query, relevant_passage=hit_result, length=len(hit_result))
        return self.genapi.generate_content(prompt)

    def generate_answer(self, query):
        fake_answers = [
            self.generate_fake_answer(q)
            for q in [query, *[self.generate_related_query(query).split("\n")]]
            if q
        ]
        # print(fake_answers)
        gathered_results = {}
        for q in fake_answers:
            search_results = self.vector_search(q)
            gathered_results[q] = search_results
        # display(gathered_results)
        results = self.reciprocal_rank_fusion(gathered_results)
        hit_result = self.generate_hit_results(results)
        # print(hit_result)
        return self.generate_output(query, hit_result)
