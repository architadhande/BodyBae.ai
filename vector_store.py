from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import JSONLoader
import json
import os

class VectorStore:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.db = None
        self.initialize_vectorstore()
    
    def initialize_vectorstore(self):
        if os.path.exists("rag_system/faiss_index"):
            self.db = FAISS.load_local("rag_system/faiss_index", self.embeddings)
        else:
            self.create_initial_vectorstore()
    
    def create_initial_vectorstore(self):
        loader = JSONLoader(
            file_path="rag_system/knowledge_base.json",
            jq_schema=".qna[]",
            text_content=False
        )
        documents = loader.load()
        
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        
        self.db = FAISS.from_documents(texts, self.embeddings)
        self.db.save_local("rag_system/faiss_index")
    
    def get_retriever(self):
        return self.db.as_retriever(search_kwargs={"k": 3})
    
    def add_text(self, text):
        # For adding new knowledge to the store
        from langchain.docstore.document import Document
        new_doc = Document(page_content=text, metadata={"source": "user_added"})
        self.db.add_documents([new_doc])
        self.db.save_local("rag_system/faiss_index")