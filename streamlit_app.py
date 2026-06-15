import streamlit as st
import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# 1. 페이지 및 환경 설정
st.set_page_config(page_title="통합 복지 모의계산기 비서", page_icon="🤖")

# Streamlit Secrets에서 OpenRouter API 키 불러오기
try:
    OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
except KeyError as e:
    st.error(f"환경변수 누락: {e}. Streamlit Cloud의 Secrets 설정을 확인하세요.")
    st.stop()

# 2. 로컬 FAISS 벡터 DB 로드 (캐싱 적용)
@st.cache_resource
def load_vectorstore():
    # 지시사항에 맞춰 한국어 전용 sroberta 임베딩 모델 적용
    model_name = "jhgan/ko-sroberta-multitask"
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': False}
    
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
    
    # FAISS DB 로드 (index.faiss, index.pkl)
    vectorstore = FAISS.load_local(".", embeddings, allow_dangerous_deserialization=True)
    return vectorstore

vectorstore = load_vectorstore()
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 3. OpenRouter LLM 초기화 (Llama-3 8B 모델 예시)
llm = ChatOpenAI(
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base="https://openrouter.ai/api/v1",
    model_name="openai/gpt-4o-mini",
    temperature=0.1
)

# 4. 프롬프트 템플릿 설정
system_prompt = (
    "당신은 'bjn.kr 복지 모의계산기' 이용을 돕는 전문 안내원입니다.\n"
    "다음 검색된 문서(컨텍스트)를 바탕으로 사용자의 질문에 친절하고 정확하게 답변하세요.\n"
    "컨텍스트에 없는 내용은 지어내지 말고, 모른다고 답변하세요.\n"
    "1단계부터 4단계까지의 마크다운 가이드라인 양식을 적절히 사용하여 가독성 있게 설명하세요.\n\n"
    "컨텍스트:\n{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
])

# RAG 체인 구성
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# 5. Streamlit 내부 UI 다이어트 (여백, 헤더 제거)
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
    /* Streamlit Cloud 임베드 워터마크 및 Fullscreen 버튼 숨기기 */
    .viewerBadge_container__1JCIV,
    .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK,
    [data-testid="viewerBadge"] {
        display: none !important;
    }
    
    /* iframe 하단의 하얀 툴바/여백 완전 제거 */
    #stApp > div > div {
        padding-bottom: 0px !important;
    }
</style>
""", unsafe_allow_html=True)

# 6. Streamlit UI 및 채팅 로직
st.caption("안내: 계산기 입력 중 헷갈리는 항목을 물어보세요.")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 복지 모의계산기 안내원입니다. 어떤 단계의 입력이 궁금하신가요?"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 처리
if user_input := st.chat_input("질문을 입력해주세요 (예: 월소득은 세전인가요?)"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("답변을 검색 중입니다..."):
            try:
                response = rag_chain.invoke({"input": user_input})
                bot_reply = response["answer"]
                st.markdown(bot_reply)
            except Exception as e:
                bot_reply = f"오류가 발생했습니다: {str(e)}"
                st.error(bot_reply)

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
