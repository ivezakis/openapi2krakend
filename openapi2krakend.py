import json
import argparse
from pathlib import Path


class Endpoint:
    def __init__(
        self,
        endpoint,
        method,
        output_encoding,
        timeout,
        extra_config,
        input_query_strings,
        backend,
        input_headers,
    ):
        self.endpoint = endpoint
        self.method = method
        self.output_encoding = output_encoding
        self.timeout = timeout
        self.extra_config = extra_config
        self.input_query_strings = input_query_strings
        self.backend = (backend,)
        self.input_headers = input_headers


class Backend:
    def __init__(
        self, url_pattern, encoding, method, is_collection, host, disable_host_sanitize
    ):
        self.url_pattern = url_pattern
        self.encoding = encoding
        self.method = method
        if is_collection:
            self.is_collection = is_collection
        self.host = host
        self.disable_host_sanitize = disable_host_sanitize


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert OpenAPI to Krakend config")
    parser.add_argument("input", help="Input file", type=str, default="swagger.json")
    parser.add_argument("output", help="Output file", type=str, default="krakend.json")
    args = parser.parse_args()

    with open(args.input, "r") as f:
        openapi = json.load(f)

    filename = Path(args.input).stem
    endpoints = []

    if "host" in openapi:
        host = [openapi["host"]]
    elif "servers" in openapi:
        host = [openapi["servers"][0]["url"]]
    elif "basePath" in openapi:
        host = [openapi["basePath"]]
    else:
        host = []

    for path in openapi["paths"]:
        for method in openapi["paths"][path]:
            output_encoding = "no-op"
            encoding = "no-op"
            is_collection = False
            if ("responses" in openapi["paths"][path][method]):
                if ("200" in openapi["paths"][path][method]["responses"]):
                    if ("content" in openapi["paths"][path][method]["responses"]["200"]):
                        if ("application/json" in openapi["paths"][path][method]["responses"]["200"]["content"]):
                            encoding = "json"
                            output_encoding = "json"
                        if ("application/xml" in openapi["paths"][path][method]["responses"]["200"]["content"]):
                            encoding = "xml"
                            output_encoding = "json"
                        if ("*/*" in openapi["paths"][path][method]["responses"]["200"]["content"]):
                            if ("schema" in openapi["paths"][path][method]["responses"]["200"]["content"]["*/*"]):
                                if ("type" in openapi["paths"][path][method]["responses"]["200"]["content"]["*/*"]["schema"]):
                                    if (openapi["paths"][path][method]["responses"]["200"]["content"]["*/*"]["schema"]["type"] == "array"):
                                        is_collection = True
                                        encoding = "json"
                                        output_encoding = "json-collection"
                                    elif (openapi["paths"][path][method]["responses"]["200"]["content"]["*/*"]["schema"]["type"] == "string"):
                                        encoding = "string"
                                        output_encoding = "json"

            endpoints.append(
                Endpoint(
                    endpoint=path,
                    method=method.upper(),
                    output_encoding=output_encoding,
                    timeout="30s",
                    extra_config={},
                    input_query_strings=["*"],
                    backend=Backend(
                        url_pattern=path,
                        encoding=encoding,
                        method=method.upper(),
                        is_collection=is_collection,
                        host=host,
                        disable_host_sanitize=False,
                    ),
                    input_headers=["*"],
                )
            )

    res = json.dumps(endpoints, default=lambda x: x.__dict__, indent=4)

    with open(args.output, "w") as f:
        f.write(res)
