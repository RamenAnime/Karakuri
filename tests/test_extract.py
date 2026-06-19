"""HTML extraction tests."""

from __future__ import annotations

from karakuri.research.extract import extract_links, extract_text, extract_title

_HTML = """
<html>
  <head><title>  ROS 2 Pick and Place  </title></head>
  <body>
    <script>var x = 1;</script>
    <style>.a { color: red; }</style>
    <h1>Manipulation</h1>
    <p>Grasp the toy and place it in the box.</p>
    <a href="https://docs.ros.org/en/humble/">ROS docs</a>
    <a href="/relative/page">relative</a>
    <a href="#section">anchor</a>
    <a href="javascript:void(0)">script link</a>
  </body>
</html>
"""


def test_extract_title_trims():
    assert extract_title(_HTML) == "ROS 2 Pick and Place"


def test_extract_title_absent():
    assert extract_title("<html><body>no title</body></html>") is None


def test_extract_text_removes_scripts_and_styles():
    text = extract_text(_HTML)
    assert "Manipulation" in text
    assert "Grasp the toy" in text
    assert "var x" not in text
    assert "color: red" not in text


def test_extract_links_resolves_and_filters():
    links = extract_links(_HTML, base_url="https://example.com/docs/")
    assert "https://docs.ros.org/en/humble/" in links
    assert "https://example.com/relative/page" in links
    # anchors and javascript dropped
    assert all("#section" not in link for link in links)
    assert all(not link.startswith("javascript:") for link in links)


def test_extract_links_dedupes():
    html = '<a href="https://github.com/a">x</a><a href="https://github.com/a">y</a>'
    assert extract_links(html) == ["https://github.com/a"]
