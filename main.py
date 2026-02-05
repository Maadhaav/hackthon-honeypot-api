from fastapi import FastAPI, Header, HTTPException
import httpx
import re
import random

app = FastAPI()


API_KEY = "7657657"  


def is_scam_message(text):
    scam_keywords = [
        "kyc", "your account will be blocked", "bank verification",
        "lottery", "urgent", "click the link", "atm update", "refund"
    ]
    return any(k.lower() in text.lower() for k in scam_keywords)


def extract_info(text):
    upi_pattern = r"\b[\w.-]+@[a-zA-Z]+\b"
    bank_pattern = r"\b\d{9,18}\b"
    link_pattern = r"https?://\S+"

    return {
        "upi": re.findall(upi_pattern, text),
        "bank_accounts": re.findall(bank_pattern, text),
        "links": re.findall(link_pattern, text)
    }


def agent_message(prev_scammer_msg, collected_info):
    if not collected_info["upi"] and "upi" in prev_scammer_msg.lower():
        return "I am confused. Can you send the UPI ID again?"

    if not collected_info["bank_accounts"] and "account" in prev_scammer_msg.lower():
        return "What is the exact bank account number?"

    if not collected_info["links"] and "click" in prev_scammer_msg.lower():
        return "This link is not opening. Can you send the correct one?"

    return "Okay sir, what should I do next?"


async def talk_to_scammer(message):
    fake_responses = [
        "Click this link to verify your KYC: http://fake-scam-link.com/login",
        "Send ₹10 to this UPI ID: scammer@ybl",
        "My account number is 987654321234",
        "Please confirm once done."
    ]
    return random.choice(fake_responses)


@app.post("/detect")
async def detect_scam(input: dict, x_api_key: str = Header(None)):

    
     
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    user_msg = input.get("message", "")
    conversation = [{"user": user_msg}]

    scam = is_scam_message(user_msg)

    if not scam:
        return {
            "is_scam": False,
            "response": "Not a scam message",
            "conversation_log": conversation
        }

    collected_info = {"upi": [], "bank_accounts": [], "links": []}

    agent_msg = "Hello, I am facing issues. Please guide me."
    scammer_reply = await talk_to_scammer(agent_msg)

    for _ in range(10):
        conversation.append({"agent": agent_msg})
        conversation.append({"scammer": scammer_reply})

        new_info = extract_info(scammer_reply)
        for k in collected_info:
            collected_info[k].extend(new_info[k])

        if any(collected_info.values()):
            break

        agent_msg = agent_message(scammer_reply, collected_info)
        scammer_reply = await talk_to_scammer(agent_msg)

    return {
        "is_scam": True,
        "scam_type": "Financial Fraud",
        "extracted_data": collected_info,
        "conversation_log": conversation
    }
