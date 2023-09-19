import openai
import os
from typing import Sequence
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.document_loaders import WebBaseLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_transformers import Html2TextTransformer
from textual import log

class AI:

    def __init__(self) -> None:
        openai.api_key = os.environ["OPENAI"]
        self.llm_name = "gpt-3.5-turbo"
        self.persist_directory = 'docs/chroma/'
        self.embedding = OpenAIEmbeddings()

    async def html_to_markdown(self, url) -> Sequence[Document]:
        loader = WebBaseLoader(url)
        data = loader.load()
        log(f"Loaded html: {data}")

        html2text = Html2TextTransformer()
        transformed_data = html2text.transform_documents(data)
        log(f"Transformed: {transformed_data}")

        return transformed_data

    async def initialize_vector_store(self, documents: Sequence[Document]):
        # text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        # splits = []
        # for document in documents:
        #     if document:
        #         s = text_splitter.split_text(document.page_content)
        #         splits.extend([Document(split) for split in s])

        vectordb = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding,
            persist_directory=self.persist_directory
        )
        # log(f"Split length: {len(splits)}")
        log(f"Vector db collection count: f{vectordb._collection.count()}")
        
        question = "Is this document about Python programming language?"
        docs = vectordb.similarity_search(question, k=3)
        log(f"Length of doc: {len(docs)}")
        log(f"First page or docs: {docs[0].page_content}")
        vectordb.persist()
