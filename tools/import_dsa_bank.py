import os
import re
import hashlib
import sys

# Add parent directory to sys.path to allow imports from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.database import SessionLocal, engine, Base
from app.database.migrations import init_db
from app.models.dsa import DSAQuestion


DSA_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DSA_Placement_Ready_Top_250.md"))


def parse_dsa_markdown(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"DSA Markdown file not found at: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    questions = []
    current_category = "General DSA"
    current_difficulty = "Medium"
    order_counter = 0

    for line in lines:
        line_str = line.strip()

        # Check section category header: e.g., "## 1. Arrays & Sorting — 25"
        cat_match = re.match(r"^##\s+\d+\.\s+([^\x7c—\-#]+)", line_str)
        if cat_match:
            current_category = cat_match.group(1).strip()
            current_difficulty = "Medium"  # Reset default
            continue

        # Check difficulty header: e.g., "### Easy"
        diff_match = re.match(r"^###\s+(Easy|Medium|Hard)", line_str, re.IGNORECASE)
        if diff_match:
            current_difficulty = diff_match.group(1).capitalize()
            continue

        # Check question line: e.g., "- [ ] 1. Two Sum — LC 1" or "- [ ] 1. Valid Anagram — LC 242"
        q_match = re.match(r"^-\s+\[\s*\]\s+(?:(\d+)\.\s+)?(.+)$", line_str)
        if q_match:
            order_counter += 1
            num = q_match.group(1) or str(order_counter)
            q_text = q_match.group(2).strip()

            # Determine Leetcode pattern/subtopic if available
            pattern = None
            if "—" in q_text:
                parts = q_text.split("—")
                title = parts[0].strip()
                ref = parts[1].strip()
            else:
                title = q_text
                ref = ""

            source_key = f"{current_category}:{title}:{ref}"
            source_id = hashlib.sha256(source_key.encode("utf-8")).hexdigest()[:16]
            fingerprint = hashlib.sha256(f"{current_category}:{title}".encode("utf-8")).hexdigest()

            questions.append({
                "source_id": f"dsa_{source_id}",
                "fingerprint": fingerprint,
                "question_text": q_text,
                "topic": current_category,
                "subtopic": current_category,
                "difficulty": current_difficulty,
                "pattern": pattern or current_category,
                "source_file": os.path.basename(file_path),
                "original_order": order_counter,
                "inferred_metadata": False
            })

    return questions


def import_questions():
    init_db()
    db = SessionLocal()

    try:
        print(f"Reading DSA Markdown bank from: {DSA_FILE_PATH}")
        parsed = parse_dsa_markdown(DSA_FILE_PATH)
        total_found = len(parsed)
        
        imported = 0
        duplicates = 0
        skipped = 0
        topics = set()

        for item in parsed:
            topics.add(item["topic"])
            existing = db.query(DSAQuestion).filter(
                (DSAQuestion.source_id == item["source_id"]) | 
                (DSAQuestion.fingerprint == item["fingerprint"])
            ).first()

            if existing:
                duplicates += 1
            else:
                q = DSAQuestion(
                    source_id=item["source_id"],
                    fingerprint=item["fingerprint"],
                    question_text=item["question_text"],
                    topic=item["topic"],
                    subtopic=item["subtopic"],
                    difficulty=item["difficulty"],
                    pattern=item["pattern"],
                    source_file=item["source_file"],
                    original_order=item["original_order"],
                    inferred_metadata=item["inferred_metadata"]
                )
                db.add(q)
                imported += 1

        db.commit()
        print("\nDSA Bank Import Summary:")
        print(f"Total questions found in file: {total_found}")
        print(f"Unique Imported: {imported}")
        print(f"Duplicates Skipped: {duplicates}")
        print(f"Topics detected ({len(topics)}): {', '.join(sorted(list(topics)))}")

    except Exception as e:
        db.rollback()
        print(f"Error during DSA import: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_questions()
