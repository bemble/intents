"""Parse sentences using language intent files."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

import yaml
from hassil.intents import Intents, SlotList, TextSlotList
from hassil.recognize import recognize
from hassil.util import merge_dict

from .const import LANGUAGES, SENTENCE_DIR, TESTS_DIR
from .util import get_base_arg_parser


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = get_base_arg_parser()
    parser.add_argument(
        "--language",
        required=True,
        type=str,
        choices=LANGUAGES,
        help="The language to validate.",
    )
    parser.add_argument(
        "--sentence",
        required=True,
        action="append",
        type=str,
        help="Sentence(s) to parse",
    )
    return parser.parse_args()


def run() -> int:
    args = get_arguments()

    language_dir = SENTENCE_DIR / args.language
    tests_dir = TESTS_DIR / args.language

    # Load test areas and entities for language
    test_names = yaml.safe_load((tests_dir / "_common.yaml").read_text())

    slot_lists: Dict[str, SlotList] = {
        "area": TextSlotList.from_tuples(
            (area["name"], area["id"]) for area in test_names["areas"]
        ),
        "name": TextSlotList.from_tuples(
            (entity["name"], entity["id"]) for entity in test_names["entities"]
        ),
    }

    # Load intents
    intents_dict: Dict[str, Any] = {}
    for intent_path in language_dir.glob("*.yaml"):
        with open(intent_path, "r", encoding="utf-8") as intent_file:
            merge_dict(intents_dict, yaml.safe_load(intent_file))

    assert intents_dict, "No intent YAML files loaded"
    intents = Intents.from_dict(intents_dict)

    # Parse sentences
    for sentence in args.sentence:
        result = recognize(sentence, intents, slot_lists=slot_lists)
        output_dict = {"text": sentence, "match": result is not None}
        if result is not None:
            output_dict["intent"] = result.intent.name
            output_dict["slots"] = {
                entity.name: entity.value for entity in result.entities_list
            }

        json.dump(output_dict, sys.stdout, ensure_ascii=False, indent=2)
        print("")

    return 0
