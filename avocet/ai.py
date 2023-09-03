import os
import csv
import httpx
# from langchain.chat_models import ChatOpenAI
# from langchain.prompts import ChatPromptTemplate
# from langchain.chains import RetrievalQA
from langchain.vectorstores import DocArrayInMemorySearch
from langchain.document_loaders import AsyncHtmlLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_transformers import Html2TextTransformer
from textual import log

class AI:

    def __init__(self) -> None:
        self.token = os.environ["OPENAI"]

    async def train(self, urls: list[str]) -> None:

        embeddings = OpenAIEmbeddings()
        loader = AsyncHtmlLoader(urls)
        data = await loader.load()
        log(data[0])

        html2text = Html2TextTransformer()
        transformed_data = html2text.transform_documents(data)
        log(transformed_data[0])

        index = VectorstoreIndexCreator(
            vectorstore_cls=DocArrayInMemorySearch,
            embedding=embeddings
        ).from_documents(transformed_data)

        query = f"Categorize this html page into a set of 3 categories that can be used as hashtags: {data[0]}"

        result = index.query(query)
        log(result)
