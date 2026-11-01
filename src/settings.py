"""Shared paths and explicit definitions used by the analysis."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PROCESSED = DATA / "processed"
ASSETS = ROOT / "assets"
YEAR = 2019
SCHEMA_VERSION = 1

SOURCE_FILES = {
    "mortality": "Anexo1.NoFetal2019_CE_15-03-23.xlsx",
    "causes": "Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx",
    "territories": "Divipola_CE_.xlsx",
}

MONTHS = (
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
)
SEX_LABELS = {1: "Masculino", 2: "Femenino", 3: "Indeterminado"}

# Disjoint academic groups supplied with the assignment. Codes are not ages.
AGE_GROUPS = (
    ("Neonatal", "Menor de 1 mes", 0, 4),
    ("Infantil", "1–11 meses", 5, 6),
    ("Primera infancia", "1–4 años", 7, 8),
    ("Niñez", "5–14 años", 9, 10),
    ("Adolescencia", "15–19 años", 11, 11),
    ("Juventud", "20–29 años", 12, 13),
    ("Adultez temprana", "30–44 años", 14, 16),
    ("Adultez intermedia", "45–59 años", 17, 19),
    ("Vejez", "60–84 años", 20, 24),
    ("Longevidad", "85 años o más", 25, 28),
    ("Edad desconocida", "Sin información", 29, 29),
)
AGE_CODE_TO_GROUP = {
    code: index
    for index, (_, _, lower, upper) in enumerate(AGE_GROUPS)
    for code in range(lower, upper + 1)
}


def source_path(key: str) -> Path:
    """Accept the supplied files in the root or the conventional raw directory."""
    name = SOURCE_FILES[key]
    for path in (DATA / "raw" / name, ROOT / name):
        if path.is_file():
            return path
    raise FileNotFoundError(f"Falta {name}. Colóquelo en data/raw/ o en la raíz.")

