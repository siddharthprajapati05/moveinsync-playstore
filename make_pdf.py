"""report/recommendations.md -> styled HTML -> PDF via headless Chrome."""
import subprocess
import sys
from pathlib import Path

import markdown

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CSS = """body{font-family:-apple-system,Helvetica,Arial,sans-serif;font-size:9.8pt;line-height:1.36;
color:#1a1a1a;max-width:760px;margin:0 auto}h1{font-size:19pt;margin:0 0 4px}
h2{font-size:13pt;border-bottom:1px solid #ddd;padding-bottom:3px;margin-top:12px;margin-bottom:6px}
h3{font-size:11pt;margin:12px 0 4px}table{border-collapse:collapse;width:100%;font-size:9.5pt}
th,td{border:1px solid #ddd;padding:3px 6px;text-align:left;vertical-align:top}th{background:#f3f3f3}
blockquote{color:#555;border-left:3px solid #ccc;margin:4px 0;padding-left:8px}
ul{margin:4px 0;padding-left:18px}li{margin:1px 0}p{margin:5px 0}@page{size:A4;margin:12mm}"""


def to_html(md_text):
    body = markdown.markdown(md_text, extensions=["tables"])
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"


def build(md_path, pdf_path):
    html_path = Path(pdf_path).with_suffix(".html")
    html_path.write_text(to_html(Path(md_path).read_text()))
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={Path(pdf_path).resolve()}", html_path.resolve().as_uri()],
                   check=True, capture_output=True)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "report/recommendations.md",
          sys.argv[2] if len(sys.argv) > 2 else "report/recommendations.pdf")
