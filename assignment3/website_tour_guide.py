from collections import Counter
import google.generativeai as genai
from rag import RAGSystem

genai.configure(api_key="AIzaSyC71miq1uuOH1BYm5PiaoqAvDKHPbp712A")
MODEL = "gemini-pro"


class Chatbot:
    def __init__(self):
        # Define self.genapi
        genapi = genai.GenerativeModel(MODEL)

        self.genapi = genapi
        self.rag = RAGSystem(genapi)

        self.default_topic = dict()
        self.create_topic()

    def decide_action(self, response, verbose=False):
        """
        Input : response
        Output : LLM choose action to do

        You can modify the behavior detection here,
        adding tasks or storing information for the large language model to act upon as needed.
        """

        task = {
            "Introduce website information": "Introducing the website based on predefined topics when the user has no specific inquiries or wishes to get a general understanding of the website structure.",
            "Answer Question": "Answering questions based on the user response.",
        }

        task_module = ""
        for idx, (title, task_describe) in enumerate(task.items()):
            task_module += f"{idx+1} {title} : {task_describe}, "

        prompt = f"You are an action-selection bot. Based on the current user's response and the task modules, \
            please decide what action to take and output one of the numbers from the task module. \
            The task modules are as follows {task_module} {response}。"

        text = self.genapi.generate_content(prompt).text
        if verbose:
            print(prompt)
            print(text)

        if "1" in text:
            action = "Introduce website information"
        elif "2" in text:
            action = "Answer Question"
        return action

    def answer_question(self, query):
        answer = self.rag.generate_answer(query)
        print("------------------------------------------------------------")
        print(" | Search: ", query, " | ")
        print("根據您的問題，我們找到了以下資訊：")
        print(answer.text)
        print("------------------------------------------------------------")
        return answer

    def process_query(self, query):
        action = self.decide_action(query)
        if action == "Introduce website information":
            self.introduce_website()
        elif action == "Answer Question":
            self.answer_question(query)
        else:
            print("Action not found.")
            return

    def create_topic(self):
        print("Creating default topics...")
        question = ""
        embed_query = self.rag.embed_model.encode(question)

        matches = self.rag.index.query(
            filter={
                "depth": 0,
            },
            vector=embed_query.tolist(),
            top_k=1,
            include_values=False,
            include_metadata=True,
        )
        links = matches.matches[0]["metadata"]["links_url"]
        link_titles = matches.matches[0]["metadata"]["links_title"]
        link_cnt = Counter()
        link_dic = dict()

        base_url = "https://www.csie.ncu.edu.tw/"
        for idx in range(len(links)):
            if link_titles[idx] != "" and base_url in links[idx]:
                link_dic[links[idx]] = link_titles[idx]
                remove_base_link = links[idx].replace(base_url, "")
                remove_base_link = remove_base_link.split("/")
                if len(remove_base_link) >= 2:
                    link_cnt[base_url + "/".join(remove_base_link[:3])] += 1

        for url, num in link_cnt.most_common(100):
            if url in link_dic and link_dic[url] not in self.default_topic:
                self.default_topic[link_dic[url]] = url
            if len(self.default_topic) == 10:
                break

        return

    def introduce_website(self):
        prompt = f"Here are some important websites. Please help me provide 5 questions that our visitors will most likely ask. Do not provide more than 5 questions. You can refer to the title of the websites. Please answer in the language same as the websites. {self.default_topic}"
        text = self.genapi.generate_content(prompt).text
        
        print("------------------------------------------------------------")
        print("這邊提供了常見的問題讓你參考：")
        print(text)
        print("------------------------------------------------------------")
        return text
        
    def chat(self):
        text = self.genapi.generate_content(
            f"You are a website navigation staff member and give a brief introduction. Just a short greeting and a couple of sentences will do; no additional information is needed."
        ).text
        print(text, "\n")
        while True:
            query = input("Please enter your query: ")
            if query == "exit":
                break
            self.process_query(query)


if __name__ == "__main__":
    chatbot = Chatbot()
    chatbot.chat()
