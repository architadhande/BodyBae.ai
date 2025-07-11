from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import json
from config import Config

class RAGService:
    def __init__(self):
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(openai_api_key=Config.OPENAI_API_KEY)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            temperature=0.3,
            model="gpt-3.5-turbo",
            openai_api_key=Config.OPENAI_API_KEY
        )
        
        # Load and process knowledge base
        self.setup_vectorstore()
        
        # Create QA chain
        self.qa_chain = self.create_qa_chain()
    
    def setup_vectorstore(self):
        """Load health knowledge and create vector store"""
        # Load health knowledge
        with open('data/health_knowledge.json', 'r') as f:
            knowledge_data = json.load(f)
        
        # Convert to documents
        documents = []
        for category, items in knowledge_data.items():
            for item in items:
                if isinstance(item, dict):
                    text = f"Category: {category}\n"
                    text += f"Question: {item.get('question', '')}\n"
                    text += f"Answer: {item.get('answer', '')}\n"
                    if 'tips' in item:
                        text += f"Tips: {', '.join(item['tips'])}\n"
                    documents.append(text)
                else:
                    documents.append(f"Category: {category}\nInformation: {item}")
        
        # Split documents
        text_splitter = CharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separator="\n"
        )
        texts = text_splitter.create_documents(documents)
        
        # Create vector store
        self.vectorstore = Chroma.from_documents(
            documents=texts,
            embedding=self.embeddings,
            persist_directory="./chroma_db"
        )
    
    def create_qa_chain(self):
        """Create the QA chain with custom prompt"""
        prompt_template = """You are BodyBae, a knowledgeable fitness and health assistant. 
        Use the following context to answer the question. If you're not sure about something, 
        say so honestly and suggest consulting with a healthcare professional.
        
        Context: {context}
        
        Question: {question}
        
        Provide a helpful, accurate, and encouraging response:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 3}
            ),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=False
        )
    
    def get_answer(self, question):
        """Get answer for a health-related question"""
        try:
            result = self.qa_chain.invoke({"query": question})
            return result['result']
        except Exception as e:
            return f"I apologize, but I'm having trouble finding information about that. For specific health concerns, please consult with a healthcare professional."