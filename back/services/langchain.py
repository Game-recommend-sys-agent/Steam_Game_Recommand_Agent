from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Qdrant
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document
from back.core.config import settings
from back.db.qdrant import get_qdrant_client

class LangChainService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        self.client = get_qdrant_client()
        self.vector_store = Qdrant(
            client=self.client,
            collection_name=settings.QDRANT_COLLECTION_NAME,
            embeddings=self.embeddings,
        )
        self.llm = ChatOpenAI(openai_api_key=settings.OPENAI_API_KEY, model="gpt-4o")

    async def add_document(self, content: str, metadata: dict):
        doc = Document(page_content=content, metadata=metadata)
        ids = self.vector_store.add_documents([doc])
        return ids[0]

    async def chat(self, query: str):
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(),
            return_source_documents=True
        )
        result = qa_chain.invoke({"query": query})
        return result
