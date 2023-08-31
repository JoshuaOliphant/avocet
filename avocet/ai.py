import os
# from langchain.chat_models import ChatOpenAI
# from langchain.prompts import ChatPromptTemplate
# from langchain.chains import RetrievalQA
from langchain.vectorstores import DocArrayInMemorySearch
from langchain.document_loaders import UnstructuredMarkdownLoader
from langchain.indexes import VectorstoreIndexCreator

class AI:

    def __init__(self) -> None:
        self.token = os.environ["OPENAI"]

    def load_document(self):
        loader = UnstructuredMarkdownLoader("README.md")

        index = VectorstoreIndexCreator(
            vectorstore_cls=DocArrayInMemorySearch
        ).from_loaders([loader])

        query = "Summarize this text"

        response = index.query(query)
        print(response)


if __name__ == "__main__":
    ai = AI()
    ai.load_document()
