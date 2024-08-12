from collections import Counter
from rag import create_pinecone, enconder, search_query, retrival, google_api
import google.generativeai as genai

def genapi(content):
    GOOGLE_API_KEY = 'Your API KEY'
    genai.configure(api_key=GOOGLE_API_KEY)

    safetySettings =  [
                {
                    "category": "HARM_CATEGORY_DANGEROUS",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
            ]
    model = genai.GenerativeModel('gemini-pro', safety_settings = safetySettings)
    response = model.generate_content(content)
    return response.text

class Chatbot:
    def __init__(self) -> None:
        self.index = create_pinecone()
        self.default_topic = dict()
        self.create_topic()

    def RAG(self, query):
        """
        Your Assignment 2
        """
        index = create_pinecone()
        embed_query = enconder(query)
        matches = search_query(index, embed_query)
        top3_hit_result = retrival(matches, index)
        answer = google_api(query, top3_hit_result)
        return answer

    def create_topic(self):
        """
        Input : None 
        Output : default topic

        Default topic options are provided to LLM as reference topics when users have no other ideas.
        You can set how to provide default topics to the large language model yourself, such as manually setting topics or using other methods.
        """
        question = ""
        embed_query = enconder(question)

        matches = self.index.query(
            filter={
                "depth": 0,
            },
            vector=embed_query.tolist(),
            top_k=1,
            include_values=False,
            include_metadata = True,
        )
        
        links = matches.matches[0]['metadata']['links_url']
        link_titles = matches.matches[0]['metadata']['links_title']
        link_cnt = Counter()
        link_dic = dict()

        base_url = 'https://www.chinese.ncu.edu.tw/'
        for idx in range(len(links)):
            if link_titles[idx] != "" and base_url in links[idx]:
                link_dic[links[idx]] = link_titles[idx]
                remove_base_link = links[idx].replace(base_url, "")
                remove_base_link = remove_base_link.split('/')
                if len(remove_base_link) >= 3 :
                    link_cnt[base_url + '/'.join(remove_base_link[:3])] += 1
        
        for url, num in link_cnt.most_common(100):
            if url in link_dic and link_dic[url] not in self.default_topic:
                self.default_topic[link_dic[url]] = url
            if len(self.default_topic) == 10 :
                break

        return 

    def decide_action(self, response):
        """
        Input : response 
        Output : LLM choose action to do

        You can modify the behavior detection here, 
        adding tasks or storing information for the large language model to act upon as needed.
        """
        
        task = {
            'Introduce website information' : "Introducing the website based on predefined topics when the user has no specific inquiries or wishes to get a general understanding of the website structure.", 
            'Answer Question' : 'Answering questions based on the user response.'
        }

        task_module = ""
        for idx, (title, task_describe) in enumerate(task.items()):
            task_module += f"{idx+1} {title} : {task_describe}, "

        text = genapi(f"You are an action-selection bot. Based on the current user's response and the task modules, \
                      please decide what action to take and output one of the numbers from the task module. \
                      The task modules are as follows {task_module} {response}。")

        if '1' in text:
            action = 'Introduce website information'
        elif '2' in text:
            action = 'Answer Question'
        return action

    def Chat(self):
        """
        Input : None 
        Output : None

        You can modify the chat flow of your chatbot according to your own settings.
        """
        text = genapi(f"You are a website navigation staff member and give a brief introduction \
                      Just a short greeting and a couple of sentences will do; no additional information is needed.")
        print(text, '\n')

        while(self.default_topic):
            response = input('Please input your message : \n')

            print('\nChatbot : ')
            action = self.decide_action(response)
            if action == 'Answer Question':
                answer = self.RAG(response)
                print(answer.text, '\n')
            elif action == 'Introduce website information':
                text = genapi(f"Here are some important websites. Please help me select five important topics based on the following websites and provide friendly and brief introductions. If the topics are in Chinese, please answer me in Chinese as well. {self.default_topic}")
                print(text, '\n')
        
if __name__ == '__main__':
    website_tour_guid = Chatbot()
    website_tour_guid.Chat()