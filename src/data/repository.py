"""Load local prepared data once, without network calls or mutable session state."""

from dataclasses import dataclass
from functools import lru_cache
import json

import pandas as pd

from src.settings import AGE_CODE_TO_GROUP, DATA, PROCESSED, SCHEMA_VERSION


@dataclass(frozen=True)
class Dataset:
    frame: pd.DataFrame
    territories: pd.DataFrame
    causes: dict[str, str]
    geography: dict
    quality: dict

    @property
    def departments(self) -> pd.DataFrame:
        return self.territories[["department", "department_name"]].drop_duplicates().sort_values("department_name")


@lru_cache(maxsize=1)
def load_dataset() -> Dataset:
    manifest = PROCESSED / "quality_report.json"
    if not manifest.exists():
        raise FileNotFoundError("Prepare los datos con: python -m scripts.prepare_data")
    quality = json.loads(manifest.read_text(encoding="utf-8"))
    if quality["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Datos procesados desactualizados. Ejecute python -m scripts.prepare_data.")
    frame = pd.read_csv(PROCESSED / "mortality.csv.gz", dtype={
        "department": "string", "municipality": "string", "cause": "string",
        "month": "int8", "sex": "int8", "age_code": "int8", "deaths": "int32",
    })
    frame["age_group"] = frame.age_code.map(AGE_CODE_TO_GROUP).astype("int8")
    frame["is_x95"] = frame.cause.str.startswith("X95")
    territories = pd.read_csv(PROCESSED / "territories.csv", dtype="string")
    frame = frame.merge(territories, on=["municipality", "department"], how="left", validate="many_to_one")
    if frame.municipality_name.isna().any() or int(frame.deaths.sum()) != quality["records"]:
        raise ValueError("Los archivos procesados no son consistentes; vuelva a preparar los datos.")
    causes = json.loads((PROCESSED / "causes.json").read_text(encoding="utf-8"))
    geography = json.loads((DATA / "geo" / "departments_2019.geojson").read_text(encoding="utf-8"))
    if any(not feature.get("geometry") for feature in geography["features"]):
        raise ValueError("La cartografía contiene geometrías vacías. Ejecute python -m scripts.fetch_geography.")
    if set(frame.department) - {feature["id"] for feature in geography["features"]}:
        raise ValueError("Hay departamentos sin geometría en el mapa.")
    for column in ("department", "municipality", "cause", "department_name", "municipality_name", "territory_type"):
        frame[column] = frame[column].astype("category")
    return Dataset(frame, territories, causes, geography, quality)

