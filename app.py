import streamlit as st
import requests # FastAPI 백엔드와 통신할 경우

st.set_page_config(page_title="통합 복지 모의계산기 비서", page_icon="🤖")

st.title("🤖 Hermes: 복지 모의계산기 도우미")
st.markdown("계산기 입력 중 헷갈리는 항목이 있다면 무엇이든 물어보세요!")

# 세션 상태 초기화 (대화 기록 저장)
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 초기 인사말 설정
    st.session_state.messages.append({"role": "assistant", "content": "안녕하세요! bjn.kr 복지 모의계산기 입력 안내원입니다. 어떤 단계의 입력이 궁금하신가요?"})

# 대화 기록 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 처리
if prompt := st.chat_input("질문을 입력해주세요 (예: 월소득은 세전인가요?)"):
    # 사용자 메시지 화면에 출력 및 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # RAG 엔진 또는 FastAPI 백엔드 호출 (여기서는 예시로 로직 생략)
    # response = requests.post("FastAPI_URL/chat", json={"message": prompt}).json()
    # bot_reply = response["reply"]
    
    # 임시 답변 (실제 로직으로 대체)
    bot_reply = "안내원 마무리 멘트: 다음 단계 입력을 위해 하단의 [다음 단계] 버튼을 눌러주세요!" 

    # 봇 답변 화면에 출력 및 저장
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})