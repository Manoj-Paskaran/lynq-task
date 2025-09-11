import os

import gradio as gr
from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig, UploadFileConfig

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY is None:
    raise ValueError(
        "GEMINI_API_KEY environment variable not set\nPlease set a valid API key"
    )

SYSTEM_PROMPT = """
You are a PDF summarization assistant. You will receive one PDF attached via the Files API.
Follow these rules:
- Be concise and factual; do not invent details. If the PDF doesn't contain the answer, say so
- Provide a structured summary
- End with a 1-2 sentence TL;DR
- If the user asks a specific question, answer it directly first, then support it with evidence from the PDF.
- Cite page numbers when you quote or refer to specific parts (e.g., “...” (p. 5)) if available.
- Prefer bullet points and short paragraphs. Keep under ~100-200 words unless the user asks for more.
"""


class GeminiPDFChat:
    def __init__(self):
        self.client = genai.Client(
            api_key=GEMINI_API_KEY,
        )
        self.file_uploaded = False
        self.uploaded_file = None

    def upload_pdf(self, pdf_file):
        if self.file_uploaded is False:
            self.uploaded_file = self.client.files.upload(
                file=pdf_file, config=UploadFileConfig()
            )
            self.file_uploaded = True
            return self.uploaded_file

        return self.uploaded_file

    def ask_gemini(self, prompt, history: list[dict]):
        text = prompt.get("text", "")
        files = prompt.get("files", [])

        if self.file_uploaded is False and files == []:
            yield "Upload a PDF File to be summarized."
            return

        if files:
            file = files[0]
            self.uploaded_file = self.upload_pdf(pdf_file=file)

        try:
            user_history = []
            for chat in history:
                role = chat.get("role")
                content = chat.get("content")
                if role == "user" and isinstance(content, str):
                    user_history.append(content)

            user_history = "\n".join(user_history)
        except Exception as e:
            print(history)
            print(e)
            pass

        try:
            stream = self.client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=[text, self.uploaded_file],  # type: ignore
                config=GenerateContentConfig(
                    system_instruction=(SYSTEM_PROMPT + f"Chat History: {history}")
                ),
            )
            partial = ""
            for chunk in stream:
                text_piece = getattr(chunk, "text", "") or ""
                if text_piece:
                    partial += text_piece
                    yield partial

        except Exception as e:
            yield f"Error: {str(e)}"
            return


gemini_pdf_chat = GeminiPDFChat()


def main():
    ui = gr.ChatInterface(
        fn=gemini_pdf_chat.ask_gemini,
        type="messages",
        multimodal=True,
        title="PDF Summarizer",
        textbox=gr.MultimodalTextbox(
            file_count="multiple",
            file_types=["application/pdf", ".pdf", "pdf"],
            sources=["upload"],
            placeholder="Type a question or drop PDFs here…",
        ),
    )

    ui.queue()
    ui.launch()


if __name__ == "__main__":
    main()
