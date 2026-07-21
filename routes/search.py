from flask import Blueprint, render_template, request

from utils.search import search


search_bp = Blueprint("search", __name__, url_prefix="/search")


@search_bp.get("/")
def search_view():
    query = request.args.get("q", "").strip()
    results, parsed = search(query)
    return render_template("search.jinja", query=query, results=results, parsed=parsed)
