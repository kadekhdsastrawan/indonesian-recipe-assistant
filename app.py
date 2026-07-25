import streamlit as st
from recipe_assistant.db import save_feedback
from recipe_assistant.rag import RecipeAssistant

st.set_page_config(page_title="Indonesian Recipe Assistant", page_icon="🍛")
st.title("🍛 Indonesian Recipe Assistant")
st.caption("Ask in English about Indonesian dishes, ingredients, substitutions, or cooking methods.")
if "messages" not in st.session_state: st.session_state.messages = []
if "assistant" not in st.session_state: st.session_state.assistant = RecipeAssistant()
show_debug = st.sidebar.toggle("Show retrieval details", False)
for message in st.session_state.messages:
    with st.chat_message(message["role"]): st.markdown(message["content"])
query = st.chat_input("e.g. How do I make a vegetarian Indonesian dinner?")
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"): st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner("Searching Indonesian recipes..."):
            try:
                answer, results, event_id = st.session_state.assistant.answer(query, st.session_state.messages[:-1])
                st.markdown(answer)
                st.session_state.last = {"event_id": event_id, "results": results}
            except Exception as error:
                st.error("The assistant could not complete that request. Please check the database and API configuration.")
                answer, results = "", []
    st.session_state.messages.append({"role": "assistant", "content": answer})
if "last" in st.session_state:
    cols = st.columns(2)
    if cols[0].button("👍 Helpful", key="up"):
        save_feedback(st.session_state.last["event_id"], 1); st.success("Thanks for the feedback!")
    if cols[1].button("👎 Not helpful", key="down"):
        save_feedback(st.session_state.last["event_id"], -1); st.info("Thanks. Your feedback was recorded.")
    comment = st.text_input("Optional feedback comment")
    if comment and st.button("Save comment"): save_feedback(st.session_state.last["event_id"], -1, comment); st.success("Comment saved")
    if show_debug:
        st.sidebar.json([{"id": r.recipe.recipe_id, "dish": r.recipe.dish_name, "score": r.score, "method": r.method} for r in st.session_state.last["results"]])
