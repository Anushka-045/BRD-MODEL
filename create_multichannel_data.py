import os

EMAIL_FILE = "enron_emails.txt"
MEETING_FILE = "data/meeting_transcripts.txt"
CHAT_FILE = "data/chat_messages.txt"

OUTPUT_FILE = "data/multichannel_data.txt"

# Check files
for file in [EMAIL_FILE, MEETING_FILE, CHAT_FILE]:
    if not os.path.exists(file):
        print(f"{file} not found")
        exit()

# Load data
with open(EMAIL_FILE, "r", encoding="utf-8") as f:
    emails = f.read().split("---EMAIL_SEPARATOR---")

with open(MEETING_FILE, "r", encoding="utf-8") as f:
    meetings = f.read().split("---MEETING_SEPARATOR---")

with open(CHAT_FILE, "r", encoding="utf-8") as f:
    chats = f.readlines()

samples = []

# Create 100 multi-channel samples
for i in range(100):
    email = emails[i].strip() if i < len(emails) else ""
    meeting = meetings[i].strip() if i < len(meetings) else ""
    chat = chats[i].strip() if i < len(chats) else ""

    combined = f"""
--- EMAIL CHANNEL ---
{email}

--- MEETING CHANNEL ---
{meeting}

--- CHAT CHANNEL ---
{chat}

============================
"""
    samples.append(combined)

# Save
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for sample in samples:
        f.write(sample)

print(f"Created {len(samples)} multi-channel samples")