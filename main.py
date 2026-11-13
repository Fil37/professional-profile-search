"""Command-line entry point for the two-agent search workflow."""

import argparse
import json

from langchain_core.globals import set_debug

from workflow import run_search


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search public professional profile information."
    )
    parser.add_argument("request", help="Free-form description of the target person")
    args = parser.parse_args()

    set_debug(True)
    result = run_search(args.request)
    print(f"Critères extraits : {result['criteria'].model_dump_json(indent=2)}")
    if result["outcome"] is None:
        print("\nLe nom de la personne n'a pas pu être extrait. Précisez-le puis réessayez.")
        return
    print("\nRésultat de recherche :")
    print(
        json.dumps(
            result["outcome"].model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()