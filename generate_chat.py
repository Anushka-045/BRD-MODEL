import os
import random

INPUT_FILE = "enron_emails.txt"
OUTPUT_FILE = "data/chat_messages.txt"

roles = ["PM", "Developer", "QA", "Manager", "Client"]

if not os.path.exists(INPUT_FILE):
    print("enron_emails.txt not found")
    exit()

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    emails = f.read().split("---EMAIL_SEPARATOR---")

chat_messages = []

for email in emails:
    email = email.strip()
    if not email:
        continue

    # Take first meaningful part of email
    message = email.replace("\n", " ")[:200]

    role = random.choice(roles)
    chat_line = f"[Slack][{role}]: {message}"

    chat_messages.append(chat_line)

# Save chats
os.makedirs("data", exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for msg in chat_messages:
        f.write(msg + "\n")

print(f"Saved {len(chat_messages)} chat messages")