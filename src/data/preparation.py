"""Validate the supplied workbooks and create a lossless frequency cube."""

import hashlib
import json
from pathlib import Path

import pandas as pd

from src.settings import PROCESSED, SCHEMA_VERSION, SOURCE_FILES, YEAR, source_path

DIMENSIONS = ["department", "municipality", "month", "sex", "age_code", "cause"]
COLUMN_NAMES = {
    "COD_DEPARTAMENTO": "department", "COD_DANE": "municipality",
    "MES": "month", "SEXO": "sex", "GRUPO_EDAD1": "age_code",
    "COD_MUERTE": "cause",
}


def normalize_code(values: pd.Series, width: int | None = None) -> pd.Series:
    """Preserve identifiers, remove Excel numeric suffixes and normalize CIE-10."""
    result = values.astype("string").str.strip().str.upper().str.replace(r"\.0$", "", regex=True)
    return result.str.zfill(width) if width else result.str.replace(".", "", regex=False)


def fingerprint(path: Path) -> dict:
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    return {
        "name": path.name, "bytes": path.stat().st_size,
        "mtime_ns": path.stat().st_mtime_ns,
        "sha256": digest,
    }


def read_territories(path: Path) -> pd.DataFrame:
    territories = pd.read_excel(path, sheet_name="Hoja1", dtype="string")
    territories = territories.rename(columns={
        "COD_DANE": "municipality", "COD_DEPARTAMENTO": "department",
        "DEPARTAMENTO": "department_name", "MUNICIPIO": "municipality_name",
    })[["municipality", "department", "department_name", "municipality_name"]]
    territories["municipality"] = normalize_code(territories["municipality"], 5)
    territories["department"] = normalize_code(territories["department"], 2)
    for column in ("department_name", "municipality_name"):
        territories[column] = territories[column].str.strip().str.title()
    territories.loc[territories.department == "11", "department_name"] = "Bogotá D. C."
    territories.loc[territories.municipality == "11001", "municipality_name"] = "Bogotá D. C."
    territories.loc[territories.department == "88", "department_name"] = "San Andrés y Providencia"
    if territories.municipality.duplicated().any():
        raise ValueError("Divipola contiene claves municipales duplicadas.")
    types = pd.read_excel(path, sheet_name="Hoja3", header=1, dtype="string")
    types = types.iloc[:, [2, 4]].copy()
    types.columns = ["municipality", "territory_type"]
    types["municipality"] = normalize_code(types.municipality, 5)
    return territories.merge(types, on="municipality", how="left", validate="one_to_one")


def read_causes(path: Path) -> dict[str, str]:
    catalog = pd.read_excel(path, sheet_name="Final", header=8, dtype="string")
    descriptions: dict[str, str] = {}
    # Specific codes take precedence; categories are a fallback for 3-character codes.
    for code_column, label_column in ((2, 3), (4, 5)):
        codes = normalize_code(catalog.iloc[:, code_column])
        for code, label in zip(codes, catalog.iloc[:, label_column]):
            if pd.notna(code) and pd.notna(label):
                descriptions[str(code)] = str(label).strip().capitalize()
    return descriptions


def prepare_data() -> dict:
    """Retain every death once; aggregate identical dimensions instead of deduplicating."""
    paths = {key: source_path(key) for key in SOURCE_FILES}
    raw = pd.read_excel(paths["mortality"], sheet_name="No_Fetales_2019", dtype={
        "COD_DANE": "string", "COD_DEPARTAMENTO": "string",
        "COD_MUNICIPIO": "string", "COD_MUERTE": "string",
    })
    required = set(COLUMN_NAMES) | {"AÑO", "COD_MUNICIPIO"}
    if missing := required.difference(raw.columns):
        raise ValueError(f"Faltan columnas: {sorted(missing)}")
    if not raw["AÑO"].eq(YEAR).all():
        raise ValueError("El archivo contiene años diferentes de 2019 o sin información.")
    data = raw[list(COLUMN_NAMES)].rename(columns=COLUMN_NAMES).copy()
    if data.isna().any().any():
        raise ValueError("Hay valores vacíos en dimensiones requeridas; revise el archivo fuente.")
    data["municipality"] = normalize_code(data.municipality, 5)
    data["department"] = normalize_code(data.department, 2)
    data["cause"] = normalize_code(data.cause)
    expected_codes = data.department + normalize_code(raw.COD_MUNICIPIO, 3)
    if not data.municipality.eq(expected_codes).all():
        raise ValueError("COD_DANE no coincide con departamento + municipio.")
    for name, allowed in (("month", range(1, 13)), ("sex", (1, 2, 3)), ("age_code", range(30))):
        if not data[name].isin(allowed).all():
            raise ValueError(f"Valores fuera del diccionario en {name}.")
        data[name] = data[name].astype("int8")
    territories = read_territories(paths["territories"])
    missing_geo = sorted(set(data.municipality) - set(territories.municipality))
    if missing_geo:
        raise ValueError(f"Territorios sin nombre en Divipola: {missing_geo}")
    causes = read_causes(paths["causes"])
    unmatched = data.loc[~data.cause.isin(causes), "cause"].value_counts().to_dict()
    cube = data.groupby(DIMENSIONS, observed=True, dropna=False).size().reset_index(name="deaths")
    if int(cube.deaths.sum()) != len(raw):
        raise ValueError("La agregación no conserva el total de defunciones.")
    report = {
        "schema_version": SCHEMA_VERSION, "year": YEAR,
        "records": len(raw), "cube_rows": len(cube),
        "departments": int(data.department.nunique()),
        "territories_with_records": int(data.municipality.nunique()),
        "x95_deaths": int(data.cause.str.startswith("X95").sum()),
        "unknown_sex": int(data.sex.eq(3).sum()),
        "unknown_age": int(data.age_code.eq(29).sum()),
        "unmatched_causes": unmatched,
        "missing_values_original": {k: int(v) for k, v in raw.isna().sum().items() if v},
        "sources": {key: fingerprint(path) for key, path in paths.items()},
    }
    PROCESSED.mkdir(parents=True, exist_ok=True)
    cube.to_csv(PROCESSED / "mortality.csv.gz", index=False, compression="gzip")
    territories.to_csv(PROCESSED / "territories.csv", index=False)
    (PROCESSED / "causes.json").write_text(json.dumps(causes, ensure_ascii=False), encoding="utf-8")
    (PROCESSED / "quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    return report

