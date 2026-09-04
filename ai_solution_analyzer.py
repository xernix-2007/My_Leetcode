from pathlib import Path
import hashlib, json, os, re, time, urllib.request

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / ".ai"
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
API_URL = "https://api.openai.com/v1/responses"


def read_problem(folder):
    readme = folder / "README.md"
    cpp = sorted(folder.glob("*.cpp"))
    if not readme.exists() or not cpp:
        return None
    r = readme.read_text(encoding="utf-8", errors="ignore")
    c = cpp[0].read_text(encoding="utf-8", errors="ignore")
    title = re.search(r"<h2>.*?>(.*?)</a></h2>", r, re.I | re.S)
    if not title:
        title = re.search(r"<h2>(.*?)</h2>", r, re.I | re.S)
    title = re.sub(r"<[^>]+>", "", title.group(1)).strip() if title else folder.name
    difficulty = re.search(r"<h3>(.*?)</h3>", r, re.I | re.S)
    difficulty = re.sub(r"<[^>]+>", "", difficulty.group(1)).strip() if difficulty else ""
    paragraphs = re.findall(r"<p>(.*?)</p>", r, re.I | re.S)
    question = ""
    for p in paragraphs:
        x = re.sub(r"<[^>]+>", " ", p)
        x = re.sub(r"\s+", " ", x).strip()
        if x and not x.lower().startswith(("example", "constraints", "follow-up")):
            question = x
            break
    return title, difficulty, question, c


def call_ai(title, difficulty, question, code):
    prompt = f'''You are a senior competitive-programming coach. Analyze this student's C++ LeetCode solution.
Return ONLY valid JSON with these exact keys:
"verdict": one of "ALREADY_OPTIMAL", "OPTIMIZATION_AVAILABLE", "NO_MEANINGFUL_IMPROVEMENT"
"optimal_approach": short name
"optimal_complexity": "Time: ... | Space: ..."
"why_better": max 3 short sentences
"optimized_code": complete LeetCode C++ solution, concise and correct. If the student's solution is already optimal, return the student's code.
"key_learning": one short sentence.
Do not invent a worse solution. Prefer the standard asymptotically optimal approach. Keep optimized_code under 28 lines when reasonably possible.
Problem: {title}
Difficulty: {difficulty}
Question: {question}
Student code:
```cpp
{code}
```'''
    payload = {"model": MODEL, "input": prompt, "max_output_tokens": 2500}
    req = urllib.request.Request(API_URL, data=json.dumps(payload).encode(), headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode())
    text = data.get("output_text", "")
    if not text:
        for item in data.get("output", []):
            for part in item.get("content", []):
                if part.get("type") in ("output_text", "text"):
                    text += part.get("text", "")
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    return json.loads(text)


def main():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        print("OPENAI_API_KEY is not set; skipping AI analysis.")
        return
    CACHE.mkdir(exist_ok=True)
    for folder in sorted(ROOT.iterdir(), key=lambda p: p.name):
        if not folder.is_dir() or not re.match(r"^\d{4}-", folder.name):
            continue
        item = read_problem(folder)
        if not item:
            continue
        title, difficulty, question, code = item
        digest = hashlib.sha256((title + "\n" + question + "\n" + code).encode()).hexdigest()
        out = CACHE / (folder.name + ".json")
        if out.exists():
            try:
                old = json.loads(out.read_text(encoding="utf-8"))
                if old.get("source_hash") == digest:
                    continue
            except Exception:
                pass
        try:
            result = call_ai(title, difficulty, question, code)
            result["source_hash"] = digest
            result["generated_by"] = MODEL
            out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            print("AI analyzed", folder.name)
            time.sleep(0.5)
        except Exception as e:
            print("AI analysis failed for", folder.name, ":", e)


if __name__ == "__main__":
    main()
