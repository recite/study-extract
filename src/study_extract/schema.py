"""Closed per-profile response schemas for structured-output backends."""

from copy import deepcopy
from typing import Any

from study_extract.catalog import CATALOG
from study_extract.models import Extraction


def response_schema(kinds: list[str]) -> dict[str, Any]:
    schema = deepcopy(Extraction.model_json_schema())
    record = schema["$defs"].pop("Record")
    alternatives = []
    for kind in kinds:
        variant = deepcopy(record)
        variant["properties"]["kind"] = {"type": "string", "enum": [kind]}
        fields = {name: {"$ref": "#/$defs/Cell"} for name in CATALOG[kind]}
        variant["properties"]["fields"] = {
            "type": "object",
            "properties": fields,
            "required": list(fields),
            "additionalProperties": False,
        }
        alternatives.append(variant)
    schema["properties"]["records"]["items"] = {"anyOf": alternatives}

    def close(node: Any) -> None:
        if isinstance(node, dict):
            node.pop("default", None)
            if node.get("type") == "object":
                node["additionalProperties"] = False
                node["required"] = list(node.get("properties", {}))
            for value in node.values():
                close(value)
        elif isinstance(node, list):
            for item in node:
                close(item)

    close(schema)
    return schema
