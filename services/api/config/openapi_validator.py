import re
import warnings
from pathlib import Path

import jsonschema
import yaml

_OPENAPI_SPEC_CACHE = None
_PREPROCESSED_SPEC_CACHE = None


def get_openapi_spec_path() -> Path:
    curr = Path(__file__).resolve().parent
    for _ in range(5):
        candidate = curr / "packages" / "contracts" / "openapi" / "schema.yaml"
        if candidate.exists():
            return candidate
        curr = curr.parent
    raise FileNotFoundError("Could not locate packages/contracts/openapi/schema.yaml")


def load_openapi_spec():
    global _OPENAPI_SPEC_CACHE, _PREPROCESSED_SPEC_CACHE
    if _OPENAPI_SPEC_CACHE is not None:
        return _OPENAPI_SPEC_CACHE, _PREPROCESSED_SPEC_CACHE

    schema_path = get_openapi_spec_path()
    with open(schema_path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    _OPENAPI_SPEC_CACHE = spec
    _PREPROCESSED_SPEC_CACHE = _preprocess_schema_for_jsonschema(spec)
    return _OPENAPI_SPEC_CACHE, _PREPROCESSED_SPEC_CACHE


def _preprocess_schema_for_jsonschema(obj):
    if not isinstance(obj, dict):
        return obj

    res = {}
    for k, v in obj.items():
        if isinstance(v, dict):
            res[k] = _preprocess_schema_for_jsonschema(v)
        elif isinstance(v, list):
            res[k] = [
                _preprocess_schema_for_jsonschema(item) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            res[k] = v

    if res.get("nullable") is True:
        del res["nullable"]
        return {"anyOf": [{"type": "null"}, res]}

    return res


def _find_matching_openapi_path(spec_paths: dict, path_info: str):
    path_info_clean = path_info.split("?")[0]

    if path_info_clean in spec_paths:
        return path_info_clean

    for openapi_path in spec_paths.keys():
        pattern = "^" + re.sub(r"\{[^}]+\}", r"[^/]+", openapi_path) + "$"
        if re.match(pattern, path_info_clean):
            return openapi_path

    if not path_info_clean.endswith("/"):
        alt_path = path_info_clean + "/"
        if alt_path in spec_paths:
            return alt_path
        for openapi_path in spec_paths.keys():
            pattern = "^" + re.sub(r"\{[^}]+\}", r"[^/]+", openapi_path) + "$"
            if re.match(pattern, alt_path):
                return openapi_path
    elif path_info_clean.endswith("/") and len(path_info_clean) > 1:
        alt_path = path_info_clean.rstrip("/")
        if alt_path in spec_paths:
            return alt_path
        for openapi_path in spec_paths.keys():
            pattern = "^" + re.sub(r"\{[^}]+\}", r"[^/]+", openapi_path) + "$"
            if re.match(pattern, alt_path):
                return openapi_path

    return None


def assert_response_matches_openapi(response, expected_status: int = None):
    if expected_status is not None:
        assert response.status_code == expected_status, (
            f"Expected status {expected_status}, but got {response.status_code}. "
            f"Body: {getattr(response, 'content', b'')[:500]!r}"
        )

    raw_spec, preprocessed_spec = load_openapi_spec()
    spec_paths = raw_spec.get("paths", {})

    req = getattr(response, "request", {})
    path_info = req.get("PATH_INFO")
    if not path_info:
        path_info = getattr(response, "url", None) or getattr(response, "path", None)

    assert path_info, "Could not determine request path from response object."

    method = req.get("REQUEST_METHOD", "GET").lower()

    matched_path = _find_matching_openapi_path(spec_paths, path_info)
    assert matched_path, (
        f"Path '{path_info}' was not found in OpenAPI schema. "
        f"Available paths in schema.yaml: {list(spec_paths.keys())}"
    )

    path_item = spec_paths[matched_path]
    assert method in path_item, (
        f"HTTP method '{method.upper()}' is not defined for path '{matched_path}' "
        f"in OpenAPI schema. Defined methods: {list(path_item.keys())}"
    )

    operation = path_item[method]
    responses_def = operation.get("responses", {})
    status_str = str(response.status_code)

    if status_str not in responses_def:
        if "default" in responses_def:
            status_def = responses_def["default"]
            status_key = "default"
        else:
            raise AssertionError(
                f"Status code {response.status_code} is not documented for {method.upper()} "
                f"{matched_path} in OpenAPI schema. Documented status codes: "
                f"{list(responses_def.keys())}. Response body: "
                f"{getattr(response, 'content', b'')[:500]!r}"
            )
    else:
        status_def = responses_def[status_str]
        status_key = status_str

    content_def = status_def.get("content", {})
    if content_def:
        content_type_header = response.headers.get("Content-Type", "")
        matching_ct = None
        for expected_ct in content_def.keys():
            if content_type_header.startswith(expected_ct):
                matching_ct = expected_ct
                break
        assert matching_ct, (
            f"Response Content-Type '{content_type_header}' does not match expected "
            f"Content-Type(s) {list(content_def.keys())} for {method.upper()} "
            f"{matched_path} ({response.status_code})."
        )

        if "application/json" in content_def and "schema" in content_def["application/json"]:
            try:
                data = response.json()
            except Exception as exc:
                raise AssertionError(
                    f"Failed to parse JSON body for {method.upper()} {matched_path} "
                    f"({response.status_code}): {exc}. Raw content: {response.content!r}"
                ) from exc

            resp_spec = preprocessed_spec["paths"][matched_path][method]["responses"]
            prep_schema = resp_spec[status_key]["content"]["application/json"]["schema"]

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    category=DeprecationWarning,
                    message=".*RefResolver.*",
                )
                resolver = jsonschema.RefResolver.from_schema(preprocessed_spec)
                validator = jsonschema.Draft7Validator(prep_schema, resolver=resolver)
                errors = list(validator.iter_errors(data))

            if errors:
                error_messages = [
                    f"  - {e.message} (at {'/'.join(str(p) for p in e.path)})" for e in errors[:10]
                ]
                raise AssertionError(
                    f"Response body for {method.upper()} {matched_path} ({response.status_code}) "
                    f"failed OpenAPI schema validation with {len(errors)} error(s):\n"
                    + "\n".join(error_messages)
                    + f"\nResponse data snippet: {str(data)[:500]}"
                )
