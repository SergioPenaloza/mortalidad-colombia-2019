"""Download public DANE 2019 geometry and Plotly's offline geographic base."""

import json
from urllib.parse import urlencode
from urllib.request import urlopen

from src.settings import ASSETS, DATA

SERVICE = "https://portalgis.dane.gov.co/mparcgis/rest/services/MGN2019/Serv_CapasMGN_2019/FeatureServer/319"
TOPOJSON = "https://cdn.plot.ly/world_110m.json"


def fetch_geography() -> None:
    query = urlencode({
        "where": "1=1", "outFields": "DPTO_CCDGO,DPTO_CNMBRE,DPTO_NANO",
        "outSR": 4326, "returnGeometry": "true", "f": "geojson",
        "maxAllowableOffset": 0.008, "geometryPrecision": 4,
    })
    with urlopen(f"{SERVICE}/query?{query}", timeout=60) as response:
        geo = json.load(response)
    if "features" not in geo or len(geo["features"]) != 33:
        raise ValueError("El servicio no devolvió las 33 unidades departamentales esperadas.")
    codes = set()
    for feature in geo["features"]:
        if not feature.get("geometry"):
            raise ValueError("El servicio devolvió una geometría vacía; no se reemplazó la cartografía local.")
        code = str(feature["properties"]["DPTO_CCDGO"]).zfill(2)
        codes.add(code)
        feature["id"] = code
        feature["properties"] = {
            "code": code, "name": feature["properties"]["DPTO_CNMBRE"],
            "year": feature["properties"]["DPTO_NANO"],
        }
    if len(codes) != 33 or "11" not in codes or "88" not in codes:
        raise ValueError("La cartografía contiene códigos incompletos o duplicados.")
    directory = DATA / "geo"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "departments_2019.geojson").write_text(
        json.dumps(geo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8",
    )
    offline = ASSETS / "geo"
    offline.mkdir(parents=True, exist_ok=True)
    with urlopen(TOPOJSON, timeout=60) as response:
        base = response.read()
    json.loads(base)
    (offline / "world_110m.json").write_bytes(base)
    (directory / "source.json").write_text(json.dumps({
        "publisher": "Departamento Administrativo Nacional de Estadística (DANE)",
        "dataset": "Marco Geoestadístico Nacional 2019, departamento", "service": SERVICE,
        "query": query, "features": 33, "simplification_degrees": 0.008,
        "feature_version_years": sorted({f["properties"]["year"] for f in geo["features"]}),
        "purpose": "Visualización estadística; no sustituye cartografía legal de límites.",
        "plotly_topojson": TOPOJSON,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Cartografía 2019 guardada: {len(codes)} departamentos, {len(base):,} bytes de base local.")


if __name__ == "__main__":
    fetch_geography()

