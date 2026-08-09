# pipeline/gex/render.py
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=False,           # we control all inputs; template emits raw numbers
)
_env.filters["n0"] = lambda v: f"{v:,.0f}" if v is not None else "—"
_env.filters["n2"] = lambda v: f"{v:,.2f}" if v is not None else "—"
_env.filters["pc"] = lambda v: f"{v:.0%}" if v is not None else "—"


def render_brief(doc: dict) -> str:
    return _env.get_template("brief.html.j2").render(d=doc)
