import os

from .db import SessionLocal
from .services.importer import import_csv


def main():
    path = "/seed/episodes.csv"

    if not os.path.exists(path):
        print(f"Episode CSV not found: {path}")
        return

    db = SessionLocal()

    try:
        result = import_csv(db, path)

        print(
            f"Episode import complete: "
            f"{result['imported']} imported, "
            f"{result['skipped']} skipped"
        )

        if result["reasons"]:
            print(f"Skip reasons: {result['reasons']}")

    finally:
        db.close()


if __name__ == "__main__":
    main()