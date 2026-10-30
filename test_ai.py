
import streamlit as st
from google import genai

api_key = st.secrets["GEMINI_API_KEY"]

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Reply with exactly: MindTrace AI is connected."
)

print(response.text)
