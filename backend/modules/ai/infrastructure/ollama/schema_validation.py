from pydantic import BaseModel, ConfigDict, create_model

# Ollama's local models have no native structured-output guarantee (unlike Claude's
# output_config.format), so responses are validated on our side. This converts the
# subset of JSON Schema our own prompt builders emit (object/array/string/integer/
# number, properties, required, additionalProperties) into a Pydantic model — not a
# general-purpose JSON Schema implementation.


def build_model_from_schema(schema: dict, name: str = "StructuredResponse") -> type[BaseModel]:
    if schema.get("type") != "object":
        raise ValueError("Root schema must be of type 'object'.")
    return _build_object_model(schema, name)


def _build_object_model(schema: dict, name: str) -> type[BaseModel]:
    required = set(schema.get("required", []))
    fields = {}
    for prop_name, prop_schema in schema.get("properties", {}).items():
        python_type = _resolve_type(prop_schema, f"{name}_{prop_name}")
        default = ... if prop_name in required else None
        fields[prop_name] = (python_type, default)

    config = ConfigDict(extra="forbid") if schema.get("additionalProperties") is False else None
    return create_model(name, __config__=config, **fields)


def build_example_from_schema(schema: dict):
    """Render a filled-in example instance from a JSON schema (same subset as above).

    Small local models follow a concrete example far more reliably than raw JSON
    Schema syntax (`{"type": "object", "properties": {...}}`) — empirically, asking
    llama3.2:1b to match a schema directly made it echo the schema's own keys
    (`type`/`properties`) instead of producing an instance of it.
    """
    schema_type = schema.get("type")
    if schema_type == "object":
        return {
            prop_name: build_example_from_schema(prop_schema)
            for prop_name, prop_schema in schema.get("properties", {}).items()
        }
    if schema_type == "array":
        return [build_example_from_schema(schema["items"])]
    if schema_type == "string":
        return "string"
    if schema_type == "integer":
        return 1
    if schema_type == "number":
        return 1.0
    if schema_type == "boolean":
        return True
    raise ValueError(f"Unsupported JSON schema type for example generation: {schema_type!r}")


def _resolve_type(schema: dict, name: str):
    schema_type = schema.get("type")
    if schema_type == "object":
        return _build_object_model(schema, name)
    if schema_type == "array":
        return list[_resolve_type(schema["items"], f"{name}Item")]
    if schema_type == "string":
        return str
    if schema_type == "integer":
        return int
    if schema_type == "number":
        return float
    if schema_type == "boolean":
        return bool
    raise ValueError(f"Unsupported JSON schema type for Ollama validation: {schema_type!r}")
