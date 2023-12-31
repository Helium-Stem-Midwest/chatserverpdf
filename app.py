import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template

from langchain.llms import HuggingFaceHub

# export OPENAI_API_KEY=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
# export HUGGINGFACEHUB_API_TOKEN=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
# streamlit run app.py

# openai_api_key = "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"
# huggingfacehub_api_token = "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"

# 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
import streamlit as st
import os

# Access secrets via st.secrets
openai_api_key = st.secrets["openai_api_key"]
huggingfacehub_api_token = st.secrets["huggingfacehub_api_token"]

# # Print the secrets
# st.write("OpenAI API key:", openai_api_key)
# st.write("Hugging Face Hub API token:", huggingfacehub_api_token)

# # Check if environment variables have been set correctly
# st.write(
#     "Has environment variable been set:",
#     os.environ["OPENAI_API_KEY"] == openai_api_key,
#     os.environ["HUGGINGFACEHUB_API_TOKEN"] == huggingfacehub_api_token,
# )

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks


def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore


def get_conversation_chain(vectorstore):
    llm = ChatOpenAI()
    # llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.5, "max_length":512})

    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain


def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)


def main():
    load_dotenv()
    st.set_page_config(page_title="Chat with multiple PDFs",
                       page_icon=":books:")
    st.write(css, unsafe_allow_html=True)
    print("OpenAI API Key:", os.environ.get("OPENAI_API_KEY"))

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("Chat with multiple PDFs :books:")
    user_question = st.text_input("Ask a question about your documents:")
    if user_question:
        handle_userinput(user_question)

    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click on 'Process'", accept_multiple_files=True)
        
        if st.button("Process"):
            with st.spinner("Processing"):
                # get pdf text
                raw_text = get_pdf_text(pdf_docs)

                # get the text chunks
                text_chunks = get_text_chunks(raw_text)

                # create vector store
                vectorstore = get_vectorstore(text_chunks)

                # create conversation chain
                st.session_state.conversation = get_conversation_chain(
                    vectorstore)


if __name__ == '__main__':
    main()
