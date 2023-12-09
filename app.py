from fastapi import Request, FastAPI,  HTTPException
from src.helper import chatbot
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel
import traceback

class ChatBot(BaseModel):
    query: str


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def hello():
    return "Welcome to Science Chatbot"


@app.post("/chatbot")
def handler(body: ChatBot, request: Request):
    try:
        response = chatbot(body.query)
    except:
        print(dict(body))
        print("Got some error in service")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Got some error in service")

    return {"response": response}
