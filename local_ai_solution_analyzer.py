from pathlib import Path
import hashlib, json, os, re, urllib.request

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / ".ai"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")


def read_problem(folder):
    readme = folder / "README.md"
    cpp = sorted(folder.glob("*.cpp"))
    if not readme.exists() or not cpp:
        return None
    r = readme.read_text(encoding="utf-8", errors="ignore")
    c = cpp[0].read_text(encoding="utf-8", errors="ignore")
    title = re.search(r"<h2>.*?>(.*?)</a></h2>", r, re.I | re.S) or re.search(r"<h2>(.*?)</h2>", r, re.I | re.S)
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


def analyze(title, difficulty, question, code):
    prompt = f'''You are a senior competitive programming coach. Analyze the student's C++ LeetCode solution.
Return ONLY valid JSON with exactly these keys:
verdict: ALREADY_OPTIMAL or OPTIMIZATION_AVAILABLE or NO_MEANINGFUL_IMPROVEMENT
optimal_approach: short name
optimal_complexity: Time: ... | Space: ...
why_better: max 3 short sentences
optimized_code: complete correct LeetCode C++ solution
key_learning: one short sentence
Rules: Do not invent an improvement. If the student's asymptotic time and space are already optimal, use ALREADY_OPTIMAL and keep their code unchanged. Prefer standard optimal DSA approaches. Keep optimized_code under 28 lines when reasonably possible.
Problem: {title}
Difficulty: {difficulty}
Question: {question}
Student code:
```cpp
{code}
```'''
    payload = json.dumps({"model": MODEL, "prompt": prompt, "stream": False, "format": "json"}).encode()
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode())
    return json.loads(data["response"])


def main():
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
                if json.loads(out.read_text(encoding="utf-8")).get("source_hash") == digest:
                    continue
            except Exception:
                pass
        try:
            result = analyze(title, difficulty, question, code)
            result["source_hash"] = digest
            result["generated_by"] = "local:" + MODEL
            out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            print("AI analyzed", folder.name)
        except Exception as e:
            print("AI analysis failed for", folder.name, ":", e)
            print("Make sure Ollama is running and the model is installed.")


if __name__ == "__main__":
    main()
