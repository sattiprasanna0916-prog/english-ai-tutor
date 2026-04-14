import pandas as pd
from pathlib import Path
from datetime import datetime
import threading
lock = threading.Lock()
DATA_PATH = Path(__file__).resolve().parents[2] / "datasets" / "users.csv"
# Keep it minimal for your current UI (email + branch + current_level)
COLUMNS = [
    "user_id",
    "email",
    "branch",
    "current_level",
    "created_at",
]


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _clean_str(x, default="") -> str:
    s = "" if x is None else str(x)
    s = s.strip()
    return s if s else default


def _ensure_file():
    """
    Ensures users.csv exists and has all required columns (in correct order).
    If old file has extra columns, we keep them BUT also ensure our columns exist.
    """
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not DATA_PATH.exists():
        pd.DataFrame(columns=COLUMNS).to_csv(DATA_PATH, index=False)
        return

    df = pd.read_csv(DATA_PATH)

    changed = False
    for col in COLUMNS:
        if col not in df.columns:
            # defaults
            if col == "current_level":
                df[col] = "Beginner"
            else:
                df[col] = ""
            changed = True

    # Reorder: keep required first, then any extra columns after
    extra_cols = [c for c in df.columns if c not in COLUMNS]
    df = df[COLUMNS + extra_cols]

    if changed:
        df.to_csv(DATA_PATH, index=False)


def _next_user_id(df: pd.DataFrame) -> int:
    if df.empty or "user_id" not in df.columns:
        return 1
    ids = pd.to_numeric(df["user_id"], errors="coerce").dropna()
    return 1 if ids.empty else int(ids.max()) + 1


def _row_to_dict(row: pd.Series) -> dict:
    d = row.to_dict()
    # Replace NaN with ""
    for k, v in list(d.items()):
        if pd.isna(v):
            d[k] = ""
    # Normalize types
    if "user_id" in d and d["user_id"] != "":
        try:
            d["user_id"] = int(float(d["user_id"]))
        except Exception:
            pass
    if "email" in d:
        d["email"] = _normalize_email(d.get("email", ""))
    if "branch" in d:
        d["branch"] = _clean_str(d.get("branch", ""), "Unknown")
    if "current_level" in d:
        d["current_level"] = _clean_str(d.get("current_level", ""), "Beginner")
    return d


def get_user(user_id: int):
    _ensure_file()
    df = pd.read_csv(DATA_PATH)
    if df.empty:
        return None

    df["user_id"] = pd.to_numeric(df["user_id"], errors="coerce")
    row = df[df["user_id"] == int(user_id)]
    if row.empty:
        return None

    return _row_to_dict(row.iloc[0])


def get_user_by_email(email: str):
    _ensure_file()
    df = pd.read_csv(DATA_PATH)
    if df.empty:
        return None

    e = _normalize_email(email)
    if not e:
        return None

    df["email"] = df["email"].astype(str).str.lower().str.strip()
    row = df[df["email"] == e]
    if row.empty:
        return None

    return _row_to_dict(row.iloc[0])
def _normalize_level(level: str) -> str:
    s = str(level).strip().lower()
    if s in ["beginner", "1"]:
        return "Beginner"
    if s in ["intermediate", "2"]:
        return "Intermediate"
    if s in ["advanced", "3"]:
        return "Advanced"
    return "Beginner"


def register_user(email: str, branch: str, current_level: str = "Beginner"):
    _ensure_file()
    with lock:
        df = pd.read_csv(DATA_PATH)

        email_norm = _normalize_email(email)
        if not email_norm:
            raise ValueError("email is required")

        branch_clean = _clean_str(branch, "Unknown")
        level_clean = _normalize_level(current_level)

    # If email exists -> return existing
        if not df.empty:
            df["email"] = df["email"].astype(str).str.lower().str.strip()
            existing = df[df["email"] == email_norm]

            if not existing.empty:
                idx = existing.index[0]
                changed = False

                if branch_clean and _clean_str(df.loc[idx, "branch"]) != branch_clean:
                    df.loc[idx, "branch"] = branch_clean
                    changed = True

                if level_clean and _clean_str(df.loc[idx, "current_level"]) != level_clean:
                    df.loc[idx, "current_level"] = level_clean
                    changed = True

                if changed:
                    df.to_csv(DATA_PATH, index=False)

            return _row_to_dict(df.loc[idx])

    # Create new user
    new_id = _next_user_id(df)
    row = {
        "user_id": new_id,
        "email": email_norm,
        "branch": branch_clean,
        "current_level": level_clean,
        "created_at": datetime.now().isoformat(),
    }

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(DATA_PATH, index=False)
    return row