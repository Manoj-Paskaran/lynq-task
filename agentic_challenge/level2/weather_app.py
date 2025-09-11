import asyncio
import os
import sys

import streamlit as st
from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client import StdioTransport
from google import genai
from google.genai.types import GenerateContentConfig

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

SYSTEM_PROMPT = """
You are a helpful assistant that provides weather information.
You have access to a tool that can fetch current weather data for any city in any country in the world.
When you need to provide weather information, use the tool to get the latest data.
If there are multiple cities with the same name, you can specify the country code to disambiguate (e.g., "London,GB" vs "London,CA").
If the user does not specify a country, you may choose the most well-known city with that name.
Be sure to cite the city and country in your response.
If the user asks to list the weather of multiple cities, use the tool for each city and compile the results into a single response.
"""


gemini_client = genai.Client(api_key=GEMINI_API_KEY)

mcp_client = Client(
    transport=StdioTransport(
        command=sys.executable,
        args=["-m", "agentic_challenge.level2.weather_mcp"],
        env={"OPENWEATHER_API_KEY": OPENWEATHER_API_KEY},
    )
)


async def ask_gemini(prompt: str) -> str:
    """Open an MCP stdio session to the weather server and ask Gemini with that tool enabled."""

    async with mcp_client:
        response = await gemini_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=GenerateContentConfig(
                tools=[mcp_client.session], system_instruction=SYSTEM_PROMPT
            ),
        )
        return getattr(response, "text", "")


def main():
    st.set_page_config(page_title="Weather Agent", page_icon="☁", layout="wide")
    st.title("Weather Agent (Gemini)")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Replay prior conversation
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Ask about the weather (e.g., Is it raining in Hyderabad today?)"
    )
    if prompt:
        # Show user turn
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Synchronous call that runs async under the hood
        with st.chat_message("assistant"):
            try:
                response_text = asyncio.run(ask_gemini(str(st.session_state.messages)))
                st.markdown(response_text or "")
            except Exception as e:
                response_text = f"Error: {e}"
                st.error(response_text)

        # Persist assistant turn
        st.session_state.messages.append(
            {"role": "assistant", "content": response_text or ""}
        )


if __name__ == "__main__":
    main()
