from pathlib import Path

path = Path("docs/learning-guide-fa.md")
raw = path.read_bytes()
content = raw.decode("utf-8-sig")
start = content.rfind("\n### ")
if start < 0:
    raise SystemExit("Expected final heading not found. No changes made.")
tail = content[start + 1:]
if len(tail) > 1600 or not all(token in tail for token in ("TPConditions", "PR", " K ", "OK")):
    raise SystemExit("Final section differs from expected. No changes made.")
replacement = '### \u062a\u0623\u06cc\u06cc\u062f \u0627\u062c\u0631\u0627\u06cc \u06cc\u06a9\u067e\u0627\u0631\u0686\u0647 \u0631\u0648\u06cc \u0644\u067e\u200c\u062a\u0627\u067e\n\u062f\u0631 \u06f9 \u0627\u06a9\u062a\u0628\u0631 \u06f2\u06f0\u06f2\u06f6\u060c \u0645\u062c\u0645\u0648\u0639\u0647\u0654 \u06f4\u06f9 \u0622\u0632\u0645\u0648\u0646 \u062f\u0631 \u06f0\u066b\u06f0\u06f8\u06f5 \u062b\u0627\u0646\u06cc\u0647 \u0628\u0627 \u0646\u062a\u06cc\u062c\u0647\u0654 OK \u0627\u062c\u0631\u0627 \u0634\u062f.\n\u0634\u0634 \u0622\u0632\u0645\u0648\u0646 \u0631\u0627\u0686\u0641\u0648\u0631\u062f\u2013\u0631\u0627\u06cc\u0633 \u0647\u0645\u0631\u0627\u0647 \u06f4\u06f3 \u0622\u0632\u0645\u0648\u0646 \u0642\u0628\u0644\u06cc \u0645\u0648\u0641\u0642 \u0628\u0648\u062f\u0646\u062f.\n\u0622\u0632\u0645\u0648\u0646\u200c\u0647\u0627\u06cc TPConditions \u062f\u0631 \u0627\u06cc\u0646 \u0627\u062c\u0631\u0627 \u062d\u0636\u0648\u0631 \u0646\u062f\u0627\u0634\u062a\u0646\u062f.\n\u0627\u06cc\u0646 \u0646\u062a\u06cc\u062c\u0647\u060c \u0631\u0641\u062a\u0627\u0631\u0647\u0627\u06cc \u0622\u0632\u0645\u0648\u062f\u0647\u200c\u0634\u062f\u0647\u0654 \u062d\u0644\u200c\u06af\u0631 \u0628\u0627 K \u0645\u0634\u062e\u0635 \u0631\u0627 \u062a\u0623\u06cc\u06cc\u062f \u0645\u06cc\u200c\u06a9\u0646\u062f\u061b\n\u0641\u0644\u0634 \u0645\u0628\u062a\u0646\u06cc \u0628\u0631 PR \u0648 \u067e\u0627\u06cc\u062f\u0627\u0631\u06cc \u0641\u0627\u0632\u06cc \u0647\u0646\u0648\u0632 \u067e\u06cc\u0627\u062f\u0647\u200c\u0633\u0627\u0632\u06cc \u0646\u0634\u062f\u0647\u200c\u0627\u0646\u062f.\n'
if "?" not in tail:
    print("Final section has no question marks. No changes made.")
else:
    if any(ord(char) > 127 for char in tail):
        raise SystemExit("Mixed text detected. Review needed; no changes made.")
    newline = "\r\n" if b"\r\n" in raw else "\n"
    replacement = replacement.replace("\n", newline)
    updated = content[:start + 1] + replacement
    bom = b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b""
    path.write_bytes(bom + updated.encode("utf-8"))
    print("Repaired only the final test-result section in UTF-8.")
