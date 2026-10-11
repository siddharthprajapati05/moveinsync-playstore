from make_pdf import to_html


def test_to_html_renders_tables_and_styles():
    html = to_html("# Title\n\n| a | b |\n|---|---|\n| 1 | 2 |\n")
    assert "<h1>Title</h1>" in html and "<table>" in html and "<style>" in html
