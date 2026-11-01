"""Dash application factory and local entry point."""

import os

from dash import Dash

from src.callbacks import register_callbacks
from src.data.repository import load_dataset
from src.layout import create_layout
from src.settings import ASSETS


def create_app() -> Dash:
    dataset = load_dataset()
    app = Dash(
        __name__, assets_folder=str(ASSETS), title="Vital Colombia | Mortalidad 2019",
        update_title="Actualizando análisis…", assets_ignore=r"geo/.*",
        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"},
                   {"name": "description", "content": "Explora la mortalidad no fetal de Colombia en 2019 con datos del DANE."}],
    )
    app.index_string = app.index_string.replace('<html>', '<html lang="es">')
    app.layout = create_layout(dataset)
    register_callbacks(app, dataset)

    @app.server.get("/health")
    def health():
        return {"status": "ok", "year": 2019, "records": dataset.quality["records"]}

    return app


app = create_app()
server = app.server

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8050")), debug=os.environ.get("DASH_DEBUG") == "1")

