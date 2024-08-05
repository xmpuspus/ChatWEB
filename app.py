import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import UnstructuredURLLoader
import tempfile

# Prompt template
prompt = PromptTemplate(
    input_variables=["chat_history", "question"],
    template="""You are a very kind and friendly AI assistant. You are
    currently having a conversation with a human. Answer the questions
    in a kind and friendly tone but in a professional manner. 
    
    chat_history: {chat_history},
    Human: {question}
    AI:"""
)

# Streamlit page configuration
st.set_page_config(
    page_title="Website Chatbot",
    page_icon="🌐",
    layout="wide"
)

# Sidebar inputs for API key and website URL
st.sidebar.title("Settings")
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
website_url = st.sidebar.text_input("Website URL")

# Chat title
st.title("Website Chatbot")

# Check if messages exist in session state, if not initialize
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello there, I am your Website chatbot."}
    ]
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

# Display all chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Handle website URL input
if website_url and openai_api_key:
    # Load website content
    loader = UnstructuredURLLoader(urls=[website_url])
    data = loader.load()
    
    website_text = ""
    for doc in data:
        website_text += doc.page_content

    # Initialize vector store with website content
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vector_store = FAISS.from_texts([website_text], embeddings)

    # Save vector store in session state
    st.session_state.vector_store = vector_store

    # Notify user of successful website processing
    st.success("Website content loaded and processed successfully!")

# User input
user_prompt = st.chat_input()

if user_prompt is not None and st.session_state.vector_store is not None:
    # Add user message to session state
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    # Generate AI response using vector store
    llm = ChatOpenAI(openai_api_key=openai_api_key, model='gpt-4o')
    memory = ConversationBufferWindowMemory(memory_key="chat_history", k=10)
    llm_chain = LLMChain(
        llm=llm,
        memory=memory,
        prompt=prompt
    )

    with st.chat_message("assistant"):
        with st.spinner("Loading..."):
            # Get the most relevant text from vector store
            relevant_text = st.session_state.vector_store.similarity_search(user_prompt, k=1)
            combined_prompt = f"{relevant_text[0].page_content}\n\n{user_prompt}"
            ai_response = llm_chain.predict(question=combined_prompt)
            st.write(ai_response)

    # Add assistant message to session state
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
elif user_prompt is not None:
    st.error("Please provide a valid Website URL and API Key first.")
