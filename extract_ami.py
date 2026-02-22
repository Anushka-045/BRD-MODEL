import pandas as pd
import os

INPUT_FILE = "data/train_df.csv"
OUTPUT_FILE = "data/meeting_transcripts.txt"

if not os.path.exists(INPUT_FILE):
    print("train_df.csv not found inside data folder")
    exit()

df = pd.read_csv(INPUT_FILE)

# Check column name
print("Columns in dataset:", df.columns)

transcripts = []

# Change column name here if needed
for text in df.iloc[:, 0][:200]:   
    if isinstance(text, str):
        transcripts.append(text)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for t in transcripts:
        f.write(t)
        f.write("\n\n---MEETING_SEPARATOR---\n\n")

print(f"Saved {len(transcripts)} meeting transcripts")