"""Development entry point: ``python app.py`` (or ``flask --app app run``).

This serves the site locally for previewing. What gets published is the static
build produced by ``freeze.py``.
"""

from royalbliss import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
