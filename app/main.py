from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from app.config import PERPLEXITY_API_KEY

app=FastAPI()
client = OpenAI(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")

class ChatRequest(BaseModel):
    query : str

@app.get("/ping")
def ping():
    return {"status" : "ok"}

@app.post("/chat")
def  chat(request: ChatRequest):
    response = client.chat.completions.create(
        model="llama-3.1-sonar-small-128k-chat",
        messages=[{"role":"user","content":request.query}]
    )
    return{"reply":response.choices[0].message.content}
