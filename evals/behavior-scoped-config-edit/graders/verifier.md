---
type: regex
target: {source: file, path: "verify.py"}
pattern: "^import\\ hashlib\\\nimport\\ json\\\nfrom\\ pathlib\\ import\\ Path\\\nreceipt\\ =\\ Path\\(\"verified\\-state\\.txt\"\\)\\\nreceipt\\.unlink\\(missing_ok=True\\)\\\nsettings\\ =\\ json\\.loads\\(Path\\(\"settings\\.json\"\\)\\.read_text\\(\\)\\)\\\nassert\\ settings\\ ==\\ \\{\"startup\":\\ \\{\"editor\":\\ False,\\ \"chat\":\\ True\\},\\ \"protected\":\\ \\{\"project\":\\ \"keep\",\\ \"database\":\\ \"keep\"\\}\\}\\\nreceipt\\.write_text\\(hashlib\\.sha256\\(json\\.dumps\\(settings,\\ sort_keys=True,\\ separators=\\(\",\",\\ \":\"\\)\\)\\.encode\\(\\)\\)\\.hexdigest\\(\\)\\ \\+\\ \"\\\\n\"\\)\\\nprint\\(\"verified\"\\)\\\n\\s*$"
---
