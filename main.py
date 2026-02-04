from fastapi import FastAPI, Header
import httpx
import re

app = FastAPI()

MOCK_SCAMMER_API = "https://mock-scammer.guvi/api/reply"   # They will give actual URL

# ----------- 1. SIMPLE SCAM DETECTION ----------------
def is_scam_message(text):
    scam_keywords = [
        "kyc", "your account will be blocked", "bank verification",
        "lottery", "urgent", "click the link", "atm update", "refund"
    ]
    return any(k.lower() in text.lower() for k in scam_keywords)


# ----------- 2. EXTRACT UPI, BANK ACCOUNT, LINKS ---------------
def extract_info(text):
    upi_pattern = r"\b[\w.-]+@[a-zA-Z]+\b"
    bank_pattern = r"\b\d{9,18}\b"
    link_pattern = r"https?://\S+"

    return {
        "upi": re.findall(upi_pattern, text),
        "bank_accounts": re.findall(bank_pattern, text),
        "links": re.findall(link_pattern, text)
    }


# ----------- 3. AGENT (LLM / RULE-BASED) ----------------
def agent_message(prev_scammer_msg, collected_info):
    if not collected_info["upi"] and "UPI" in prev_scammer_msg:
        return "I am confused, can you give me the UPI ID properly?"

    if not collected_info["bank_accounts"] and "account" in prev_scammer_msg:
        return "Where exactly should I transfer? Can you send the bank account number?"

    if not collected_info["links"] and "click" in prev_scammer_msg:
        return "This link is not opening, can you send the correct link?"

    return "Okay sir, I am ready. What should I do next?"


# ----------- 4. SEND MESSAGE TO MOCK SCAMMER -------------
async def talk_to_scammer(message):
    # Temporary fake scammer responses for local testing
    fake_responses = [
        "Click this link to verify your KYC: http://fake-scam-link.com/login",
        "Send ₹10 to this UPI ID: scammer@ybl",
        "My account number is 987654321234",
        "Please confirm once done.",
    ]

    import random
    return random.choice(fake_responses)



# ----------- 5. MAIN /detect ENDPOINT --------------------
@app.post("/detect")
async def detect_scam(input: dict, Authorization: str = Header(None)):

    user_msg = input.get("message", "")

    # STEP 1: Scam detection
    scam = is_scam_message(user_msg)
    conversation = [{"user": user_msg}]

    if not scam:
        return {
            "is_scam": False,
            "response": "This message does not appear to be a scam.",
            "conversation_log": conversation
        }

    # STEP 2: Agentic Loop
    collected_info = {"upi": [], "bank_accounts": [], "links": []}

    agent_msg = "Hello, I am facing issues. Please guide me."
    scammer_reply = await talk_to_scammer(agent_msg)

    for _ in range(10):  # max 10-turn conversation
        conversation.append({"agent": agent_msg})
        conversation.append({"scammer": scammer_reply})

        # Extract intelligence
        new_info = extract_info(scammer_reply)
        for k in collected_info:
            collected_info[k].extend(new_info[k])

        # If info collected → stop
        if any(collected_info.values()):
            break

        # Generate next agent message
        agent_msg = agent_message(scammer_reply, collected_info)
        scammer_reply = await talk_to_scammer(agent_msg)

    # STEP 3: Return final structured JSON
    return {
        "is_scam": True,
        "scam_type": "Financial Fraud",
        "extracted_data": collected_info,
        "conversation_log": conversation
    }
