import openai
import os
from typing import Sequence
from langchain.chat_models import ChatOpenAI
from langchain.schema.output_parser import OutputParserException
from langchain.chains import create_extraction_chain
from langchain.schema import Document
from langchain.vectorstores import Chroma
from langchain.document_loaders import WebBaseLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
# from langchain.document_transformers import Html2TextTransformer
from textual import log
from requests.exceptions import SSLError

class AI:

    def __init__(self) -> None:
        openai.api_key = os.environ["OPENAI_API_KEY"]
        self.llm_name = "gpt-3.5-turbo"
        self.persist_directory = 'docs/chroma/'
        self.embedding = OpenAIEmbeddings()
        self.llm = ChatOpenAI(temperature=0, model=self.llm_name)

    async def extract(self, content: str, schema: dict):
        try:
            text_splitter = RecursiveCharacterTextSplitter().from_language(language=Language.HTML)
            text_splits = text_splitter.split_text(content[0].page_content)
            print(f"Length of text_splits: {len(text_splits)}")
            if len(text_splits) == 0:
                return None
            return create_extraction_chain(schema=schema, llm=self.llm).run(text_splits[0])
        except OutputParserException as e:
            # Handle the exception here
            print(f"Error occurred during output parsing: {e}")
            return None
        except SSLError as e:
            print(f"SSL error occurred: {e}")
            return None

    async def html_to_markdown(self, url) -> Sequence[Document]:
        loader = WebBaseLoader(url)
        data = loader.load()

        schema = {
            "properties": {
                "article_title": {"type": "string"},
                "article_summary": {"type": "string"},
            },
            "required": ["article_title", "article_body"],
        }

        transformed_data = await self.extract(data, schema)
        print(f"transormed data: {transformed_data}")

        return transformed_data

    async def initialize_vector_store(self, documents: Sequence[Document]):

        vectordb = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding,
            persist_directory=self.persist_directory
        )
        log(f"Vector db collection count: f{vectordb._collection.count()}")

        question = "Is this document about Python programming language?"
        docs = vectordb.similarity_search(question, k=3)
        log(f"Length of doc: {len(docs)}")
        log(f"First page or docs: {docs[0].page_content}")
        vectordb.persist()

        assert len(docs) == 3
        assert docs[0].page_content is not None
        assert isinstance(docs[0].page_content, str)
        assert vectordb._collection.count() > 0
