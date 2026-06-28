#!/usr/bin/env python3
"""
Render Markdown report(s) into standalone, self-contained HTML you can open in any
browser on your HOST machine.

Why this works headless: the data/ folder is bind-mounted, so a report the AI writes
INSIDE the container also lands in the repo folder on your computer — convert it here,
then just double-click the .html on your host (no VS Code, no internet needed; the CSS
is embedded).

    python scripts/md2html.py data/<account>/analysis/REPORT.md
    python scripts/md2html.py data/<account>/analysis        # every .md in a folder

Writes <name>.html next to each .md.
"""
import os
import sys

try:
    import markdown
except ImportError:
    sys.exit("!! needs the 'markdown' package — it's in requirements.txt "
             "(rebuild the container, or `pip install markdown`).")

CSS = """<style>
  :root { color-scheme: light dark; }
  body { margin: 0; background: #f6f8fa; }
  @media (prefers-color-scheme: dark) { body { background: #0d1117; } }
  .md { max-width: 880px; margin: 2.5rem auto; padding: 2.5rem 3rem;
        background: #fff; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.08);
        font: 16px/1.6 -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
        color: #1f2328; }
  @media (prefers-color-scheme: dark) { .md { background: #161b22; color: #e6edf3;
        box-shadow: none; border: 1px solid #30363d; } }
  .md h1, .md h2 { border-bottom: 1px solid #d0d7de; padding-bottom: .3em; }
  .md h1 { font-size: 1.9em; } .md h2 { font-size: 1.4em; margin-top: 1.8em; }
  .md code { background: rgba(127,127,127,.18); padding: .15em .4em; border-radius: 5px;
        font: .88em ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
  .md pre { background: rgba(127,127,127,.12); padding: 1em; border-radius: 8px;
        overflow-x: auto; } .md pre code { background: none; padding: 0; }
  .md table { border-collapse: collapse; width: 100%; margin: 1em 0; }
  .md th, .md td { border: 1px solid #d0d7de; padding: 6px 13px; text-align: left; }
  .md th { background: rgba(127,127,127,.12); }
  .md blockquote { margin: 1em 0; padding: .2em 1em; color: #57606a;
        border-left: 4px solid #d0d7de; }
  .md a { color: #0969da; }
</style>"""

TEMPLATE = ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<title>{title}</title>{css}</head>"
            "<body><article class='md'>{body}</article></body></html>")


def render(path):
    body = markdown.markdown(
        open(path, encoding="utf-8").read(),
        extensions=["extra", "sane_lists", "toc", "nl2br"])
    out = os.path.splitext(path)[0] + ".html"
    title = os.path.basename(os.path.splitext(path)[0])
    with open(out, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(title=title, css=CSS, body=body))
    return out


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python scripts/md2html.py <file.md | directory>")
    target = sys.argv[1]
    if os.path.isdir(target):
        files = [os.path.join(target, f) for f in sorted(os.listdir(target))
                 if f.endswith(".md")]
    elif target.endswith(".md") and os.path.isfile(target):
        files = [target]
    else:
        sys.exit(f"!! '{target}' is not a .md file or a directory")
    if not files:
        sys.exit("!! no .md files found")
    for f in files:
        print(">> wrote", render(f))
    print(">> open the .html in your browser — it's on your host via the data/ mount.")


if __name__ == "__main__":
    main()
