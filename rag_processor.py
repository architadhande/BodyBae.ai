from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from .vector_store import VectorStore
import os

class RAGProcessor:
    def __init__(self):
        self.llm = OpenAI(temperature=0.3, max_tokens=150)
        self.vector_store = VectorStore()
        self.retriever = self.vector_store.get_retriever()
        
        self.prompt_template = """Use the following context to answer the fitness/health question at the end.
        If you don't know the answer, say you don't know, don't try to make up an answer.
        
        Context: {context}
        
        Question: {question}
        
        Helpful Answer:"""
        
        self.qa_prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            chain_type_kwargs={"prompt": self.qa_prompt}
        )
    
    def process_query(self, query):
        try:
            result = self.qa_chain({"query": query})
            return result["result"]
        except Exception as e:
            print(f"Error processing query: {e}")
            return "I'm having trouble answering that right now. Could you try rephrasing your question?"

    def add_to_knowledge(self, text):
        self.vector_store.add_text(text)