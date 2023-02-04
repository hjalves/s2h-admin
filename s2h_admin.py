#!/usr/bin/env python
import os
import shlex
import sys
import xml.etree.ElementTree as ET
from functools import partial
from pathlib import Path
from string import Template

THIS_DIR = Path(__file__).resolve().parent
ENV_FILE = THIS_DIR / "s2h.env"
PAGES = {}

# Templates and CSS

CSS = """
/* Body */
html {
  font-size: 50%;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
}
body {
  font-size: 1.8rem;
  line-height: 1.618;
  max-width: 50em;
  margin: auto;
  color: #c9c9c9;
  background-color: #222222;
  padding: 13px;
}
@media (max-width: 684px) {
  body {
    font-size: 1.53rem;
  }
}
@media (max-width: 382px) {
  body {
    font-size: 1.35rem; 
  } 
}
h1, h2, h3, h4, h5, h6 {
  line-height: 1.1;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
  font-weight: 700;
  margin-top: 3rem;
  margin-bottom: 1.5rem;
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
  hyphens: auto;
}
h1 {
  font-size: 2.35em;
}
h2 {
  font-size: 2.00em;
}
h3 {
  font-size: 1.75em;
}
h4 {
  font-size: 1.5em;
}
h5 {
  font-size: 1.25em;
}
h6 {
  font-size: 1em;
}
p {
  margin-top: 0px;
  margin-bottom: 2.5rem;
}
small, sub, sup {
  font-size: 75%;
}
hr {
  border-color: #ffffff;
}
a {
  text-decoration: none;
  color: #ffffff; }
  a:hover {
    color: #c9c9c9;
    border-bottom: 2px solid #c9c9c9;
}
ul {
  padding-left: 1.4em;
  margin-top: 0px;
  margin-bottom: 2.5rem;
}
li {
  margin-bottom: 0.4em;
}
blockquote {
  margin-left: 0px;
  margin-right: 0px;
  padding-left: 1em;
  padding-top: 0.8em;
  padding-bottom: 0.8em;
  padding-right: 0.8em;
  border-left: 5px solid #ffffff;
  margin-bottom: 2.5rem;
  background-color: #4a4a4a;
}
blockquote p {
  margin-bottom: 0;
}
img {
  height: auto;
  max-width: 100%;
  margin-top: 0px;
  margin-bottom: 2.5rem;
}
/* Pre and Code */
pre {
  background-color: #4a4a4a;
  display: block;
  padding: 1em;
  overflow-x: auto;
  margin-top: 0px;
  margin-bottom: 2.5rem;
}
code {
  font-size: 0.9em;
  padding: 0 0.5em;
  background-color: #4a4a4a;
  white-space: pre-wrap;
}
pre > code {
  padding: 0;
  background-color: transparent;
  white-space: pre;
}
/* Tables */
table {
  text-align: justify;
  width: 100%;
  border-collapse: collapse;
}
td, th {
  padding: 0.5em;
  border-bottom: 1px solid #4a4a4a;
}
/* Buttons, forms and input */
input, textarea {
  border: 1px solid #c9c9c9;
}
input:focus, textarea:focus {
  border: 1px solid #ffffff;
}
textarea {
  width: 100%;
}
.button, button, input[type="submit"], input[type="reset"], input[type="button"] {
  display: inline-block;
  padding: 5px 10px;
  text-align: center;
  text-decoration: none;
  white-space: nowrap;
  background-color: #ffffff;
  color: #222222;
  border-radius: 1px;
  border: 1px solid #ffffff;
  cursor: pointer;
  box-sizing: border-box;
}
.button[disabled], button[disabled], input[type="submit"][disabled], input[type="reset"][disabled], input[type="button"][disabled] {
  cursor: default;
  opacity: .5;
}
.button:focus:enabled, .button:hover:enabled, button:focus:enabled, button:hover:enabled, input[type="submit"]:focus:enabled, input[type="submit"]:hover:enabled, input[type="reset"]:focus:enabled, input[type="reset"]:hover:enabled, input[type="button"]:focus:enabled, input[type="button"]:hover:enabled {
  background-color: #c9c9c9;
  border-color: #c9c9c9;
  color: #222222;
  outline: 0;
}
textarea, select, input[type] {
  color: #c9c9c9;
  padding: 6px 10px;
  /* The 6px vertically centers text on FF, ignored by Webkit */
  margin-bottom: 10px;
  background-color: #4a4a4a;
  border: 1px solid #4a4a4a;
  border-radius: 4px;
  box-shadow: none;
  box-sizing: border-box;
}
textarea:focus, select:focus, input[type]:focus {
  border: 1px solid #ffffff;
  outline: 0;
}
input[type="checkbox"]:focus {
  outline: 1px dotted #ffffff;
}
label, legend, fieldset {
  display: block;
  margin-bottom: .5rem;
  font-weight: 600;
}
"""

HTML_TEMPLATE = Template(
    f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Admin > $title</title>
<style>{CSS}</style>
</head>
<body>
<nav>$navigation<hr></nav>
<main><h1>$title</h1>
$content
</main>
<footer>$footer</footer>
</body>
</html>"""
)


# HTML generation tools


class HtmlElement:
    def __init__(self, tag, *elems, **attrib):
        self.tag = tag
        self.elems = elems
        self.attrib = {k.strip("_"): str(v) for k, v in attrib.items()}

    def __call__(self, *elems):
        elem = ET.Element(self.tag, self.attrib)
        for arg in self.elems + elems:
            if arg is not None:
                if isinstance(arg, ET.Element):
                    elem.append(arg)
                elif isinstance(arg, HtmlElement):
                    elem.append(arg())
                elif len(elem) == 0:
                    elem.text = (elem.text or "") + str(arg)
                else:
                    elem[-1].tail = str(arg)
        return elem


class Html:
    def __getattr__(self, item):
        return partial(HtmlElement, item)

    @staticmethod
    def render(elem):
        return ET.tostring(elem, "unicode")


h = Html()


# Page routing logic


def page(page_key, title=None):
    def decorator(func):
        page_title = title or func.__name__.replace("_", " ").title()
        PAGES[page_key] = func, page_title
        return func

    return decorator


def page_router(variables):
    variables = dict(variables)
    page_key = variables.pop("page", next(iter(PAGES)))
    page_tup = PAGES.get(page_key)
    if not page_tup:
        return "Page not found", "<p>Could not find the page requested</p>"
    page_func, page_title = page_tup
    return page_title, page_func(**variables)


# Pages


@page("routing")
def routing(submit=None, **form):
    settings = parse_env_file(ENV_FILE.read_text())

    if submit:
        settings["SH_ROUTES"] = encode_routes(parse_routes_from_form(form))
        ENV_FILE.write_text(encode_env_file(settings))

    routes = parse_routes(settings.get("SH_ROUTES", ""))

    form = h.form(method="post")(
        h.fieldset(
            h.legend("Command routing"),
            h.table(
                h.thead(h.tr(h.th("Path"), h.th("Command"), h.th("Run"))),
                h.tbody(*routing_render_rows(routes)),
            ),
            h.br(),
            h.input(type="submit", name="submit", value="Save"),
            " ",
            h.input(type="reset", value="Reset"),
        ),
    )
    return Html.render(form)


def routing_render_rows(routes, extra=1):
    route_list = [
        (num, path, command) for num, (path, command) in enumerate(routes.items())
    ] + [(i, "", "") for i in range(len(routes), len(routes) + extra)]

    return [
        h.tr(
            h.td(h.input(id=f"path_{i}", name=f"path_{i}", type="text", value=path)),
            h.td(
                h.input(id=f"com_{i}", name=f"com_{i}", type="text", value=com, size=40)
            ),
            h.td(
                h.input(type="button", onclick=f"window.open('{path}');", value="Go")
                if path
                else "-"
            ),
        )
        for (i, path, com) in route_list
    ]


@page("auth")
def authentication(submit=None, username="", password=""):
    settings = parse_env_file(ENV_FILE.read_text())

    if submit:
        settings["SH_BASIC_AUTH"] = (
            f"{username}:{password}" if username and password else ""
        )
        ENV_FILE.write_text(encode_env_file(settings))

    username, _, password = settings.get("SH_BASIC_AUTH", "").partition(":")

    form = h.form(method="post")(
        h.fieldset(
            h.legend("Basic authorization"),
            h.label(for_="username")("Username"),
            h.input(
                id="username",
                name="username",
                type="text",
                value=username,
                placeholder="leave blank to disable",
            ),
            h.label(for_="password")("Password"),
            h.input(
                id="password",
                name="password",
                type="password",
                value=password,
                placeholder="leave blank to disable",
            ),
            h.br(),
            h.input(type="submit", name="submit", value="Save"),
            " ",
            h.input(type="reset", value="Reset"),
        ),
    )
    return Html.render(form)


# Parse and encode utils


def parse_env_file(contents):
    variables = {}
    for line in contents.splitlines():
        env, sep, value = line.partition("=")
        if sep:
            variables[env] = value
    return variables


def encode_env_file(variables):
    return "\n".join(f"{env}={value}" for env, value in variables.items())


def parse_routes(value):
    arguments = shlex.split(value)
    paths, commands = arguments[::2], arguments[1::2]
    return dict(zip(paths, commands))


def encode_routes(routes):
    arguments = []
    for key, value in routes.items():
        arguments.extend((key, value))
    return shlex.join(arguments)


def parse_routes_from_form(form_data):
    routes = {}
    path_keys = sorted(k for k in form_data if k.startswith("path_"))
    for key in path_keys:
        if route := form_data.get(key):
            num = int(key[5:])
            command = form_data.get(f"com_{num}", "")
            routes[route] = command
    return routes


# Main and render


def render():
    input_data = {k[2:]: v for k, v in os.environ.items() if k.startswith("v_")}
    title, content = page_router(input_data)
    navigation = render_navigation()
    return HTML_TEMPLATE.substitute(
        {
            "title": title,
            "navigation": navigation,
            "content": content,
            "footer": footer(),
        }
    )


def render_navigation():
    links = [("[ shell2http ]", "../")] + [
        (page_title, f"?page={page_key}")
        for page_key, (page_func, page_title) in PAGES.items()
    ]
    return " | ".join(f'<a href="{href}">{name}</a>' for name, href in links)


def env_debug():
    return "\n".join(f"{k}={v}" for k, v in os.environ.items())


def footer():
    return f"""<hr>
    <details>
    <summary>env vars</summary>
    <pre><code>{env_debug()}</code></pre>
    </details>
    """


def main(args):
    html_output = render()
    print(html_output)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
