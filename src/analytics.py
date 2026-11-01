"""Pure calculations shared by visualizations, exports and tests."""

from dataclasses import dataclass

import pandas as pd

from src.settings import AGE_GROUPS


@dataclass(frozen=True)
class Filters:
    department: str = "all"
    months: tuple[int, ...] = ()
    sex: str = "all"
    age_group: str = "all"


def filter_data(frame: pd.DataFrame, filters: Filters) -> pd.DataFrame:
    mask = pd.Series(True, index=frame.index)
    if filters.department != "all":
        mask &= frame.department.eq(filters.department)
    if filters.months:
        mask &= frame.month.isin(filters.months)
    if filters.sex != "all":
        mask &= frame.sex.eq(int(filters.sex))
    if filters.age_group != "all":
        mask &= frame.age_group.eq(int(filters.age_group))
    return frame.loc[mask]


def count_by(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return frame.groupby(columns, observed=True, dropna=False).deaths.sum().reset_index()


def monthly_counts(frame: pd.DataFrame, months: tuple[int, ...] = ()) -> pd.Series:
    # Unselected months are not zeroes: only display the requested period.
    domain = sorted(set(months)) if months else list(range(1, 13))
    return frame.groupby("month", observed=True).deaths.sum().reindex(domain, fill_value=0)


def municipality_ranking(frame: pd.DataFrame, *, lowest: bool = False) -> pd.DataFrame:
    # Divipola also includes non-municipal areas and islands: rankings are municipal.
    eligible = frame.loc[frame.territory_type.eq("Municipio")]
    if not lowest:
        eligible = eligible.loc[eligible.is_x95]
    result = count_by(eligible, ["municipality", "municipality_name", "department_name"])
    result = result.loc[result.deaths.gt(0)]
    return result.sort_values(["deaths", "municipality"], ascending=[lowest, True]).head(10 if lowest else 5)


def top_causes(frame: pd.DataFrame, descriptions: dict[str, str]) -> pd.DataFrame:
    result = count_by(frame, ["cause"]).sort_values(["deaths", "cause"], ascending=[False, True]).head(10)
    result["description"] = result.cause.astype("string").map(descriptions).fillna("Descripción no disponible en el catálogo")
    total = int(frame.deaths.sum())
    result["share"] = result.deaths / total if total else 0.0
    return result


def age_counts(frame: pd.DataFrame) -> pd.Series:
    return frame.groupby("age_group", observed=True).deaths.sum().reindex(range(len(AGE_GROUPS)), fill_value=0)


def metrics(frame: pd.DataFrame) -> dict:
    total = int(frame.deaths.sum())
    older = int(frame.loc[frame.age_code.between(20, 28), "deaths"].sum())
    return {
        "total": total, "x95": int(frame.loc[frame.is_x95, "deaths"].sum()),
        "departments": int(frame.department.nunique()),
        "older_share": older / total * 100 if total else None,
        "unknown_age": int(frame.loc[frame.age_code.eq(29), "deaths"].sum()),
    }


def format_count(value: int | float) -> str:
    return f"{int(value):,}".replace(",", ".")


def format_percent(value: float) -> str:
    return f"{value:.1f}".replace(".", ",") + " %"
