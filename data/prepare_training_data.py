import json

INPUT_FILE = "data/multichannel_data.txt"
OUTPUT_FILE = "data/brd_training.jsonl"

def create_dummy_brd(text):
    # Simple BRD structure (can be improved later)
    return {
        "executive_summary": "Project requirements extracted from communications.",
        "business_objectives": ["Improve system functionality"],
        "stakeholders": ["Client", "Project Manager", "Development Team"],
        "functional_requirements": ["Feature implementation based on discussion"],
        "non_functional_requirements": ["Performance", "Security"],
        "assumptions": ["Requirements may evolve"],
        "timeline": "To be finalized",
        "conflicts": []
    }

samples = []

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    content = f.read().split("============================")

for text in content[:50]:
    text = text.strip()
    if not text:
        continue

    sample = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": text}]
            },
            {
                "role": "model",
                "parts": [{"text": json.dumps(create_dummy_brd(text))}]
            }
        ]
    }

    samples.append(sample)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for s in samples:
        f.write(json.dumps(s) + "\n")

print(f"Created {len(samples)} training samples")