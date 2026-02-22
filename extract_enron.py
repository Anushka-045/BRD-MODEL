import pandas as pd
import os

INPUT_FILE = "data/emails.csv"
OUTPUT_FILE = "enron_emails.txt"

if not os.path.exists(INPUT_FILE):
    print("emails.csv not found in data folder")
    exit()

print("Reading CSV... (this may take some time)")

df = pd.read_csv(INPUT_FILE)

print("Columns:", df.columns)

emails = []

# The email body column name is usually 'message'
for text in df["message"][:500]:
    if isinstance(text, str):
        # Split headers and body
        parts = text.split("\n\n", 1)
        if len(parts) > 1:
            body = parts[1]
        else:
            body = text

        if len(body) > 50:
            emails.append(body)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for email in emails:
        f.write(email)
        f.write("\n\n---EMAIL_SEPARATOR---\n\n")

print(f"Saved {len(emails)} clean emails")