import streamlit as st
import streamlit.components.v1 as components
import streamlit_javascript as st_js 
from pymongo import MongoClient
from bson import ObjectId
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv
import base64
from streamlit_javascript import st_javascript

# --- Load environment variables ---
load_dotenv()
mongo_uri = os.getenv("MONGO_URI")
openai_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = openai_key

# --- MongoDB Setup ---
client = MongoClient(mongo_uri)
DB_NAME = "FIRE"
COLLECTIONS = [
    "networths", "personalrisks", "net_worths", "multiusers", "mfdetails",
    "marriagefundplans", "insurances", "houseplans", "googles", "fundallocations",
    "childexpenses", "childeducations", "budgetincomeplans", "firequestions",
    "financials", "customplans", "expensesmasters", "vehicles", "emergencyfunds",
    "profiles", "realitybudgetincomes"
]

# --- Streamlit Page Config ---
st.set_page_config(page_title="FIFP", layout="centered")

# --- Custom CSS Styling ---
st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
        }
        h1, h2, h3 {
            text-align: center;
            color: #0d6efd;
        }
        .stTextInput>div>div>input {
            font-size: 16px;
        }
    </style>
""", unsafe_allow_html=True)

# --- Centered Image Logo ---
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_base64 = get_base64_image("fifp_logo.png")

st.markdown(f"""
    <div style='text-align: center;'>
        <img src="data:image/png;base64,{logo_base64}" width="120"/>
    </div>
""", unsafe_allow_html=True)

# --- Title & Subtitle ---
st.markdown("<h2 style='text-align: center; color: #0d6efd;'>Financial Independence Focus Passion</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #555;'>💼 Chat with your personalized data</p>", unsafe_allow_html=True)
st.divider()

components.html(
    """
    <script>

    window.addEventListener('message', (event) => {
        // Check the origin of the sender
        const { userId } = event.data;
        if (userId) {
            localStorage.setItem('userId', userId);
            console.log('userId saved in iframe localStorage:', userId);
        }
    });
        // Wait for the DOM to load
        document.addEventListener("DOMContentLoaded", function () {
            const userID = localStorage.getItem("userID");

            // Send it to Streamlit using an iframe hack
            const streamlitReceiver = window.parent;
            if (streamlitReceiver) {
                streamlitReceiver.postMessage({ type: "userID", value: userID }, "*");
            }
        });
    </script>

    <iframe id="receiver" style="display:none;"></iframe>
    """,
    height=0,  # Hide the component
)

# Placeholder to display userID
userID = st_javascript("localStorage.getItem('userID');")

# --- User ID Input ---
#user_input = st.text_input("UserId", key="userid", label_visibility="collapsed",value=userID)
#user_input = userID
query_params=st.query_params if hasattr(st,"query_params") else st.experimental_get_query_params()
user_input=query_params.get("userID",[None])
# --- Load User Documents ---
@st.cache_data(show_spinner=False)
def load_user_documents(user_id_str):
    db = client[DB_NAME]
    all_docs = []

    for collection_name in COLLECTIONS:
        if not collection_name.strip():
            continue
        collection = db[collection_name]
        try:
            cursor = collection.find({"userId": ObjectId(user_id_str)})
            for doc in cursor:
                doc.pop("_id", None)
                doc.pop("userId", None)
                text = f"[{collection_name}]\n" + "\n".join([f"{k}: {v}" for k, v in doc.items()])
                all_docs.append(Document(page_content=text))
        except Exception as e:
            st.warning(f"⚠️ Error loading `{collection_name}`: {e}")
    return all_docs

# --- Build Chatbot ---
@st.cache_resource
def build_chatbot(_docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = splitter.split_documents(_docs)
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(split_docs, embedding=embeddings)
    retriever = vectorstore.as_retriever()
    qa = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model_name="gpt-3.5-turbo"),
        chain_type="stuff",
        retriever=retriever
    )
    return qa

# --- Chat Interface ---
if user_input:
    status = st.empty()
    try:
        with status.container():
            st.info("⏳ Fetching your documents, please wait...")
            raw_docs = load_user_documents(user_input)

        if not raw_docs:
            status.error("❌ No documents found for this userId.")
        else:
            with status.container():
                st.success("✅ Documents loaded. Setting up your assistant...")

            qa = build_chatbot(raw_docs)
            st.divider()
            st.subheader("💬 Ask me anything about your details:")

            if "messages" not in st.session_state:
                st.session_state.messages = []

            chat_container = st.container()

            # Display previous messages
            with chat_container:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            # Input box
            prompt = st.chat_input("Type your question here...")

            # Handle user input
            if prompt:
                # Append user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                with chat_container.chat_message("user"):
                    st.markdown(prompt)

                # Spinner only during response generation
                with st.spinner("🤔 Thinking..."):
                    response = qa.run(prompt)

                # Append assistant message
                st.session_state.messages.append({"role": "assistant", "content": response})
                with chat_container.chat_message("assistant"):
                    st.markdown(response)

    except Exception as e:
        status.error(f"❌ Error occurred: {str(e)}")
