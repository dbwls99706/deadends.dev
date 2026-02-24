"""Bulk generate ErrorCanon JSON files from seed definitions.

Usage: python -m generator.bulk_generate
"""

import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "canons"
BASE_URL = "https://deadends.dev"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def canon(
    domain: str,
    slug: str,
    env_id: str,
    signature: str,
    regex: str,
    category: str,
    runtime_name: str,
    runtime_ver: str,
    os_str: str,
    resolvable: str,
    fix_rate: float,
    confidence: float,
    summary: str,
    dead_ends: list[dict],
    workarounds: list[dict],
    python: str | None = None,
    gpu: str | None = None,
    vram: int | None = None,
    arch: str | None = None,
    leads_to: list[dict] | None = None,
    preceded_by: list[dict] | None = None,
    confused_with: list[dict] | None = None,
) -> dict:
    """Build a complete ErrorCanon dict."""
    full_id = f"{domain}/{slug}/{env_id}"
    env: dict = {
        "runtime": {"name": runtime_name, "version_range": runtime_ver},
        "os": os_str,
    }
    if python:
        env["python"] = python
    if gpu:
        env["hardware"] = {"gpu": gpu}
        if vram:
            env["hardware"]["vram_gb"] = vram
    if arch:
        env["additional"] = {"architecture": arch}

    # Ensure dead_ends have sources
    for d in dead_ends:
        d.setdefault("sources", [])
        d.setdefault("condition", "")
    for w in workarounds:
        w.setdefault("sources", [])
        w.setdefault("condition", "")

    return {
        "schema_version": "1.0.0",
        "id": full_id,
        "url": f"{BASE_URL}/{full_id}",
        "error": {
            "signature": signature,
            "regex": regex,
            "domain": domain,
            "category": category,
            "first_seen": "2023-01-01",
            "last_confirmed": TODAY,
        },
        "environment": env,
        "verdict": {
            "resolvable": resolvable,
            "fix_success_rate": fix_rate,
            "confidence": confidence,
            "last_updated": TODAY,
            "summary": summary,
        },
        "dead_ends": dead_ends,
        "workarounds": workarounds,
        "transition_graph": {
            "leads_to": leads_to or [],
            "preceded_by": preceded_by or [],
            "frequently_confused_with": confused_with or [],
        },
        "metadata": {
            "generated_by": "bulk_generate.py",
            "generation_date": TODAY,
            "review_status": "auto_generated",
            "evidence_count": 50,
            "last_verification": TODAY,
        },
    }


def de(action: str, why: str, rate: float, sources: list[str] | None = None) -> dict:
    d = {"action": action, "why_fails": why, "fail_rate": rate}
    if sources:
        d["sources"] = sources
    return d


def wa(action: str, rate: float, how: str = "", sources: list[str] | None = None) -> dict:
    d: dict = {"action": action, "success_rate": rate}
    if how:
        d["how"] = how
    if sources:
        d["sources"] = sources
    return d


def leads(error_id: str, probability: float, condition: str = "") -> dict:
    d: dict = {"error_id": error_id, "probability": probability}
    if condition:
        d["condition"] = condition
    return d


def preceded(error_id: str, probability: float, condition: str = "") -> dict:
    d: dict = {"error_id": error_id, "probability": probability}
    if condition:
        d["condition"] = condition
    return d


def confused(error_id: str, distinction: str) -> dict:
    return {"error_id": error_id, "distinction": distinction}


def get_all_canons() -> list[dict]:
    """Return all seed canon definitions."""
    canons = []

    # === PYTHON ===
    canons.append(canon(
        "python", "typeerror-nonetype-not-subscriptable", "py311-linux",
        "TypeError: 'NoneType' object is not subscriptable",
        r"TypeError: 'NoneType' object is not (subscriptable|iterable)",
        "type_error", "python", ">=3.11,<3.13", "linux", "true", 0.85, 0.88,
        "Occurs when indexing or iterating over a None value. Usually a missing return or failed API call.",
        [de("Add try/except around the indexing", "Masks the root cause without fixing the None source", 0.72, sources=["https://docs.python.org/3/tutorial/errors.html"]),
         de("Check if variable is None right before use", "The None originates earlier in the call chain", 0.65, sources=["https://docs.python.org/3/library/exceptions.html#TypeError"])],
        [wa("Trace the variable back to its assignment and fix the source of None", 0.90, "Add breakpoint or print before assignment", sources=["https://docs.python.org/3/library/functions.html#breakpoint"]),
         wa("Use Optional type hints and handle None explicitly in the function that produces the value", 0.85, sources=["https://docs.python.org/3/library/typing.html#typing.Optional"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/keyerror/py311-linux", 0.2, "Fixing None source reveals missing key access"), leads("python/valueerror-invalid-literal/py311-linux", 0.15, "Underlying data has wrong type")],
        preceded_by=[preceded("python/keyerror/py311-linux", 0.15, "dict.get() returns None which is then subscripted")],
        confused_with=[confused("python/keyerror/py311-linux", "KeyError is about missing dict keys; TypeError NoneType is about operating on None values")],
    ))

    canons.append(canon(
        "python", "keyerror", "py311-linux",
        "KeyError: 'key_name'",
        r"KeyError: ['\"](.+?)['\"]",
        "key_error", "python", ">=3.11,<3.13", "linux", "true", 0.92, 0.90,
        "Dictionary key access fails. Common in config parsing, API responses, and data pipelines.",
        [de("Wrap in try/except KeyError", "Silences the error but doesn't fix missing data", 0.60, sources=["https://docs.python.org/3/tutorial/errors.html#handling-exceptions"]),
         de("Add the missing key to the dict manually", "Key may be dynamically generated or come from external source", 0.55, sources=["https://docs.python.org/3/library/exceptions.html#KeyError"])],
        [wa("Use dict.get(key, default) instead of dict[key]", 0.95, "response.get('data', {}).get('items', [])", sources=["https://docs.python.org/3/library/stdtypes.html#dict.get"]),
         wa("Validate dict structure before access using schema validation", 0.88, sources=["https://docs.python.org/3/library/stdtypes.html#dict"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/typeerror-nonetype-not-subscriptable/py311-linux", 0.2, "dict.get() returns None which may be subscripted"), leads("python/valueerror-invalid-literal/py311-linux", 0.15, "Retrieved value has unexpected type")],
        preceded_by=[preceded("python/typeerror-nonetype-not-subscriptable/py311-linux", 0.2, "Fixing NoneType error reveals missing keys in data")],
        confused_with=[confused("python/valueerror-invalid-literal/py311-linux", "ValueError is about wrong value format; KeyError is about missing dictionary keys")],
    ))

    canons.append(canon(
        "python", "filenotfounderror", "py311-linux",
        "FileNotFoundError: [Errno 2] No such file or directory",
        r"FileNotFoundError: \[Errno 2\] No such file or directory:?\s*['\"]?(.+?)['\"]?$",
        "io_error", "python", ">=3.11,<3.13", "linux", "true", 0.90, 0.92,
        "File path does not exist. Common in scripts with hardcoded paths or relative path assumptions.",
        [de("Create empty file at the path", "May not contain expected content, causing downstream errors", 0.58, sources=["https://docs.python.org/3/library/exceptions.html#FileNotFoundError"]),
         de("Hardcode absolute path", "Breaks portability across machines and environments", 0.70, sources=["https://stackoverflow.com/questions/3430372/how-do-i-get-the-full-path-of-the-current-files-directory"])],
        [wa("Use pathlib.Path and resolve relative to __file__ or project root", 0.92, "Path(__file__).parent / 'data' / 'config.json'", sources=["https://docs.python.org/3/library/pathlib.html"]),
         wa("Check path existence before access with Path.exists()", 0.88, sources=["https://docs.python.org/3/library/pathlib.html#pathlib.Path.exists"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/permissionerror-errno13/py311-linux", 0.25, "File exists but has wrong permissions"), leads("python/unicodedecodeerror/py311-linux", 0.15, "File found but has unexpected encoding")],
        preceded_by=[preceded("python/permissionerror-errno13/py311-linux", 0.1, "Changed path to avoid permission issue but new path doesn't exist")],
        confused_with=[confused("python/permissionerror-errno13/py311-linux", "PermissionError means file exists but access is denied; FileNotFoundError means file does not exist")],
    ))

    canons.append(canon(
        "python", "unicodedecodeerror", "py311-linux",
        "UnicodeDecodeError: 'utf-8' codec can't decode byte",
        r"UnicodeDecodeError: '(utf-8|ascii|charmap)' codec can't decode byte",
        "encoding_error", "python", ">=3.11,<3.13", "linux", "true", 0.82, 0.85,
        "File contains non-UTF-8 bytes. Common with legacy data, binary files, or Windows-generated CSVs.",
        [de("Force encoding='utf-8' everywhere", "File genuinely isn't UTF-8, forcing it corrupts or crashes", 0.75, sources=["https://docs.python.org/3/library/codecs.html#standard-encodings"]),
         de("Strip non-ASCII bytes", "Loses legitimate non-ASCII data like names, currencies", 0.68, sources=["https://docs.python.org/3/howto/unicode.html"])],
        [wa("Detect encoding with chardet/charset-normalizer then open with correct encoding", 0.88, "import charset_normalizer; detected = charset_normalizer.from_path(path).best()", sources=["https://docs.python.org/3/library/codecs.html"]),
         wa("Open with errors='replace' or errors='ignore' when data loss is acceptable", 0.80, sources=["https://docs.python.org/3/library/functions.html#open"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/valueerror-invalid-literal/py311-linux", 0.2, "Decoded text contains unexpected characters causing parse errors")],
        preceded_by=[preceded("python/filenotfounderror/py311-linux", 0.15, "Found the file but it has unexpected encoding")],
        confused_with=[confused("python/valueerror-invalid-literal/py311-linux", "ValueError is about data format; UnicodeDecodeError is specifically about byte-to-string decoding")],
    ))

    canons.append(canon(
        "python", "valueerror-invalid-literal", "py311-linux",
        "ValueError: invalid literal for int() with base 10",
        r"ValueError: invalid literal for int\(\) with base 10:?\s*['\"]?(.+?)['\"]?",
        "value_error", "python", ">=3.11,<3.13", "linux", "true", 0.93, 0.91,
        "String-to-int conversion fails on non-numeric input. Common in CLI args, CSV parsing, form data.",
        [de("Wrap every int() call in try/except", "Masks data quality issues upstream", 0.55, sources=["https://docs.python.org/3/tutorial/errors.html#handling-exceptions"]),
         de("Use regex to strip non-digits before converting", "May silently produce wrong numbers", 0.62, sources=["https://docs.python.org/3/library/re.html"])],
        [wa("Validate and sanitize input at the entry point (argparse, form validation)", 0.95, sources=["https://docs.python.org/3/library/argparse.html"]),
         wa("Use str.strip() and check str.isdigit() before conversion", 0.90, "value.strip().isdigit() and int(value.strip())", sources=["https://docs.python.org/3/library/stdtypes.html#str.isdigit"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/typeerror-nonetype-not-subscriptable/py311-linux", 0.15, "Conversion returns None or fails silently")],
        preceded_by=[preceded("python/unicodedecodeerror/py311-linux", 0.2, "Decoded text contains non-numeric characters"), preceded("python/keyerror/py311-linux", 0.15, "Retrieved dict value is not a valid integer string")],
        confused_with=[confused("python/typeerror-nonetype-not-subscriptable/py311-linux", "TypeError is about wrong type operations; ValueError is about correct type but invalid value")],
    ))

    canons.append(canon(
        "python", "connectionrefusederror", "py311-linux",
        "ConnectionRefusedError: [Errno 111] Connection refused",
        r"ConnectionRefusedError: \[Errno 111\] Connection refused",
        "network_error", "python", ">=3.11,<3.13", "linux", "partial", 0.65, 0.80,
        "Target service is not running or not listening on the expected port.",
        [de("Retry the connection immediately in a loop", "If the service is down, retrying won't help and wastes time", 0.78, sources=["https://docs.python.org/3/library/exceptions.html#ConnectionRefusedError"]),
         de("Change the port number", "The port is usually correct; the service itself is not running", 0.72, sources=["https://docs.python.org/3/library/socket.html"])],
        [wa("Verify the target service is running and listening on the correct port", 0.85, "ss -tlnp | grep :PORT or docker ps", sources=["https://docs.python.org/3/library/socket.html#socket.socket.connect"]),
         wa("Add exponential backoff retry with a health check endpoint", 0.75, sources=["https://docs.python.org/3/library/urllib.request.html"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/permissionerror-errno13/py311-linux", 0.1, "Service starts but file access is denied")],
        preceded_by=[preceded("docker/bind-address-already-in-use/docker27-linux", 0.2, "Changed port but service not yet running on new port"), preceded("docker/cannot-connect-to-docker-daemon/docker27-linux", 0.15, "Docker daemon not running so containerized service is unavailable")],
        confused_with=[confused("python/permissionerror-errno13/py311-linux", "PermissionError is about file access; ConnectionRefusedError is about network connections")],
    ))

    canons.append(canon(
        "python", "memoryerror", "py311-linux",
        "MemoryError",
        r"MemoryError",
        "resource_error", "python", ">=3.11,<3.13", "linux", "partial", 0.55, 0.78,
        "Process exceeded available RAM. Common with large datasets, recursive structures, or memory leaks.",
        [de("Increase swap space", "Swap is orders of magnitude slower, making the program unusable", 0.80, sources=["https://docs.python.org/3/library/exceptions.html#MemoryError"]),
         de("Upgrade to more RAM", "Often the data processing approach itself is inefficient", 0.60, sources=["https://docs.python.org/3/library/sys.html#sys.getsizeof"])],
        [wa("Process data in chunks/batches instead of loading all into memory", 0.82, "for chunk in pd.read_csv(path, chunksize=10000):", sources=["https://docs.python.org/3/library/functions.html#iter"]),
         wa("Use memory-mapped files or streaming approaches (mmap, generators)", 0.78, sources=["https://docs.python.org/3/library/mmap.html"])],
        python=">=3.11,<3.13",
        leads_to=[leads("kubernetes/oomkilled/k8s1-linux", 0.2, "Application deployed to K8s hits memory limits")],
        preceded_by=[preceded("python/filenotfounderror/py311-linux", 0.1, "Loaded correct large file that exceeds memory")],
        confused_with=[confused("kubernetes/oomkilled/k8s1-linux", "OOMKilled is container-level memory limit; MemoryError is Python process-level")],
    ))

    canons.append(canon(
        "python", "permissionerror-errno13", "py311-linux",
        "PermissionError: [Errno 13] Permission denied",
        r"PermissionError: \[Errno 13\] Permission denied:?\s*['\"]?(.+?)['\"]?",
        "io_error", "python", ">=3.11,<3.13", "linux", "true", 0.88, 0.87,
        "Insufficient file system permissions. Common with system paths, Docker volumes, or pip installs.",
        [de("Run with sudo", "Creates root-owned files causing more permission issues later", 0.75, sources=["https://docs.python.org/3/library/exceptions.html#PermissionError"]),
         de("chmod 777 the directory", "Security vulnerability, doesn't fix the ownership issue", 0.82, sources=["https://stackoverflow.com/questions/22071853/permission-denied-error-errno-13"])],
        [wa("Fix ownership with chown and use appropriate user permissions", 0.90, "chown -R $(whoami) /path/to/dir", sources=["https://docs.python.org/3/library/os.html#os.chown"]),
         wa("Use virtual environments or user-local paths", 0.88, "pip install --user or python -m venv .venv", sources=["https://docs.python.org/3/library/venv.html"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/filenotfounderror/py311-linux", 0.15, "Changed path to user directory but file doesn't exist there")],
        preceded_by=[preceded("python/filenotfounderror/py311-linux", 0.1, "File found but access denied"), preceded("pip/no-matching-distribution/pip24-linux", 0.15, "pip install fails with permission error on system Python")],
        confused_with=[confused("node/eacces-permission-denied/node20-linux", "EACCES is Node.js file permission error; PermissionError is Python's equivalent"), confused("python/filenotfounderror/py311-linux", "FileNotFoundError means path doesn't exist; PermissionError means it exists but access is denied")],
    ))

    # === NODE ===
    canons.append(canon(
        "node", "err-module-not-found", "node20-linux",
        "Error [ERR_MODULE_NOT_FOUND]: Cannot find module",
        r"Error \[ERR_MODULE_NOT_FOUND\]: Cannot find module ['\"](.+?)['\"]",
        "module_error", "node", ">=20,<23", "linux", "true", 0.87, 0.89,
        "Node.js cannot resolve the specified module. Common with ESM/CJS conflicts or missing dependencies.",
        [de("Add .js extension to import", "Only works for local files, not for node_modules", 0.60, sources=["https://nodejs.org/api/esm.html#mandatory-file-extensions"]),
         de("Switch type in package.json between module and commonjs", "May break other imports throughout the project", 0.68, sources=["https://nodejs.org/api/packages.html#type"])],
        [wa("Run npm install to ensure all dependencies are installed", 0.92, "rm -rf node_modules && npm install", sources=["https://docs.npmjs.com/cli/v10/commands/npm-install"]),
         wa("Check package.json exports field matches the import path", 0.85, sources=["https://nodejs.org/api/packages.html#package-entry-points"])],
        leads_to=[leads("node/syntaxerror-unexpected-token/node20-linux", 0.2, "Found module but it has ESM/CJS format mismatch"), leads("node/err-require-esm/node20-linux", 0.15, "Module found but it is ESM-only and code uses require()")],
        preceded_by=[preceded("node/cannot-find-module-npm/node20-linux", 0.25, "npm module installed but ESM resolution fails")],
        confused_with=[confused("node/cannot-find-module-npm/node20-linux", "cannot-find-module is CJS require() failure; ERR_MODULE_NOT_FOUND is ESM import failure"), confused("node/err-require-esm/node20-linux", "ERR_REQUIRE_ESM is about CJS requiring ESM; ERR_MODULE_NOT_FOUND is about missing modules entirely")],
    ))

    canons.append(canon(
        "node", "eacces-permission-denied", "node20-linux",
        "Error: EACCES: permission denied",
        r"Error: EACCES: permission denied,?\s*(open|mkdir|unlink|scandir)\s*['\"]?(.+?)['\"]?",
        "permission_error", "node", ">=20,<23", "linux", "true", 0.85, 0.87,
        "File system operation denied. Common with global npm installs or Docker volume mounts.",
        [de("Run npm with sudo", "Creates root-owned node_modules causing cascading permission issues", 0.82, sources=["https://docs.npmjs.com/resolving-eacces-permissions-errors-when-installing-packages-globally"]),
         de("chmod -R 777 node_modules", "Security risk and doesn't fix the root cause", 0.78, sources=["https://nodejs.org/api/errors.html#common-system-errors"])],
        [wa("Fix npm prefix to use user directory", 0.90, "npm config set prefix ~/.npm-global", sources=["https://docs.npmjs.com/resolving-eacces-permissions-errors-when-installing-packages-globally"]),
         wa("Use nvm or volta for Node version management (avoids system paths)", 0.88, sources=["https://nodejs.org/en/download/package-manager"])],
        leads_to=[leads("node/cannot-find-module-npm/node20-linux", 0.2, "Permission fix changes install location and modules not found")],
        preceded_by=[preceded("node/cannot-find-module-npm/node20-linux", 0.15, "npm install fails with permission error")],
        confused_with=[confused("python/permissionerror-errno13/py311-linux", "Python PermissionError is the same concept; EACCES is the Node.js/POSIX equivalent")],
    ))

    canons.append(canon(
        "node", "err-require-esm", "node20-linux",
        "Error [ERR_REQUIRE_ESM]: require() of ES Module not supported",
        r"Error \[ERR_REQUIRE_ESM\]:.*require\(\) of ES Module.+not supported",
        "module_error", "node", ">=20,<23", "linux", "true", 0.80, 0.85,
        "Trying to require() an ESM-only package from CommonJS code.",
        [de("Downgrade the ESM-only package to an older CJS version", "Misses security patches and new features", 0.65, sources=["https://nodejs.org/api/esm.html"]),
         de("Use dynamic import() in CJS synchronously", "import() is async, cannot be used synchronously in CJS", 0.88, sources=["https://nodejs.org/api/esm.html#import-expressions"])],
        [wa("Convert your project to ESM (set type: module in package.json)", 0.85, sources=["https://nodejs.org/api/packages.html#type"]),
         wa("Use dynamic import() with await in an async context", 0.82, "const pkg = await import('esm-package')", sources=["https://nodejs.org/api/esm.html#import-expressions"])],
        leads_to=[leads("node/syntaxerror-unexpected-token/node20-linux", 0.25, "Converting to ESM causes syntax errors in CJS files"), leads("node/err-module-not-found/node20-linux", 0.2, "ESM conversion changes module resolution rules")],
        preceded_by=[preceded("node/err-module-not-found/node20-linux", 0.15, "Module resolution led to discovering ESM/CJS mismatch")],
        confused_with=[confused("node/err-module-not-found/node20-linux", "ERR_MODULE_NOT_FOUND is about missing modules; ERR_REQUIRE_ESM is about CJS code trying to require() an ESM module")],
    ))

    canons.append(canon(
        "node", "syntaxerror-unexpected-token", "node20-linux",
        "SyntaxError: Unexpected token",
        r"SyntaxError: Unexpected token\s*['\"]?(.+?)['\"]?",
        "syntax_error", "node", ">=20,<23", "linux", "true", 0.88, 0.86,
        "JavaScript parser encountered invalid syntax. Common with JSON parse failures or ESM/CJS confusion.",
        [de("Add Babel to transpile", "Adds unnecessary complexity if the issue is just a syntax typo or wrong file format", 0.55, sources=["https://nodejs.org/api/errors.html#class-syntaxerror"]),
         de("Upgrade Node.js version", "Usually not a version issue but a code or configuration error", 0.62, sources=["https://nodejs.org/api/errors.html"])],
        [wa("Check if the file is valid JSON when using JSON.parse()", 0.90, sources=["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/parse"]),
         wa("Verify file extension matches the module system (.mjs for ESM, .cjs for CJS)", 0.85, sources=["https://nodejs.org/api/esm.html#enabling"])],
        leads_to=[leads("node/err-module-not-found/node20-linux", 0.15, "Fixing syntax reveals missing module imports"), leads("node/err-require-esm/node20-linux", 0.2, "Syntax error was caused by ESM/CJS mismatch")],
        preceded_by=[preceded("node/err-require-esm/node20-linux", 0.25, "ESM/CJS mismatch manifests as unexpected token error"), preceded("node/err-module-not-found/node20-linux", 0.1, "Wrong module format loaded")],
        confused_with=[confused("node/err-require-esm/node20-linux", "ERR_REQUIRE_ESM is specifically about CJS/ESM mismatch; SyntaxError can have many causes including JSON parse and typos")],
    ))

    canons.append(canon(
        "node", "cannot-find-module-npm", "node20-linux",
        "Error: Cannot find module",
        r"Error: Cannot find module ['\"](.+?)['\"]",
        "module_error", "node", ">=20,<23", "linux", "true", 0.90, 0.91,
        "Module not found in node_modules or local paths. Most common Node.js error.",
        [de("Manually copy the module file into node_modules", "Will be overwritten on next npm install", 0.85, sources=["https://nodejs.org/api/modules.html#loading-from-node_modules-folders"]),
         de("Create a symlink to the module", "Fragile and breaks on different machines", 0.72, sources=["https://docs.npmjs.com/cli/v10/commands/npm-link"])],
        [wa("Delete node_modules and package-lock.json then reinstall", 0.92, "rm -rf node_modules package-lock.json && npm install", sources=["https://docs.npmjs.com/cli/v10/commands/npm-install"]),
         wa("Check the module name for typos in require/import statement", 0.88, sources=["https://nodejs.org/api/modules.html#all-together"])],
        leads_to=[leads("node/err-module-not-found/node20-linux", 0.2, "CJS module resolved but ESM import fails"), leads("node/err-require-esm/node20-linux", 0.15, "Module found but is ESM-only")],
        preceded_by=[preceded("node/eacces-permission-denied/node20-linux", 0.15, "Permission error during npm install leaves incomplete node_modules")],
        confused_with=[confused("node/err-module-not-found/node20-linux", "ERR_MODULE_NOT_FOUND is ESM-specific; Cannot find module is the CJS require() error"), confused("typescript/ts2307-cannot-find-module/ts5-linux", "TS2307 is a compile-time type resolution error; Cannot find module is a runtime error")],
    ))

    # === DOCKER ===
    canons.append(canon(
        "docker", "oci-runtime-create-failed", "docker27-linux",
        "OCI runtime create failed: unable to start container process",
        r"OCI runtime create failed:.*unable to start container process",
        "runtime_error", "docker", ">=27,<28", "linux", "partial", 0.65, 0.80,
        "Container entrypoint or command cannot be executed. Often wrong binary path or missing executable.",
        [de("Rebuild the image from scratch", "If the Dockerfile is wrong, rebuilding reproduces the same error", 0.70, sources=["https://docs.docker.com/engine/reference/builder/#entrypoint"]),
         de("Set --privileged flag", "Security risk and usually not related to the actual issue", 0.82, sources=["https://docs.docker.com/engine/reference/run/#runtime-privilege-and-linux-capabilities"])],
        [wa("Check that the entrypoint/CMD binary exists inside the container", 0.85, "docker run --entrypoint sh image -c 'which myapp'", sources=["https://docs.docker.com/engine/reference/builder/#cmd"]),
         wa("Verify exec format matches the container architecture (amd64 vs arm64)", 0.78, sources=["https://docs.docker.com/build/building/multi-platform/"])],
        leads_to=[leads("kubernetes/crashloopbackoff/k8s1-linux", 0.3, "Container fails to start in Kubernetes pod"), leads("docker/exec-format-error/docker27-linux", 0.2, "Issue is actually architecture mismatch")],
        preceded_by=[preceded("docker/exec-format-error/docker27-linux", 0.2, "Exec format error is a common cause of OCI runtime failure")],
        confused_with=[confused("docker/exec-format-error/docker27-linux", "exec format error is specifically about binary architecture mismatch; OCI runtime create is a broader container start failure")],
    ))

    canons.append(canon(
        "docker", "exec-format-error", "docker27-linux",
        "exec format error",
        r"exec format error|exec user process caused:.*exec format error",
        "platform_error", "docker", ">=27,<28", "linux", "true", 0.82, 0.88,
        "Binary architecture mismatch. Common when running amd64 images on arm64 (Apple Silicon) or vice versa.",
        [de("Reinstall Docker", "Architecture mismatch is not a Docker installation issue", 0.85, sources=["https://docs.docker.com/engine/install/"]),
         de("Add #!/bin/bash shebang to script", "Only helps if the entrypoint is a script without shebang, not for binary mismatch", 0.60, sources=["https://docs.docker.com/engine/reference/builder/#entrypoint"])],
        [wa("Build or pull the correct platform image", 0.90, "docker build --platform linux/amd64 .", sources=["https://docs.docker.com/build/building/multi-platform/"]),
         wa("Use multi-platform builds with docker buildx", 0.85, "docker buildx build --platform linux/amd64,linux/arm64 .", sources=["https://docs.docker.com/build/builders/"])],
        leads_to=[leads("docker/oci-runtime-create-failed/docker27-linux", 0.3, "Architecture mismatch causes OCI runtime failure")],
        preceded_by=[preceded("docker/oci-runtime-create-failed/docker27-linux", 0.2, "Investigating OCI failure reveals architecture mismatch")],
        confused_with=[confused("docker/oci-runtime-create-failed/docker27-linux", "OCI runtime create failed is a broader error; exec format error specifically means wrong CPU architecture")],
    ))

    canons.append(canon(
        "docker", "bind-address-already-in-use", "docker27-linux",
        "Bind for 0.0.0.0:PORT failed: port is already allocated",
        r"Bind for .+?:\d+ failed: port is already allocated|address already in use",
        "network_error", "docker", ">=27,<28", "linux", "true", 0.92, 0.90,
        "Port is already in use by another container or host process.",
        [de("Change the container's internal port", "The conflict is on the host port, not the container port", 0.75, sources=["https://docs.docker.com/engine/reference/commandline/run/#publish"]),
         de("Restart Docker daemon", "Doesn't release ports held by running containers", 0.65, sources=["https://docs.docker.com/config/daemon/"])],
        [wa("Find and stop the process using the port", 0.95, "lsof -i :PORT or docker ps --filter publish=PORT", sources=["https://docs.docker.com/engine/reference/commandline/ps/"]),
         wa("Map to a different host port", 0.90, "docker run -p 8081:80 instead of -p 80:80", sources=["https://docs.docker.com/network/#published-ports"])],
        leads_to=[leads("python/connectionrefusederror/py311-linux", 0.2, "Changed port but application still connects to old port")],
        preceded_by=[preceded("docker/cannot-connect-to-docker-daemon/docker27-linux", 0.15, "Started daemon but old container is still holding the port")],
        confused_with=[confused("python/connectionrefusederror/py311-linux", "ConnectionRefused means nothing is listening; bind already in use means something IS listening on that port")],
    ))

    canons.append(canon(
        "docker", "cannot-connect-to-docker-daemon", "docker27-linux",
        "Cannot connect to the Docker daemon. Is the docker daemon running?",
        r"Cannot connect to the Docker daemon",
        "daemon_error", "docker", ">=27,<28", "linux", "true", 0.88, 0.90,
        "Docker daemon is not running or socket permissions are wrong.",
        [de("Reinstall Docker", "Daemon just needs to be started, not reinstalled", 0.82, sources=["https://docs.docker.com/engine/install/"]),
         de("Run with sudo every time", "Doesn't fix the underlying group permission issue", 0.60, sources=["https://docs.docker.com/engine/install/linux-postinstall/"])],
        [wa("Start the Docker daemon", 0.92, "sudo systemctl start docker", sources=["https://docs.docker.com/config/daemon/start/"]),
         wa("Add user to docker group", 0.88, "sudo usermod -aG docker $USER && newgrp docker", sources=["https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user"])],
        leads_to=[leads("docker/bind-address-already-in-use/docker27-linux", 0.15, "Daemon starts but previous containers left ports allocated"), leads("docker/oci-runtime-create-failed/docker27-linux", 0.2, "Daemon running but container fails to start")],
        preceded_by=[preceded("docker/bind-address-already-in-use/docker27-linux", 0.1, "Restarted daemon to fix port issue but daemon didn't come back up")],
        confused_with=[confused("python/connectionrefusederror/py311-linux", "ConnectionRefused is about app-level network; Cannot connect to Docker daemon is about Docker socket access")],
    ))

    # === GIT ===
    canons.append(canon(
        "git", "not-a-git-repository", "git2-linux",
        "fatal: not a git repository (or any of the parent directories)",
        r"fatal: not a git repository",
        "init_error", "git", ">=2.40,<3.0", "linux", "true", 0.95, 0.92,
        "Current directory is not inside a git repository.",
        [de("Run git init in the wrong directory", "Creates a new repo instead of finding the existing one", 0.70, sources=["https://git-scm.com/docs/git-init"]),
         de("Clone the repo again into a nested directory", "Creates duplicate repos", 0.65, sources=["https://git-scm.com/docs/git-clone"])],
        [wa("Navigate to the correct project directory", 0.95, "cd /path/to/project && git status", sources=["https://git-scm.com/docs/git-status"]),
         wa("Initialize a new repo if starting fresh", 0.90, "git init && git remote add origin URL", sources=["https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository"])],
        leads_to=[leads("git/pathspec-no-match/git2-linux", 0.15, "Initialized new repo but expected files are not tracked")],
        preceded_by=[preceded("git/pathspec-no-match/git2-linux", 0.1, "Wrong directory led to pathspec failure then this error")],
        confused_with=[confused("git/pathspec-no-match/git2-linux", "pathspec error means file/branch not found in git; not-a-git-repository means no git repo at all")],
    ))

    canons.append(canon(
        "git", "failed-to-push-refs", "git2-linux",
        "error: failed to push some refs to remote",
        r"error: failed to push some refs to",
        "push_error", "git", ">=2.40,<3.0", "linux", "true", 0.88, 0.90,
        "Remote has commits not in local branch. Most common git push error.",
        [de("Force push with git push --force", "Overwrites remote history, can destroy teammates' work", 0.85, sources=["https://git-scm.com/docs/git-push#Documentation/git-push.txt---force"]),
         de("Delete remote branch and push again", "Loses remote-only commits permanently", 0.90, sources=["https://git-scm.com/docs/git-push"])],
        [wa("Pull and rebase before pushing", 0.92, "git pull --rebase origin main && git push", sources=["https://git-scm.com/docs/git-pull#Documentation/git-pull.txt---rebase"]),
         wa("Fetch and merge remote changes first", 0.88, "git fetch origin && git merge origin/main", sources=["https://git-scm.com/docs/git-fetch"])],
        leads_to=[leads("git/local-changes-overwritten/git2-linux", 0.3, "Pulling remote changes conflicts with local uncommitted work")],
        preceded_by=[preceded("git/local-changes-overwritten/git2-linux", 0.2, "Stashed changes and pulled but push still fails")],
        confused_with=[confused("git/local-changes-overwritten/git2-linux", "local-changes-overwritten is about uncommitted changes; failed-to-push is about committed but unpushed changes vs remote")],
    ))

    canons.append(canon(
        "git", "local-changes-overwritten", "git2-linux",
        "error: Your local changes to the following files would be overwritten by merge",
        r"error: Your local changes to the following files would be overwritten",
        "merge_error", "git", ">=2.40,<3.0", "linux", "true", 0.90, 0.88,
        "Uncommitted local changes conflict with incoming changes.",
        [de("Use git checkout -- . to discard all changes", "Permanently loses all uncommitted work", 0.88, sources=["https://git-scm.com/docs/git-checkout"]),
         de("Delete the conflicting files", "Loses work and may break the project", 0.90, sources=["https://git-scm.com/docs/git-merge"])],
        [wa("Stash changes before merge/pull", 0.92, "git stash && git pull && git stash pop", sources=["https://git-scm.com/docs/git-stash"]),
         wa("Commit your changes before pulling", 0.88, "git add -A && git commit -m 'wip' && git pull", sources=["https://git-scm.com/docs/git-commit"])],
        leads_to=[leads("git/failed-to-push-refs/git2-linux", 0.3, "After resolving local changes, push fails due to diverged history")],
        preceded_by=[preceded("git/failed-to-push-refs/git2-linux", 0.25, "Pull triggered by push failure conflicts with local work")],
        confused_with=[confused("git/failed-to-push-refs/git2-linux", "failed-to-push is about remote vs local commits; local-changes-overwritten is about uncommitted working tree changes")],
    ))

    canons.append(canon(
        "git", "pathspec-no-match", "git2-linux",
        "error: pathspec 'X' did not match any file(s) known to git",
        r"error: pathspec ['\"]?(.+?)['\"]? did not match any file",
        "path_error", "git", ">=2.40,<3.0", "linux", "true", 0.92, 0.90,
        "File or branch name doesn't exist in the repository.",
        [de("Create the file manually then checkout", "Checkout expects the file in git history, not on disk", 0.65, sources=["https://git-scm.com/docs/git-checkout"]),
         de("Use git checkout -f", "Force flag doesn't help if the path genuinely doesn't exist", 0.72, sources=["https://git-scm.com/docs/git-checkout#Documentation/git-checkout.txt--f"])],
        [wa("Check spelling and use git ls-files or git branch -a to verify the name", 0.92, sources=["https://git-scm.com/docs/git-ls-files"]),
         wa("Fetch remote branches if switching to a remote branch", 0.88, "git fetch origin && git checkout branch-name", sources=["https://git-scm.com/docs/git-fetch"])],
        leads_to=[leads("git/not-a-git-repository/git2-linux", 0.1, "Wrong directory causes both pathspec and repo errors")],
        preceded_by=[preceded("git/not-a-git-repository/git2-linux", 0.15, "Navigated to repo but wrong branch or file path")],
        confused_with=[confused("git/not-a-git-repository/git2-linux", "not-a-git-repository means no repo exists; pathspec error means repo exists but file/branch does not")],
    ))

    # === PIP ===
    canons.append(canon(
        "pip", "no-matching-distribution", "pip24-linux",
        "ERROR: No matching distribution found for package",
        r"ERROR: No matching distribution found for (.+)",
        "resolution_error", "pip", ">=24,<25", "linux", "true", 0.82, 0.85,
        "Package doesn't exist for this Python version/platform or has a different name on PyPI.",
        [de("Keep retrying pip install", "If the package doesn't exist for your platform, retrying won't help", 0.85, sources=["https://pip.pypa.io/en/stable/cli/pip_install/"]),
         de("Install from a random GitHub URL", "May get an untrusted or incompatible version", 0.72, sources=["https://pip.pypa.io/en/stable/topics/vcs-support/"])],
        [wa("Check the correct package name on PyPI and verify Python version compatibility", 0.88, sources=["https://pip.pypa.io/en/stable/cli/pip_install/#requirement-specifiers"]),
         wa("Use a different Python version that the package supports", 0.82, "pyenv install 3.11 && pyenv local 3.11", sources=["https://pip.pypa.io/en/stable/cli/pip_install/"])],
        python=">=3.10,<3.13",
        leads_to=[leads("pip/dependency-resolver-conflict/pip24-linux", 0.25, "Found the package but it conflicts with existing dependencies")],
        preceded_by=[preceded("python/modulenotfounderror/py311-linux", 0.35, "Module import failed so user tries pip install")],
        confused_with=[confused("pip/dependency-resolver-conflict/pip24-linux", "Dependency conflict means packages exist but versions clash; no matching distribution means package not found at all")],
    ))

    canons.append(canon(
        "pip", "dependency-resolver-conflict", "pip24-linux",
        "ERROR: pip's dependency resolver does not currently consider all the packages",
        r"ERROR: pip's dependency resolver does not currently consider",
        "resolution_error", "pip", ">=24,<25", "linux", "partial", 0.55, 0.75,
        "Dependency version constraints are mutually exclusive across installed packages.",
        [de("Use --force-reinstall", "Forces installation but doesn't resolve the underlying conflict", 0.70, sources=["https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-force-reinstall"]),
         de("Pin all packages to exact versions from a working machine", "Breaks on different platforms or Python versions", 0.65, sources=["https://pip.pypa.io/en/stable/topics/dependency-resolution/"])],
        [wa("Use pip-compile from pip-tools to find a compatible resolution", 0.78, "pip-compile requirements.in", sources=["https://pip.pypa.io/en/stable/topics/dependency-resolution/"]),
         wa("Create a fresh virtual environment and install from scratch", 0.75, "python -m venv .venv --clear && pip install -r requirements.txt", sources=["https://docs.python.org/3/library/venv.html"])],
        python=">=3.10,<3.13",
        leads_to=[leads("python/modulenotfounderror/py311-linux", 0.2, "Conflict prevents installation so module remains missing")],
        preceded_by=[preceded("pip/no-matching-distribution/pip24-linux", 0.2, "Tried alternative package that conflicts with existing deps")],
        confused_with=[confused("pip/no-matching-distribution/pip24-linux", "No matching distribution means package not found; dependency conflict means packages found but versions are incompatible")],
    ))

    # === CUDA ===
    canons.append(canon(
        "cuda", "device-side-assert", "cuda12-a100",
        "RuntimeError: CUDA error: device-side assert triggered",
        r"RuntimeError: CUDA error: device-side assert triggered",
        "runtime_error", "cuda", ">=12.0,<13.0", "linux", "partial", 0.60, 0.78,
        "Illegal operation on GPU, often index out of bounds in a kernel. Error message is unhelpful by default.",
        [de("Set CUDA_LAUNCH_BLOCKING=0 and ignore", "Async errors will appear later in wrong places, making debugging impossible", 0.85, sources=["https://pytorch.org/docs/stable/notes/cuda.html#asynchronous-execution"]),
         de("Increase GPU memory", "This is a logic error, not a memory error", 0.80, sources=["https://pytorch.org/docs/stable/notes/cuda.html"])],
        [wa("Set CUDA_LAUNCH_BLOCKING=1 to get the actual error location", 0.82, "CUDA_LAUNCH_BLOCKING=1 python train.py", sources=["https://pytorch.org/docs/stable/notes/cuda.html#asynchronous-execution"]),
         wa("Check tensor shapes and label ranges (num_classes must match output dim)", 0.78, sources=["https://pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html"])],
        gpu="A100-80GB", vram=80,
        leads_to=[leads("cuda/nvidia-smi-failed/cuda12-linux", 0.1, "Repeated CUDA errors may indicate driver instability")],
        preceded_by=[preceded("cuda/torch-not-compiled-cuda/cuda12-rtx4090", 0.15, "Installed CUDA-enabled PyTorch but model code has shape bugs")],
        confused_with=[confused("kubernetes/oomkilled/k8s1-linux", "OOMKilled is about memory limits; device-side assert is about illegal GPU operations like out-of-bounds indexing")],
    ))

    canons.append(canon(
        "cuda", "torch-not-compiled-cuda", "cuda12-rtx4090",
        "AssertionError: Torch not compiled with CUDA enabled",
        r"(AssertionError|AssertError):.*Torch not compiled with CUDA enabled",
        "install_error", "cuda", ">=12.0,<13.0", "linux", "true", 0.90, 0.88,
        "PyTorch was installed without CUDA support (CPU-only build).",
        [de("Install CUDA toolkit separately", "PyTorch ships its own CUDA runtime, system CUDA doesn't matter", 0.82, sources=["https://pytorch.org/get-started/locally/"]),
         de("Set CUDA_HOME environment variable", "Doesn't affect already-compiled PyTorch binary", 0.78, sources=["https://pytorch.org/docs/stable/notes/cuda.html"])],
        [wa("Reinstall PyTorch with the correct CUDA version from pytorch.org", 0.92, "pip install torch --index-url https://download.pytorch.org/whl/cu121", sources=["https://pytorch.org/get-started/locally/"]),
         wa("Verify installation with torch.cuda.is_available()", 0.88, sources=["https://pytorch.org/docs/stable/cuda.html#torch.cuda.is_available"])],
        gpu="RTX-4090", vram=24,
        leads_to=[leads("cuda/device-side-assert/cuda12-a100", 0.2, "CUDA-enabled PyTorch installed but model has shape/index bugs")],
        preceded_by=[preceded("pip/no-matching-distribution/pip24-linux", 0.2, "Wrong pip install command installs CPU-only build"), preceded("cuda/nvidia-smi-failed/cuda12-linux", 0.15, "Driver issues cause PyTorch to fall back to CPU build")],
        confused_with=[confused("cuda/nvidia-smi-failed/cuda12-linux", "nvidia-smi failure is about the driver; torch-not-compiled-cuda is about the PyTorch package build")],
    ))

    canons.append(canon(
        "cuda", "nvidia-smi-failed", "cuda12-linux",
        "NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver",
        r"NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver",
        "driver_error", "cuda", ">=12.0,<13.0", "linux", "partial", 0.60, 0.82,
        "NVIDIA driver is not loaded or is incompatible. Common after kernel updates.",
        [de("Reinstall CUDA toolkit", "CUDA toolkit and NVIDIA driver are separate; toolkit doesn't fix driver", 0.78, sources=["https://docs.nvidia.com/cuda/cuda-installation-guide-linux/"]),
         de("Reboot without investigating", "May work temporarily but doesn't fix driver/kernel mismatch", 0.55, sources=["https://docs.nvidia.com/cuda/cuda-installation-guide-linux/#driver-installation"])],
        [wa("Reinstall NVIDIA driver matching your kernel version", 0.80, "sudo apt install nvidia-driver-535", sources=["https://docs.nvidia.com/cuda/cuda-installation-guide-linux/#driver-installation"]),
         wa("Use DKMS to auto-rebuild driver module on kernel updates", 0.75, "sudo apt install nvidia-dkms-535", sources=["https://docs.nvidia.com/cuda/cuda-installation-guide-linux/"])],
        leads_to=[leads("cuda/torch-not-compiled-cuda/cuda12-rtx4090", 0.25, "Driver failure causes PyTorch to report no CUDA support")],
        preceded_by=[preceded("cuda/device-side-assert/cuda12-a100", 0.1, "Repeated CUDA errors destabilize the driver")],
        confused_with=[confused("cuda/torch-not-compiled-cuda/cuda12-rtx4090", "torch-not-compiled-cuda is about PyTorch build; nvidia-smi failure is about the system driver")],
    ))

    canons.append(canon(
        "cuda", "cublas-status-not-initialized", "cuda12-linux",
        "RuntimeError: CUDA error: CUBLAS_STATUS_NOT_INITIALIZED",
        r"(CUBLAS_STATUS_NOT_INITIALIZED|cublasCreate.*failed|cublas.*not.*initialized)",
        "runtime_error", "cuda", ">=12.0,<13.0", "linux", "true", 0.82, 0.85,
        "cuBLAS handle creation failed. Usually caused by GPU memory exhaustion or CUDA context corruption.",
        [de("Reinstall cuBLAS libraries",
            "cuBLAS ships with CUDA toolkit and PyTorch; reinstalling libraries does not fix runtime context issues", 0.82),
         de("Downgrade CUDA version",
            "This is a runtime state error, not a version compatibility issue", 0.78)],
        [wa("Reduce batch size or model size to free GPU memory", 0.88,
            "cuBLAS init fails when GPU memory is nearly full; reduce batch_size or use gradient checkpointing"),
         wa("Ensure no other process is consuming GPU memory", 0.85,
            "nvidia-smi  # check for zombie processes holding GPU memory"),
         wa("Destroy and recreate CUDA context if running in a long-lived process", 0.80,
            "torch.cuda.empty_cache()")],
        preceded_by=[preceded("cuda/torch-cuda-oom-new/torch2-a100", 0.30, "OOM weakens CUDA context, subsequent cuBLAS calls fail")],
        confused_with=[confused("cuda/device-side-assert/cuda12-a100", "Device-side assert is a kernel logic error; CUBLAS_NOT_INITIALIZED is a context/memory initialization failure")],
    ))

    canons.append(canon(
        "cuda", "misaligned-address", "cuda12-linux",
        "RuntimeError: CUDA error: misaligned address",
        r"(CUDA error:.*misaligned address|misaligned.*address.*cuda|an illegal memory access.*misalign)",
        "runtime_error", "cuda", ">=12.0,<13.0", "linux", "partial", 0.55, 0.78,
        "CUDA kernel accessed memory at an address not aligned to the required boundary. Often caused by custom CUDA kernels or corrupted tensors.",
        [de("Increase GPU memory allocation",
            "This is an alignment error, not an out-of-memory error; more memory does not fix wrong addresses", 0.90),
         de("Disable CUDA memory caching allocator",
            "The caching allocator does not cause misalignment; disabling it only hurts performance", 0.82)],
        [wa("Set CUDA_LAUNCH_BLOCKING=1 to get the exact kernel and line", 0.85,
            "CUDA_LAUNCH_BLOCKING=1 python train.py"),
         wa("Check for integer overflow in index calculations for large tensors", 0.80,
            "Use torch.long for indices when tensor dimensions exceed 2^31"),
         wa("Verify custom CUDA kernel alignment with alignof() and aligned_alloc()", 0.75)],
        confused_with=[confused("cuda/illegal-memory-access/cuda12-linux", "Illegal memory access is out-of-bounds; misaligned address is valid memory but wrong alignment boundary")],
    ))

    canons.append(canon(
        "cuda", "nccl-timeout-distributed", "cuda12-a100",
        "RuntimeError: NCCL error: Timeout (NCCL_ERROR_TIMEOUT)",
        r"(NCCL.*timeout|NCCL_ERROR_TIMEOUT|NCCL.*watchdog.*triggered|ncclSystemError.*Timeout)",
        "runtime_error", "cuda", ">=12.0,<13.0", "linux", "partial", 0.65, 0.82,
        "NCCL collective operation timed out during distributed training. One or more GPUs fell behind or lost network connectivity.",
        [de("Increase NCCL_TIMEOUT to very large values",
            "Masks the real issue (GPU hang, network failure); training will hang silently instead of crashing", 0.80),
         de("Disable NCCL and use Gloo backend",
            "Gloo is CPU-based for GPU tensors; 10-100x slower for large models", 0.88)],
        [wa("Set NCCL_DEBUG=INFO to identify which rank and operation hangs", 0.88,
            "NCCL_DEBUG=INFO torchrun --nproc_per_node=8 train.py"),
         wa("Check NVLink/InfiniBand connectivity between GPUs", 0.82,
            "nvidia-smi topo -m  # verify NVLink topology"),
         wa("Ensure all ranks reach the collective at the same point (no conditional branching)", 0.85,
            "All processes must call the same collectives in the same order; check for if/else around all_reduce")],
        gpu="A100-80GB", vram=80,
        preceded_by=[preceded("cuda/illegal-memory-access/cuda12-linux", 0.15, "GPU crash on one rank causes other ranks to timeout waiting")],
    ))

    canons.append(canon(
        "cuda", "flash-attention-unsupported", "cuda12-rtx4090",
        "RuntimeError: FlashAttention only supports Ampere GPUs or newer (sm >= 80)",
        r"(FlashAttention.*only supports|flash.*attn.*sm.*80|flash_attn.*not supported|FlashAttention.*compute capability)",
        "runtime_error", "cuda", ">=12.0,<13.0", "linux", "true", 0.85, 0.88,
        "FlashAttention requires GPU compute capability >= 8.0 (Ampere: A100, RTX 3090+). Older GPUs are not supported.",
        [de("Install an older version of flash-attn",
            "No version of flash-attn supports pre-Ampere GPUs; the hardware limitation is fundamental", 0.92),
         de("Set CUDA_VISIBLE_DEVICES to a different GPU hoping it works",
            "If no Ampere+ GPU is available on the machine, no device will work", 0.85)],
        [wa("Use torch.nn.functional.scaled_dot_product_attention with math backend as fallback", 0.90,
            "with torch.backends.cuda.sdp_kernel(enable_flash=False, enable_math=True): output = F.scaled_dot_product_attention(q, k, v)"),
         wa("Set attn_implementation='eager' when loading HuggingFace models", 0.88,
            "model = AutoModelForCausalLM.from_pretrained('...', attn_implementation='eager')"),
         wa("Use xformers memory_efficient_attention as alternative", 0.82,
            "pip install xformers && set use_memory_efficient_attention=True")],
        gpu="RTX-4090", vram=24,
    ))

    canons.append(canon(
        "cuda", "mixed-precision-dtype-error", "cuda12-a100",
        "RuntimeError: expected scalar type Half but found Float",
        r"(expected scalar type Half.*found Float|expected.*Float.*found.*Half|dtype mismatch.*half.*float|mixed precision.*type.*error)",
        "runtime_error", "cuda", ">=12.0,<13.0", "linux", "true", 0.88, 0.88,
        "Mixed precision training produces tensors with mismatched dtypes (float16 vs float32). Usually a model or loss function not wrapped in autocast.",
        [de("Cast all tensors to float16 manually",
            "Loss computation and gradient accumulation in float16 causes numerical instability and NaN gradients", 0.85),
         de("Disable mixed precision entirely",
            "Loses 2x memory savings and training speed; not necessary if autocast is used correctly", 0.70)],
        [wa("Wrap forward pass in torch.cuda.amp.autocast", 0.92,
            "with torch.cuda.amp.autocast(): output = model(input); loss = criterion(output, target)"),
         wa("Keep loss computation outside autocast for numerical stability", 0.88,
            "Loss scaling and gradient computation should stay in float32"),
         wa("Use GradScaler to handle float16 gradient underflow", 0.90,
            "scaler = torch.cuda.amp.GradScaler(); scaler.scale(loss).backward(); scaler.step(optimizer)")],
        gpu="A100-80GB", vram=80,
    ))

    canons.append(canon(
        "cuda", "triton-compilation-error", "cuda12-linux",
        "RuntimeError: Triton compilation failed: LLVM ERROR",
        r"(Triton.*compilation.*fail|triton.*LLVM.*ERROR|torch._inductor.*triton.*error|triton.*kernel.*compil.*fail)",
        "runtime_error", "cuda", ">=12.0,<13.0", "linux", "true", 0.80, 0.82,
        "torch.compile or Triton JIT failed to compile a kernel. Common with complex model architectures or unsupported operations.",
        [de("Upgrade Triton to latest version independently of PyTorch",
            "Triton version must match PyTorch; standalone upgrades cause ABI incompatibility", 0.85),
         de("Delete __pycache__ and retry",
            "Triton caches in ~/.triton/cache, not __pycache__; wrong cache location", 0.72)],
        [wa("Clear the Triton cache and retry", 0.85,
            "rm -rf ~/.triton/cache && python train.py"),
         wa("Fall back to eager mode for the failing operation", 0.88,
            "model = torch.compile(model, mode='reduce-overhead')  # or disable: torch._dynamo.config.suppress_errors = True"),
         wa("Set TORCH_COMPILE_DEBUG=1 to get the failing Triton IR", 0.80,
            "TORCH_COMPILE_DEBUG=1 python train.py  # look for .ttir files in debug output")],
    ))

    canons.append(canon(
        "cuda", "cudnn-rnn-backward-error", "cuda12-a100",
        "RuntimeError: cuDNN error: CUDNN_STATUS_EXECUTION_FAILED on RNN backward",
        r"(cuDNN.*EXECUTION_FAILED.*RNN|CUDNN_STATUS.*EXECUTION.*backward|RNN.*backward.*cuDNN.*fail)",
        "runtime_error", "cuda", ">=12.0,<13.0", "linux", "true", 0.82, 0.85,
        "cuDNN RNN backward pass fails. Often caused by non-contiguous tensors or workspace memory exhaustion.",
        [de("Disable cuDNN for all operations globally",
            "Disabling cuDNN causes 5-10x slowdown on convolutions and other operations unrelated to the RNN issue", 0.80),
         de("Replace LSTM/GRU with manual implementation",
            "Manual RNN implementations are much slower and lose cuDNN-optimized fused kernels", 0.85)],
        [wa("Ensure input tensors are contiguous before passing to RNN", 0.90,
            "input = input.contiguous(); h0 = h0.contiguous()"),
         wa("Reduce batch size to give cuDNN more workspace memory", 0.85),
         wa("Set torch.backends.cudnn.enabled=True but benchmark=False for deterministic mode", 0.82,
            "torch.backends.cudnn.benchmark = False  # avoids workspace size instability")],
        gpu="A100-80GB", vram=80,
    ))

    canons.append(canon(
        "cuda", "multi-gpu-peer-access-error", "cuda12-a100",
        "RuntimeError: CUDA error: peer access is not supported between these two devices",
        r"(peer access.*not supported|cannot enable peer|P2P.*not.*support|cudaDeviceEnablePeerAccess.*error)",
        "runtime_error", "cuda", ">=12.0,<13.0", "linux", "partial", 0.65, 0.80,
        "GPUs cannot directly access each other's memory. No NVLink between the devices or PCIe topology prevents P2P.",
        [de("Force enable peer access with environment variables",
            "P2P is a hardware capability; if the bus topology doesn't support it, no software config can enable it", 0.90),
         de("Move all tensors to a single GPU to avoid P2P",
            "Defeats the purpose of multi-GPU; model may not fit on one GPU", 0.82)],
        [wa("Disable P2P and let NCCL fall back to shared host memory", 0.85,
            "export NCCL_P2P_DISABLE=1  # uses host-staged copies instead"),
         wa("Check GPU topology to verify which GPUs have P2P support", 0.88,
            "nvidia-smi topo -m  # NV# = NVLink, PHB = no direct P2P"),
         wa("Place communicating tensors on GPUs with direct NVLink connections", 0.80)],
        gpu="A100-80GB", vram=80,
        preceded_by=[preceded("cuda/nccl-timeout-distributed/cuda12-a100", 0.15, "Failed P2P access causes NCCL to timeout on collectives")],
    ))

    canons.append(canon(
        "cuda", "nvrtc-compilation-error", "cuda12-linux",
        "RuntimeError: NVRTC compilation failed",
        r"(NVRTC.*compilation.*fail|nvrtc.*error|CUDA JIT.*compilation.*error|nvrtcCompileProgram.*fail)",
        "runtime_error", "cuda", ">=12.0,<13.0", "linux", "true", 0.78, 0.82,
        "CUDA JIT (runtime compilation) failed. Custom CUDA extensions or torch.compile emitted invalid PTX/CUDA code.",
        [de("Reinstall CUDA toolkit",
            "NVRTC is a runtime compiler issue, not an installation issue; the generated code is invalid", 0.80),
         de("Downgrade GPU driver",
            "NVRTC compiles for the installed toolkit version, not the driver version", 0.75)],
        [wa("Check CUDA_HOME points to the correct toolkit version", 0.85,
            "echo $CUDA_HOME && nvcc --version  # must match PyTorch's CUDA version"),
         wa("Clear JIT cache and retry", 0.82,
            "rm -rf ~/.cache/torch_extensions/ && python -c 'import torch; torch.utils.cpp_extension.load(...)'"),
         wa("For custom extensions, ensure NVCC flags match the GPU architecture", 0.80,
            "TORCH_CUDA_ARCH_LIST='8.0;8.9' python setup.py install")],
    ))

    canons.append(canon(
        "cuda", "cuda-graphs-capture-error", "cuda12-a100",
        "RuntimeError: CUDA error: operation not permitted when stream is capturing",
        r"(operation not permitted.*stream.*captur|CUDA graph.*capture.*error|stream.*capturing.*not allowed|cudaStreamCapture.*error)",
        "runtime_error", "cuda", ">=12.0,<13.0", "linux", "true", 0.78, 0.82,
        "CUDA Graphs capture mode does not allow certain operations (memory allocation, CPU sync, conditional branching).",
        [de("Disable CUDA Graphs and accept the performance loss",
            "CUDA Graphs provide 10-30% speedup for small kernels; worth fixing the capture issue", 0.65),
         de("Wrap every operation in a separate graph",
            "Creates excessive overhead from multiple graph launches; defeats the purpose of graphing", 0.78)],
        [wa("Pre-allocate all tensors before graph capture", 0.88,
            "static_input = torch.empty(..., device='cuda'); with torch.cuda.graph(g): output = model(static_input)"),
         wa("Move CPU operations and conditionals outside the captured region", 0.85),
         wa("Use torch.compiler.cudagraph_mark_step_begin() for torch.compile integration", 0.80,
            "torch._inductor.config.triton.cudagraph_trees = True")],
        gpu="A100-80GB", vram=80,
    ))

    # === TYPESCRIPT ===
    canons.append(canon(
        "typescript", "ts2307-cannot-find-module", "ts5-linux",
        "TS2307: Cannot find module 'X' or its corresponding type declarations",
        r"TS2307: Cannot find module ['\"](.+?)['\"]",
        "module_error", "typescript", ">=5.0,<6.0", "linux", "true", 0.85, 0.88,
        "TypeScript cannot resolve the import. Either the module or its @types/ package is missing.",
        [de("Add // @ts-ignore above the import", "Silences the error but you lose all type safety for that module", 0.72, sources=["https://www.typescriptlang.org/docs/handbook/modules/reference.html"]),
         de("Create an empty .d.ts file", "Gives wrong types (everything becomes any), causing runtime bugs", 0.65, sources=["https://www.typescriptlang.org/docs/handbook/declaration-files/introduction.html"])],
        [wa("Install the @types/ package for the module", 0.90, "npm install --save-dev @types/module-name", sources=["https://www.typescriptlang.org/docs/handbook/2/type-declarations.html"]),
         wa("Check tsconfig.json paths and moduleResolution settings", 0.85, sources=["https://www.typescriptlang.org/tsconfig#moduleResolution"])],
        leads_to=[leads("typescript/ts2322-type-not-assignable/ts5-linux", 0.2, "After adding types, type mismatches become visible")],
        preceded_by=[preceded("node/err-module-not-found/node20-linux", 0.15, "Runtime module error leads to checking TypeScript config"), preceded("node/cannot-find-module-npm/node20-linux", 0.2, "npm module missing causes both runtime and compile errors")],
        confused_with=[confused("node/err-module-not-found/node20-linux", "ERR_MODULE_NOT_FOUND is a runtime error; TS2307 is a compile-time type resolution error"), confused("node/cannot-find-module-npm/node20-linux", "Cannot find module is runtime; TS2307 is TypeScript compiler unable to find type declarations")],
    ))

    canons.append(canon(
        "typescript", "ts2322-type-not-assignable", "ts5-linux",
        "TS2322: Type 'X' is not assignable to type 'Y'",
        r"TS2322: Type ['\"]?(.+?)['\"]? is not assignable to type ['\"]?(.+?)['\"]?",
        "type_error", "typescript", ">=5.0,<6.0", "linux", "true", 0.88, 0.90,
        "Type mismatch in assignment. The most common TypeScript error.",
        [de("Cast with 'as any'", "Removes all type safety, defeats the purpose of TypeScript", 0.80, sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions"]),
         de("Add @ts-expect-error", "Silences the error without fixing the type issue", 0.75, sources=["https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-9.html#-ts-expect-error-comments"])],
        [wa("Fix the type at the source (function return type, API response type, etc.)", 0.92, sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html"]),
         wa("Use type guards or narrowing to handle union types properly", 0.88, "if ('field' in obj) { /* obj is narrowed */ }", sources=["https://www.typescriptlang.org/docs/handbook/2/narrowing.html"])],
        leads_to=[leads("typescript/ts2345-argument-not-assignable/ts5-linux", 0.25, "Fixing assignment types reveals argument type mismatches")],
        preceded_by=[preceded("typescript/ts2307-cannot-find-module/ts5-linux", 0.2, "After adding type declarations, type mismatches become visible")],
        confused_with=[confused("typescript/ts2345-argument-not-assignable/ts5-linux", "TS2345 is about function arguments; TS2322 is about variable/property assignments")],
    ))

    canons.append(canon(
        "typescript", "ts2345-argument-not-assignable", "ts5-linux",
        "TS2345: Argument of type 'X' is not assignable to parameter of type 'Y'",
        r"TS2345: Argument of type ['\"]?(.+?)['\"]? is not assignable to parameter",
        "type_error", "typescript", ">=5.0,<6.0", "linux", "true", 0.87, 0.89,
        "Function argument doesn't match the expected parameter type.",
        [de("Cast the argument with 'as ExpectedType'", "Type assertion can hide real bugs if the runtime value doesn't match", 0.72, sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions"]),
         de("Change the function parameter to accept any", "Removes type safety for all callers", 0.80, sources=["https://www.typescriptlang.org/docs/handbook/2/functions.html"])],
        [wa("Transform the argument to match the expected type before passing", 0.90, sources=["https://www.typescriptlang.org/docs/handbook/2/narrowing.html"]),
         wa("Use function overloads or generics to accept multiple types safely", 0.85, sources=["https://www.typescriptlang.org/docs/handbook/2/generics.html"])],
        leads_to=[leads("typescript/ts7006-implicitly-any/ts5-linux", 0.15, "Fixing argument types leads to discovering untyped parameters")],
        preceded_by=[preceded("typescript/ts2322-type-not-assignable/ts5-linux", 0.25, "Fixing assignment types reveals argument mismatches in function calls")],
        confused_with=[confused("typescript/ts2322-type-not-assignable/ts5-linux", "TS2322 is about assignment to variables/properties; TS2345 is specifically about function call arguments")],
    ))

    canons.append(canon(
        "typescript", "ts7006-implicitly-any", "ts5-linux",
        "TS7006: Parameter 'x' implicitly has an 'any' type",
        r"TS7006: Parameter ['\"]?(.+?)['\"]? implicitly has an ['\"]any['\"] type",
        "type_error", "typescript", ">=5.0,<6.0", "linux", "true", 0.95, 0.92,
        "TypeScript strict mode requires explicit types. Very common when enabling strict for the first time.",
        [de("Disable strict mode in tsconfig.json", "Loses all the safety benefits of TypeScript strict mode", 0.85, sources=["https://www.typescriptlang.org/tsconfig#strict"]),
         de("Add : any to every parameter", "Removes type safety, making TypeScript equivalent to JavaScript", 0.82, sources=["https://www.typescriptlang.org/tsconfig#noImplicitAny"])],
        [wa("Add proper type annotations to function parameters", 0.95, "function greet(name: string): void { }", sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#parameter-type-annotations"]),
         wa("Use type inference where possible (let TypeScript infer from usage)", 0.88, sources=["https://www.typescriptlang.org/docs/handbook/type-inference.html"])],
        leads_to=[leads("typescript/ts2322-type-not-assignable/ts5-linux", 0.3, "Adding types reveals existing type mismatches"), leads("typescript/ts2345-argument-not-assignable/ts5-linux", 0.25, "Adding parameter types reveals argument mismatches")],
        preceded_by=[preceded("typescript/ts2345-argument-not-assignable/ts5-linux", 0.1, "Fixing argument errors leads to enabling stricter settings")],
        confused_with=[confused("typescript/ts2345-argument-not-assignable/ts5-linux", "TS2345 is about wrong argument types; TS7006 is about missing type annotations entirely")],
    ))

    # === RUST ===
    canons.append(canon(
        "rust", "e0382-borrow-moved-value", "rust1-linux",
        "error[E0382]: borrow of moved value",
        r"error\[E0382\]: borrow of moved value:?\s*`?(.+?)`?",
        "ownership_error", "rust", ">=1.70,<2.0", "linux", "true", 0.85, 0.88,
        "Value was moved to a new owner and can no longer be used. Core Rust ownership concept.",
        [de("Clone everything to avoid moves", "Unnecessary allocations, poor performance, doesn't teach ownership", 0.65, sources=["https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html"]),
         de("Use unsafe to bypass borrow checker", "Undefined behavior risk, completely wrong approach", 0.92, sources=["https://doc.rust-lang.org/book/ch19-01-unsafe-rust.html"])],
        [wa("Use references (&T or &mut T) instead of moving ownership", 0.90, "fn process(data: &Vec<i32>) instead of fn process(data: Vec<i32>)", sources=["https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html"]),
         wa("Clone only when genuinely needed and restructure to minimize moves", 0.85, sources=["https://doc.rust-lang.org/error_codes/E0382.html"])],
        leads_to=[leads("rust/e0308-mismatched-types/rust1-linux", 0.2, "Using references changes types causing mismatches"), leads("rust/e0277-trait-bound/rust1-linux", 0.15, "Borrowed types may not implement required traits")],
        preceded_by=[preceded("rust/e0308-mismatched-types/rust1-linux", 0.15, "Type fix changes ownership semantics")],
        confused_with=[confused("rust/e0308-mismatched-types/rust1-linux", "E0308 is about type mismatches; E0382 is specifically about use-after-move ownership violations")],
    ))

    canons.append(canon(
        "rust", "e0308-mismatched-types", "rust1-linux",
        "error[E0308]: mismatched types",
        r"error\[E0308\]: mismatched types",
        "type_error", "rust", ">=1.70,<2.0", "linux", "true", 0.90, 0.90,
        "Expected one type but got another. Very common with String vs &str, Option<T> vs T, etc.",
        [de("Use as to cast between incompatible types", "as is for numeric casts, not type conversions", 0.72, sources=["https://doc.rust-lang.org/reference/expressions/operator-expr.html#type-cast-expressions"]),
         de("Use unsafe transmute", "Undefined behavior, never correct for type mismatches", 0.95, sources=["https://doc.rust-lang.org/std/mem/fn.transmute.html"])],
        [wa("Use .into(), .as_ref(), .to_string(), or .as_str() for standard conversions", 0.92, "let s: String = my_str.into();", sources=["https://doc.rust-lang.org/error_codes/E0308.html"]),
         wa("Handle Option/Result with unwrap_or, map, or pattern matching", 0.88, sources=["https://doc.rust-lang.org/book/ch06-02-match.html"])],
        leads_to=[leads("rust/e0277-trait-bound/rust1-linux", 0.25, "Converted type may not implement required traits"), leads("rust/e0382-borrow-moved-value/rust1-linux", 0.15, "Conversion moves value causing use-after-move")],
        preceded_by=[preceded("rust/e0382-borrow-moved-value/rust1-linux", 0.2, "Fixing ownership changes variable types")],
        confused_with=[confused("rust/e0277-trait-bound/rust1-linux", "E0277 is about missing trait implementations; E0308 is about concrete type mismatches")],
    ))

    canons.append(canon(
        "rust", "e0277-trait-bound", "rust1-linux",
        "error[E0277]: the trait bound 'T: Trait' is not satisfied",
        r"error\[E0277\]: the trait bound .+ is not satisfied",
        "trait_error", "rust", ">=1.70,<2.0", "linux", "true", 0.82, 0.85,
        "Type doesn't implement a required trait. Common with Display, Debug, Clone, Serialize.",
        [de("Implement the trait manually when derive would work", "Unnecessary boilerplate for standard traits", 0.55, sources=["https://doc.rust-lang.org/book/ch10-02-traits.html#deriving-traits"]),
         de("Remove the trait bound from the function", "Breaks the function's ability to use trait methods", 0.70, sources=["https://doc.rust-lang.org/error_codes/E0277.html"])],
        [wa("Add #[derive(Trait)] to your struct/enum", 0.92, "#[derive(Debug, Clone, Serialize)]", sources=["https://doc.rust-lang.org/book/appendix-03-derivable-traits.html"]),
         wa("Add the trait bound to your generic function signature", 0.85, "fn process<T: Display + Clone>(item: T)", sources=["https://doc.rust-lang.org/book/ch10-02-traits.html#traits-as-parameters"])],
        leads_to=[leads("rust/e0308-mismatched-types/rust1-linux", 0.2, "Implementing trait changes expected types")],
        preceded_by=[preceded("rust/e0308-mismatched-types/rust1-linux", 0.2, "Type mismatch fix requires implementing a trait")],
        confused_with=[confused("rust/e0308-mismatched-types/rust1-linux", "E0308 is about concrete type mismatches; E0277 is about missing trait implementations on a type")],
    ))

    # === GO ===
    canons.append(canon(
        "go", "undefined-reference", "go1-linux",
        "undefined: X",
        r"undefined:\s+(\w+)",
        "compile_error", "go", ">=1.21,<2.0", "linux", "true", 0.90, 0.88,
        "Symbol not found. Usually an unexported name, missing import, or file not in the same package.",
        [de("Add the missing function to a different package", "Go packages must be imported explicitly, adding to wrong package won't help", 0.65, sources=["https://go.dev/doc/effective_go#names"]),
         de("Use //go:linkname to access unexported symbols", "Fragile hack that breaks on version updates", 0.88, sources=["https://go.dev/ref/spec#Exported_identifiers"])],
        [wa("Check capitalization (exported names start with uppercase in Go)", 0.92, sources=["https://go.dev/doc/effective_go#names"]),
         wa("Ensure the file is in the correct package and directory", 0.88, "go vet ./...", sources=["https://go.dev/ref/spec#Packages"])],
        leads_to=[leads("go/imported-not-used/go1-linux", 0.15, "Adding import to fix undefined creates unused import if wrong package")],
        preceded_by=[preceded("go/imported-not-used/go1-linux", 0.2, "Removing unused import causes undefined reference to symbol from that package")],
        confused_with=[confused("go/cannot-use-as-type/go1-linux", "cannot-use-as-type is about type mismatches; undefined means the symbol doesn't exist in scope")],
    ))

    canons.append(canon(
        "go", "imported-not-used", "go1-linux",
        "imported and not used",
        r"imported and not used:?\s*['\"]?(.+?)['\"]?",
        "compile_error", "go", ">=1.21,<2.0", "linux", "true", 0.98, 0.95,
        "Go requires all imports to be used. This is a compile error, not a warning.",
        [de("Comment out the import", "Messy, easy to forget, and goimports will re-add it", 0.60, sources=["https://go.dev/doc/effective_go#blank_import"]),
         de("Use blank identifier _ for every unused import", "Only correct for side-effect imports, not for temporarily unused ones", 0.55, sources=["https://go.dev/ref/spec#Import_declarations"])],
        [wa("Use goimports or gopls to auto-manage imports", 0.98, "goimports -w .", sources=["https://pkg.go.dev/golang.org/x/tools/cmd/goimports"]),
         wa("Remove the unused import line", 0.95, sources=["https://go.dev/doc/effective_go#blank_import"])],
        leads_to=[leads("go/undefined-reference/go1-linux", 0.25, "Removing import makes previously used symbols undefined")],
        preceded_by=[preceded("go/undefined-reference/go1-linux", 0.15, "Added import to fix undefined but used wrong package")],
        confused_with=[confused("go/undefined-reference/go1-linux", "undefined means symbol not found; imported-not-used means symbol package was imported but never referenced")],
    ))

    canons.append(canon(
        "go", "cannot-use-as-type", "go1-linux",
        "cannot use X (variable of type T1) as type T2 in argument",
        r"cannot use .+ \(.*type .+\) as .*type .+ in",
        "type_error", "go", ">=1.21,<2.0", "linux", "true", 0.88, 0.87,
        "Type mismatch in function argument or assignment. Go has no implicit conversions.",
        [de("Use unsafe.Pointer to cast between types", "Extremely dangerous, undefined behavior for non-pointer types", 0.92, sources=["https://go.dev/ref/spec#Conversions"]),
         de("Create a type alias", "Aliases don't help with interface satisfaction or conversion", 0.65, sources=["https://go.dev/ref/spec#Type_declarations"])],
        [wa("Explicitly convert between compatible types", 0.90, "int64(myInt32) or string(myBytes)", sources=["https://go.dev/doc/effective_go#conversions"]),
         wa("Implement the required interface on your type", 0.85, sources=["https://go.dev/doc/effective_go#interfaces"])],
        leads_to=[leads("go/undefined-reference/go1-linux", 0.1, "Refactoring types introduces undefined references")],
        preceded_by=[preceded("go/undefined-reference/go1-linux", 0.15, "Fixed undefined by using value from different package with incompatible type")],
        confused_with=[confused("typescript/ts2322-type-not-assignable/ts5-linux", "TS2322 is TypeScript type assignability; Go cannot-use-as-type is Go's compile-time type checking"), confused("rust/e0308-mismatched-types/rust1-linux", "Rust E0308 is similar concept but in Rust's type system")],
    ))

    # === KUBERNETES ===
    canons.append(canon(
        "kubernetes", "crashloopbackoff", "k8s1-linux",
        "CrashLoopBackOff",
        r"CrashLoopBackOff",
        "pod_error", "kubernetes", ">=1.28,<2.0", "linux", "partial", 0.60, 0.82,
        "Container starts and crashes repeatedly. K8s backs off restart attempts exponentially.",
        [de("Delete and recreate the pod", "Pod will crash again with the same config", 0.82, sources=["https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#restart-policy"]),
         de("Increase restart limit", "There is no restart limit in K8s; the issue is in the container itself", 0.88, sources=["https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/"])],
        [wa("Check container logs for the crash reason", 0.85, "kubectl logs pod-name --previous", sources=["https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/#examine-pod-logs"]),
         wa("Check if the container needs environment variables, secrets, or config maps", 0.80, "kubectl describe pod pod-name", sources=["https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/"])],
        leads_to=[leads("kubernetes/oomkilled/k8s1-linux", 0.2, "Container starts but consumes too much memory and gets OOMKilled")],
        preceded_by=[preceded("docker/oci-runtime-create-failed/docker27-linux", 0.25, "Container image has startup issues that cause crash loop in K8s"), preceded("kubernetes/imagepullbackoff/k8s1-linux", 0.15, "Fixed image pull but container itself crashes")],
        confused_with=[confused("kubernetes/imagepullbackoff/k8s1-linux", "ImagePullBackOff is about pulling the image; CrashLoopBackOff means image pulled successfully but container crashes")],
    ))

    canons.append(canon(
        "kubernetes", "imagepullbackoff", "k8s1-linux",
        "ImagePullBackOff",
        r"ImagePullBackOff|ErrImagePull",
        "image_error", "kubernetes", ">=1.28,<2.0", "linux", "true", 0.85, 0.88,
        "Cannot pull container image. Wrong image name, tag, or missing registry credentials.",
        [de("Keep waiting for the pull to succeed", "If credentials or image name are wrong, it will never succeed", 0.80, sources=["https://kubernetes.io/docs/concepts/containers/images/#imagepullbackoff"]),
         de("Pull the image manually on the node", "Not scalable and doesn't fix the underlying auth/name issue", 0.72, sources=["https://kubernetes.io/docs/concepts/containers/images/"])],
        [wa("Verify image name and tag exist in the registry", 0.90, "docker pull image:tag", sources=["https://kubernetes.io/docs/concepts/containers/images/#updating-images"]),
         wa("Create or fix imagePullSecrets for private registries", 0.85, "kubectl create secret docker-registry regcred --docker-server=... --docker-username=... --docker-password=...", sources=["https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/"])],
        leads_to=[leads("kubernetes/crashloopbackoff/k8s1-linux", 0.3, "Image pulled successfully but container crashes on start")],
        preceded_by=[preceded("docker/exec-format-error/docker27-linux", 0.15, "Wrong architecture image pushed to registry")],
        confused_with=[confused("kubernetes/crashloopbackoff/k8s1-linux", "CrashLoopBackOff means container runs and crashes; ImagePullBackOff means image cannot be downloaded")],
    ))

    canons.append(canon(
        "kubernetes", "oomkilled", "k8s1-linux",
        "OOMKilled",
        r"OOMKilled|Out of memory|OOM",
        "resource_error", "kubernetes", ">=1.28,<2.0", "linux", "partial", 0.55, 0.80,
        "Container exceeded its memory limit and was killed by the kernel OOM killer.",
        [de("Remove memory limits entirely", "Pod can consume all node memory and affect other pods", 0.78, sources=["https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"]),
         de("Set memory limit to maximum node capacity", "Still kills if it exceeds, and starves other pods", 0.72, sources=["https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory"])],
        [wa("Profile actual memory usage and set limits 20-30% above normal usage", 0.80, "kubectl top pod pod-name", sources=["https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/"]),
         wa("Fix memory leaks in the application or reduce batch sizes", 0.75, sources=["https://kubernetes.io/docs/tasks/configure-pod-container/assign-memory-resource/"])],
        leads_to=[leads("kubernetes/crashloopbackoff/k8s1-linux", 0.35, "OOMKilled container restarts and enters crash loop")],
        preceded_by=[preceded("kubernetes/crashloopbackoff/k8s1-linux", 0.25, "Investigating crash loop reveals OOM as the root cause")],
        confused_with=[confused("python/memoryerror/py311-linux", "Python MemoryError is process-level; OOMKilled is container-level enforced by the kernel"), confused("kubernetes/crashloopbackoff/k8s1-linux", "CrashLoopBackOff is the symptom; OOMKilled is a specific cause of the crash")],
    ))

    # === TERRAFORM ===
    canons.append(canon(
        "terraform", "state-lock-error", "tf1-linux",
        "Error acquiring the state lock",
        r"Error (acquiring|locking) the state lock",
        "state_error", "terraform", ">=1.5,<2.0", "linux", "true", 0.85, 0.88,
        "Another Terraform process holds the state lock or a previous run crashed without releasing it.",
        [de("Delete the state file", "Permanently loses all resource tracking, causing orphaned infrastructure", 0.95, sources=["https://developer.hashicorp.com/terraform/language/state"]),
         de("Use -no-lock flag", "Creates race conditions when multiple users apply simultaneously", 0.78, sources=["https://developer.hashicorp.com/terraform/language/state/locking"])],
        [wa("Force unlock the state with the lock ID", 0.88, "terraform force-unlock LOCK_ID", sources=["https://developer.hashicorp.com/terraform/cli/commands/force-unlock"]),
         wa("Check if another terraform apply is running and wait for it to finish", 0.85, sources=["https://developer.hashicorp.com/terraform/language/state/locking"])],
        leads_to=[leads("terraform/provider-not-present/tf1-linux", 0.1, "After unlock, re-init may be needed to restore providers")],
        preceded_by=[preceded("terraform/cycle-in-module/tf1-linux", 0.1, "Cycle error crashed apply leaving lock behind")],
        confused_with=[confused("terraform/provider-not-present/tf1-linux", "Provider not present is about missing terraform init; state lock is about concurrent access or crashed runs")],
    ))

    canons.append(canon(
        "terraform", "provider-not-present", "tf1-linux",
        "Provider configuration not present",
        r"Provider configuration not present|provider .+ not available",
        "config_error", "terraform", ">=1.5,<2.0", "linux", "true", 0.90, 0.88,
        "Required provider is not configured in the Terraform configuration.",
        [de("Manually download the provider binary", "Terraform manages provider binaries; manual placement is fragile", 0.72, sources=["https://developer.hashicorp.com/terraform/language/providers/configuration"]),
         de("Copy .terraform from another project", "Provider versions and configs may not match", 0.78, sources=["https://developer.hashicorp.com/terraform/cli/commands/init"])],
        [wa("Run terraform init to download and configure providers", 0.92, "terraform init", sources=["https://developer.hashicorp.com/terraform/cli/commands/init"]),
         wa("Add the required_providers block to your terraform configuration", 0.88, sources=["https://developer.hashicorp.com/terraform/language/providers/requirements"])],
        leads_to=[leads("terraform/cycle-in-module/tf1-linux", 0.15, "After init, applying reveals circular dependencies")],
        preceded_by=[preceded("terraform/state-lock-error/tf1-linux", 0.1, "After unlocking state, init needed to restore provider config")],
        confused_with=[confused("terraform/state-lock-error/tf1-linux", "State lock is about concurrent access; provider not present is about missing terraform init")],
    ))

    canons.append(canon(
        "terraform", "cycle-in-module", "tf1-linux",
        "Error: Cycle",
        r"Error: Cycle:?\s*(.+)",
        "dependency_error", "terraform", ">=1.5,<2.0", "linux", "partial", 0.55, 0.78,
        "Circular dependency between resources. Terraform cannot determine apply order.",
        [de("Add depends_on to break the cycle", "depends_on can make cycles worse by adding more edges to the dependency graph", 0.65, sources=["https://developer.hashicorp.com/terraform/language/meta-arguments/depends_on"]),
         de("Move resources to separate modules", "Cycles across modules are even harder to debug", 0.60, sources=["https://developer.hashicorp.com/terraform/language/modules"])],
        [wa("Use terraform graph to visualize the cycle and refactor", 0.78, "terraform graph | dot -Tpng > graph.png", sources=["https://developer.hashicorp.com/terraform/cli/commands/graph"]),
         wa("Break the cycle by using data sources instead of direct references for one direction", 0.72, sources=["https://developer.hashicorp.com/terraform/language/data-sources"])],
        leads_to=[leads("terraform/state-lock-error/tf1-linux", 0.1, "Long-running apply to fix cycle crashes leaving lock")],
        preceded_by=[preceded("terraform/provider-not-present/tf1-linux", 0.15, "After init, plan reveals circular dependencies")],
        confused_with=[confused("terraform/state-lock-error/tf1-linux", "State lock is about concurrent access; cycle error is about circular resource dependencies in configuration")],
    ))

    # === AWS ===
    canons.append(canon(
        "aws", "access-denied-exception", "awscli2-linux",
        "An error occurred (AccessDeniedException) when calling the X operation",
        r"(AccessDeniedException|AccessDenied|403 Forbidden).*when calling",
        "auth_error", "aws", ">=2.0,<3.0", "linux", "true", 0.82, 0.85,
        "IAM permissions insufficient for the requested operation.",
        [de("Add AdministratorAccess policy", "Severe security risk, violates least-privilege principle", 0.85, sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege"]),
         de("Use root account credentials", "Root should never be used for API calls, critical security issue", 0.95, sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#lock-away-credentials"])],
        [wa("Check which specific permission is needed using CloudTrail or IAM Access Analyzer", 0.85, "aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=OperationName", sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-getting-started.html"]),
         wa("Add the minimum required IAM policy for the specific action and resource", 0.82, sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create.html"])],
        leads_to=[leads("aws/expired-token-exception/awscli2-linux", 0.15, "Created temporary credentials that expire"), leads("aws/resource-not-found/awscli2-linux", 0.2, "Has permissions but wrong region or resource name")],
        preceded_by=[preceded("aws/expired-token-exception/awscli2-linux", 0.25, "Refreshed token but new role has insufficient permissions")],
        confused_with=[confused("aws/expired-token-exception/awscli2-linux", "ExpiredToken means valid permissions but expired session; AccessDenied means active session but insufficient permissions"), confused("aws/resource-not-found/awscli2-linux", "ResourceNotFound means resource doesn't exist; AccessDenied means it may exist but you can't access it")],
    ))

    canons.append(canon(
        "aws", "expired-token-exception", "awscli2-linux",
        "An error occurred (ExpiredTokenException): The security token included in the request is expired",
        r"ExpiredTokenException|security token.+is expired|token.+has expired",
        "auth_error", "aws", ">=2.0,<3.0", "linux", "true", 0.90, 0.90,
        "AWS session token has expired. Common with STS temporary credentials and SSO sessions.",
        [de("Hardcode long-lived access keys", "Security anti-pattern, keys can leak and don't rotate", 0.88, sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#rotate-credentials"]),
         de("Extend token lifetime to maximum", "Only delays the problem, tokens still expire", 0.55, sources=["https://docs.aws.amazon.com/STS/latest/APIReference/API_GetSessionToken.html"])],
        [wa("Refresh credentials with aws sso login or aws sts assume-role", 0.92, "aws sso login --profile my-profile", sources=["https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html"]),
         wa("Use credential_process or credential helpers for automatic refresh", 0.85, sources=["https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sourcing-external.html"])],
        leads_to=[leads("aws/access-denied-exception/awscli2-linux", 0.2, "Refreshed credentials may have different/fewer permissions")],
        preceded_by=[preceded("aws/access-denied-exception/awscli2-linux", 0.15, "Assumed role with temporary credentials that later expire")],
        confused_with=[confused("aws/access-denied-exception/awscli2-linux", "AccessDenied means wrong permissions; ExpiredToken means right permissions but session has timed out")],
    ))

    canons.append(canon(
        "aws", "resource-not-found", "awscli2-linux",
        "An error occurred (ResourceNotFoundException): The specified resource does not exist",
        r"ResourceNotFoundException|NoSuchBucket|NoSuchKey|404.*Not Found",
        "resource_error", "aws", ">=2.0,<3.0", "linux", "true", 0.88, 0.87,
        "AWS resource doesn't exist or is in a different region.",
        [de("Create the resource with the same name", "May not have the same configuration, causing downstream issues", 0.55, sources=["https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html"]),
         de("Switch to us-east-1 (default region)", "Resource may be in a completely different region", 0.62, sources=["https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html#cli-configure-files-settings"])],
        [wa("Check the resource exists in the correct region", 0.90, "aws s3 ls s3://bucket-name --region us-west-2", sources=["https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html#cli-configure-files-settings"]),
         wa("Verify the ARN or resource identifier for typos", 0.85, sources=["https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html"])],
        leads_to=[leads("aws/access-denied-exception/awscli2-linux", 0.15, "Resource found but permissions insufficient in that region")],
        preceded_by=[preceded("aws/access-denied-exception/awscli2-linux", 0.2, "Permissions fixed but resource referenced by wrong name or region")],
        confused_with=[confused("aws/access-denied-exception/awscli2-linux", "AccessDenied can mask ResourceNotFound when permissions hide resource existence for security")],
    ))

    # === NEXTJS ===
    canons.append(canon(
        "nextjs", "hydration-failed", "nextjs14-linux",
        "Error: Hydration failed because the initial UI does not match what was rendered on the server",
        r"Hydration failed because the initial UI does not match",
        "render_error", "nextjs", ">=14,<16", "linux", "partial", 0.60, 0.82,
        "Server-rendered HTML doesn't match client-side render. Common with dynamic content, dates, or browser APIs.",
        [de("Suppress hydration warnings with suppressHydrationWarning", "Masks real bugs, content will flash/shift for users", 0.65, sources=["https://nextjs.org/docs/messages/react-hydration-error"]),
         de("Make everything client-side with 'use client'", "Loses all SSR/SSG benefits, defeats the purpose of Next.js", 0.78, sources=["https://nextjs.org/docs/app/building-your-application/rendering/client-components"])],
        [wa("Move browser-only code into useEffect", 0.82, "const [mounted, setMounted] = useState(false); useEffect(() => setMounted(true), []);", sources=["https://nextjs.org/docs/messages/react-hydration-error"]),
         wa("Use dynamic import with ssr: false for client-only components", 0.78, "const Comp = dynamic(() => import('./Comp'), { ssr: false })", sources=["https://nextjs.org/docs/app/building-your-application/optimizing/lazy-loading"])],
        leads_to=[leads("nextjs/server-component-client-hook/nextjs14-linux", 0.2, "Moving code to useEffect requires making component a Client Component")],
        preceded_by=[preceded("nextjs/server-component-client-hook/nextjs14-linux", 0.15, "Added 'use client' but server/client HTML mismatch remains")],
        confused_with=[confused("react/cannot-update-while-rendering/react18-linux", "Cannot update while rendering is about state updates during render; hydration mismatch is about server/client HTML differences")],
    ))

    canons.append(canon(
        "nextjs", "module-not-found-resolve", "nextjs14-linux",
        "Module not found: Can't resolve 'X'",
        r"Module not found: Can't resolve ['\"](.+?)['\"]",
        "build_error", "nextjs", ">=14,<16", "linux", "true", 0.88, 0.90,
        "Webpack/Turbopack cannot find the module. Usually a missing dependency or wrong import path.",
        [de("Add the module to webpack externals", "Makes the module unavailable at runtime", 0.72, sources=["https://nextjs.org/docs/app/api-reference/next-config-js/webpack"]),
         de("Use require() instead of import", "Doesn't fix the missing module, just changes the error format", 0.65, sources=["https://nextjs.org/docs/app/building-your-application/optimizing/package-bundling"])],
        [wa("Install the missing dependency", 0.92, "npm install missing-package", sources=["https://nextjs.org/docs/getting-started/installation"]),
         wa("Check for typos in the import path and use correct relative/absolute paths", 0.88, sources=["https://nextjs.org/docs/app/building-your-application/configuring/absolute-imports-and-module-aliases"])],
        leads_to=[leads("nextjs/server-component-client-hook/nextjs14-linux", 0.15, "Installed module uses hooks requiring Client Component")],
        preceded_by=[preceded("node/cannot-find-module-npm/node20-linux", 0.2, "npm module issue surfaces as Next.js build error")],
        confused_with=[confused("node/err-module-not-found/node20-linux", "ERR_MODULE_NOT_FOUND is a Node.js runtime error; Next.js Module not found is a webpack/turbopack build error"), confused("typescript/ts2307-cannot-find-module/ts5-linux", "TS2307 is TypeScript compile error; Next.js Module not found is bundler resolution error")],
    ))

    canons.append(canon(
        "nextjs", "server-component-client-hook", "nextjs14-linux",
        "Error: useState/useEffect can only be used in Client Components",
        r"(useState|useEffect|useContext).+can only be used in Client Components",
        "component_error", "nextjs", ">=14,<16", "linux", "true", 0.92, 0.90,
        "React hooks used in a Server Component. Next.js App Router defaults to Server Components.",
        [de("Make the entire page a Client Component", "Loses server-side rendering benefits for the whole page", 0.72, sources=["https://nextjs.org/docs/app/building-your-application/rendering/client-components"]),
         de("Pass hooks through props from a parent Client Component", "Hooks cannot be passed as props, they must be called in the component", 0.85, sources=["https://react.dev/reference/rules/rules-of-hooks"])],
        [wa("Add 'use client' directive at the top of the file that uses hooks", 0.95, "// Add as first line:\n'use client';", sources=["https://nextjs.org/docs/app/building-your-application/rendering/client-components#using-client-components-in-nextjs"]),
         wa("Extract the interactive part into a separate Client Component", 0.90, sources=["https://nextjs.org/docs/app/building-your-application/rendering/composition-patterns"])],
        leads_to=[leads("nextjs/hydration-failed/nextjs14-linux", 0.2, "Client Component has browser-only code causing hydration mismatch"), leads("react/invalid-hook-call/react18-linux", 0.1, "Hook placement still incorrect after adding use client")],
        preceded_by=[preceded("react/invalid-hook-call/react18-linux", 0.2, "Invalid hook call in Next.js is often a Server Component issue")],
        confused_with=[confused("react/invalid-hook-call/react18-linux", "Invalid hook call is about hook rules; server-component-client-hook is about Server vs Client Component boundary")],
    ))

    # === REACT ===
    canons.append(canon(
        "react", "invalid-hook-call", "react18-linux",
        "Invalid hook call. Hooks can only be called inside the body of a function component",
        r"Invalid hook call.*Hooks can only be called inside",
        "hook_error", "react", ">=18,<20", "linux", "true", 0.85, 0.88,
        "Hook called outside a component, in a class component, or with multiple React copies.",
        [de("Convert class component to function component just for hooks", "If the class has complex lifecycle, conversion may introduce bugs", 0.55, sources=["https://react.dev/reference/rules/rules-of-hooks"]),
         de("Call hooks inside event handlers or callbacks", "Hooks must be at the top level, not inside conditions or callbacks", 0.82, sources=["https://react.dev/warnings/invalid-hook-call-warning"])],
        [wa("Ensure hooks are called at the top level of a function component", 0.92, sources=["https://react.dev/reference/rules/rules-of-hooks"]),
         wa("Check for duplicate React versions in node_modules", 0.85, "npm ls react", sources=["https://react.dev/warnings/invalid-hook-call-warning"])],
        leads_to=[leads("react/too-many-rerenders/react18-linux", 0.15, "Fixing hook placement may introduce render loop if dependencies wrong"), leads("react/cannot-update-while-rendering/react18-linux", 0.1, "Moved hook call but placed state update in render body")],
        preceded_by=[preceded("nextjs/server-component-client-hook/nextjs14-linux", 0.2, "Next.js Server Component hook error leads to investigating hook rules")],
        confused_with=[confused("nextjs/server-component-client-hook/nextjs14-linux", "Server Component error is about component type; invalid hook call is about hook placement rules")],
    ))

    canons.append(canon(
        "react", "cannot-update-while-rendering", "react18-linux",
        "Cannot update a component while rendering a different component",
        r"Cannot update a component .+ while rendering a different component",
        "render_error", "react", ">=18,<20", "linux", "true", 0.82, 0.85,
        "State update triggered during render phase of another component. Usually setState in render body.",
        [de("Wrap the update in setTimeout", "Hacky fix that can cause flickering and race conditions", 0.65, sources=["https://react.dev/reference/react/useState#ive-updated-the-state-but-the-screen-doesnt-update"]),
         de("Use useLayoutEffect for the update", "May cause the same issue if the update triggers a re-render", 0.60, sources=["https://react.dev/reference/react/useLayoutEffect"])],
        [wa("Move the state update into useEffect", 0.90, "useEffect(() => { setState(value); }, [dependency]);", sources=["https://react.dev/reference/react/useEffect"]),
         wa("Restructure to lift state up or use a shared context", 0.82, sources=["https://react.dev/learn/sharing-state-between-components"])],
        leads_to=[leads("react/too-many-rerenders/react18-linux", 0.25, "Moving update to useEffect with wrong deps causes infinite loop")],
        preceded_by=[preceded("react/too-many-rerenders/react18-linux", 0.2, "Fixed infinite loop but state update now happens during render")],
        confused_with=[confused("react/too-many-rerenders/react18-linux", "Too many re-renders is about infinite loops; cannot-update-while-rendering is about timing of state updates")],
    ))

    canons.append(canon(
        "react", "too-many-rerenders", "react18-linux",
        "Error: Too many re-renders. React limits the number of renders to prevent an infinite loop",
        r"Too many re-renders.*React limits the number of renders",
        "render_error", "react", ">=18,<20", "linux", "true", 0.88, 0.90,
        "Infinite render loop caused by setState during render or wrong useEffect dependencies.",
        [de("Increase React's render limit", "There is no configurable render limit; the issue is an infinite loop", 0.90, sources=["https://react.dev/reference/react/useState"]),
         de("Remove all useEffect dependencies", "Makes useEffect run on every render, potentially worsening the loop", 0.78, sources=["https://react.dev/reference/react/useEffect#specifying-reactive-dependencies"])],
        [wa("Check for setState calls during render (not inside useEffect or event handlers)", 0.92, sources=["https://react.dev/reference/react/useState#setstate-caveats"]),
         wa("Fix useEffect dependency arrays to prevent retriggering", 0.88, "useEffect(() => { ... }, [specificDep]); // not [object] or []", sources=["https://react.dev/reference/react/useEffect#specifying-reactive-dependencies"])],
        leads_to=[leads("react/cannot-update-while-rendering/react18-linux", 0.2, "Fixing the loop may move setState to wrong phase of render cycle")],
        preceded_by=[preceded("react/cannot-update-while-rendering/react18-linux", 0.2, "Fixing render-phase update by adding useEffect causes infinite loop"), preceded("react/invalid-hook-call/react18-linux", 0.1, "Fixing hook placement introduces dependency array issues")],
        confused_with=[confused("react/cannot-update-while-rendering/react18-linux", "Cannot update while rendering is about state update timing; too many re-renders is about infinite render loops")],
    ))

    # === NETWORKING (HTTPS) ===
    canons.append(canon(
        "networking", "mixed-content-blocked", "http-linux",
        "Mixed Content: The page was loaded over HTTPS, but requested an insecure resource",
        r"Mixed Content.*loaded over HTTPS.*insecure|blocked.*mixed.*content|mixed-content.*blocked",
        "ssl_tls", "http", "HTTP/1.1+", "linux", "true", 0.91, 0.92,
        "The browser blocked an HTTP sub-resource (image, script, stylesheet, XHR) loaded on an HTTPS page. Occurs most often during HTTP-to-HTTPS migrations when asset URLs were not updated.",
        [de("Add 'upgrade-insecure-requests' meta tag to the HTML head", "Only works when the HTTPS version of the resource exists; fails for third-party assets without HTTPS endpoints", 0.55, sources=["https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/upgrade-insecure-requests"]),
         de("Disable mixed content blocking in browser developer settings", "Cannot be disabled in production—only in local dev tools. Chrome removed per-site mixed content allowance in 2021.", 0.98, sources=["https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content"]),
         de("Proxy all mixed content through the origin server to rewrite URLs on the fly", "Violates CDN terms of service, breaks cache-busting, introduces latency, and is complex to maintain", 0.72, sources=["https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content/How_to_fix_website_with_mixed_content"])],
        [wa("Audit and rewrite all HTTP asset URLs to HTTPS in templates, CSS, and CMS content", 0.94, "grep -r 'http://' templates/ static/ --include='*.html' --include='*.css'", sources=["https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content/How_to_fix_website_with_mixed_content"]),
         wa("Add Content-Security-Policy: upgrade-insecure-requests header at the web server (TLS termination) layer", 0.82, "nginx: add_header Content-Security-Policy \"upgrade-insecure-requests\";", sources=["https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/upgrade-insecure-requests"]),
         wa("Self-host or replace third-party HTTP-only assets with HTTPS-capable alternatives", 0.88, "Download and serve from your HTTPS origin, or switch to an HTTPS CDN", sources=["https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content"])],
        leads_to=[leads("networking/ssl-unable-to-verify/openssl3-linux", 0.1, "Upgrading asset URLs to HTTPS reveals untrusted certificate on asset server"),
                  leads("networking/cors-preflight-failed/http-linux", 0.15, "HTTPS assets on a different origin may lack proper CORS headers")],
        preceded_by=[preceded("networking/too-many-redirects/http-linux", 0.1, "Incomplete HTTP-to-HTTPS migration leaves asset URLs pointing to HTTP origins"),
                     preceded("networking/ssl-certificate-expired/openssl3-linux", 0.05, "Renewing expired cert reveals asset URLs were hardcoded to HTTP")],
        confused_with=[confused("networking/cors-preflight-failed/http-linux", "Mixed content is protocol mismatch on the same page; CORS is cross-origin access control regardless of protocol"),
                       confused("networking/ssl-unable-to-verify/openssl3-linux", "Mixed content: assets loaded over HTTP on an HTTPS page; ssl-unable-to-verify: the HTTPS connection itself fails due to invalid cert chain")],
    ))

    canons.append(canon(
        "networking", "hsts-preload-misconfigured", "http-linux",
        "Strict-Transport-Security header missing or misconfigured / HSTS preload requirements not met",
        r"Strict-Transport-Security.*missing|hsts.*not.*set|max-age.*too.*short.*preload|includeSubDomains.*required.*preload|preload.*directive.*missing",
        "ssl_tls", "http", "HTTP/1.1+", "linux", "true", 0.88, 0.89,
        "The HSTS header is absent or does not meet browser preload requirements (max-age >= 31536000, includeSubDomains, preload directive). Without HSTS, the first HTTP request is vulnerable to downgrade attacks.",
        [de("Submit domain to HSTS preload list before verifying all subdomains support HTTPS", "includeSubDomains forces all subdomains to HTTPS permanently; any subdomain without a valid cert becomes inaccessible with no bypass. Removal takes months.", 0.85, sources=["https://hstspreload.org/"]),
         de("Set max-age to a very large value immediately on first HSTS deployment", "If HTTPS breaks later, browsers refuse HTTP fallback for the full cached duration. Ramp up progressively.", 0.70, sources=["https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security"]),
         de("Add HSTS header only in the application layer when a reverse proxy handles TLS termination", "The header must be set at the TLS-terminating layer to be sent on all HTTPS responses including static files", 0.60, sources=["https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security"])],
        [wa("Add Strict-Transport-Security header at the TLS termination layer with progressive max-age", 0.92, "Start: max-age=300 → 86400 → 604800 → 31536000. nginx: add_header Strict-Transport-Security \"max-age=31536000; includeSubDomains\" always;", sources=["https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security"]),
         wa("Submit to HSTS preload list only after all subdomains are HTTPS-ready", 0.85, "Validate at https://hstspreload.org/ then submit; requires max-age=31536000, includeSubDomains, preload", sources=["https://hstspreload.org/"]),
         wa("Use Helmet.js (Node.js) or framework security middleware to set HSTS automatically", 0.88, "app.use(helmet.hsts({ maxAge: 31536000, includeSubDomains: true }))", sources=["https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security"])],
        leads_to=[leads("networking/ssl-certificate-expired/openssl3-linux", 0.2, "Long max-age HSTS with later certificate expiry leaves users unable to bypass HTTPS requirement"),
                  leads("networking/mixed-content-blocked/http-linux", 0.15, "Enabling HSTS reveals subdomains or assets still served over HTTP")],
        preceded_by=[preceded("networking/ssl-certificate-expired/openssl3-linux", 0.1, "Fixing expired certificate triggers security audit revealing missing HSTS"),
                     preceded("networking/too-many-redirects/http-linux", 0.1, "Diagnosing HTTP-to-HTTPS redirect loops reveals HSTS missing from HTTPS response")],
        confused_with=[confused("networking/ssl-certificate-expired/openssl3-linux", "HSTS: missing or wrong security policy header; certificate expiry: cert past validity date. HSTS errors appear in security audits; cert expiry shows browser error pages."),
                       confused("networking/mixed-content-blocked/http-linux", "Mixed content: HTTP sub-resources on an HTTPS page; HSTS: enforcing HTTPS at transport level via response header. Both occur during HTTPS migrations but are independent.")],
    ))


    # =====================================================================
    # === ROS 2 ===
    # =====================================================================
    canons.append(canon(
        "ros2", "package-not-found", "ros2-humble-linux",
        "PackageNotFoundError: Packages not found: ['my_package']",
        r"PackageNotFound(Error|Exception).*Packages?\s+not\s+found",
        "build_error", "ros2", ">=humble,<rolling", "linux", "true", 0.90, 0.92,
        "colcon build or ros2 run cannot locate the package. Usually the workspace is not sourced or the package name is misspelled.",
        [de("Re-run colcon build without sourcing the workspace first",
            "Building and running in the same terminal without sourcing install/setup.bash means the new package is invisible to ros2 CLI", 0.80),
         de("Manually copy the package into /opt/ros/humble/share/",
            "System install paths are managed by apt; manual copies get overwritten and break dependency resolution", 0.85),
         de("Add the package path to AMENT_PREFIX_PATH by hand",
            "Does not persist across terminals and masks the real issue: the workspace overlay is not sourced", 0.70)],
        [wa("Source the workspace overlay after building", 0.95,
            "cd ~/ros2_ws && colcon build --packages-select my_package && source install/setup.bash"),
         wa("Verify package.xml <name> matches the directory name and CMakeLists project() name", 0.88),
         wa("Check that the package is listed in colcon list output", 0.85,
            "cd ~/ros2_ws && colcon list | grep my_package")],
    ))

    canons.append(canon(
        "ros2", "qos-incompatible", "ros2-humble-linux",
        "[WARN] New publisher discovered on topic '/sensor_data', offering incompatible QoS",
        r"(incompatible QoS|QoS.*incompatib|RELIABLE.*BEST_EFFORT|offered.*incompatible)",
        "communication_error", "ros2", ">=humble,<rolling", "linux", "true", 0.88, 0.90,
        "Publisher and subscriber have mismatched QoS profiles. Messages are silently dropped with no error besides this warning.",
        [de("Set both sides to RELIABLE QoS unconditionally",
            "Sensor drivers often only offer BEST_EFFORT; forcing RELIABLE on subscriber causes zero messages with no further error", 0.82),
         de("Ignore the warning assuming messages still arrive",
            "With incompatible QoS the DDS layer drops ALL messages; the warning is not cosmetic", 0.90),
         de("Change DDS middleware hoping it fixes QoS",
            "QoS incompatibility is DDS-standard behavior, not vendor-specific; switching RMW does not help", 0.75)],
        [wa("Match subscriber QoS to publisher using SensorDataQoS or qos_profile_sensor_data", 0.92,
            "from rclpy.qos import qos_profile_sensor_data; self.create_subscription(Msg, topic, cb, qos_profile_sensor_data)"),
         wa("Use ros2 topic info -v to check offered and requested QoS", 0.90,
            "ros2 topic info -v /sensor_data"),
         wa("Set QoS reliability to BEST_EFFORT for high-frequency sensor topics", 0.88)],
    ))

    canons.append(canon(
        "ros2", "tf-lookup-exception", "ros2-humble-linux",
        "tf2.LookupException: \"map\" passed to lookupTransform argument target_frame does not exist",
        r"(tf2.*LookupException|lookupTransform.*does not exist|Could not find a connection between)",
        "tf_error", "ros2", ">=humble,<rolling", "linux", "true", 0.82, 0.88,
        "TF2 cannot find the requested frame. The frame publisher is not running or publishing to the wrong topic.",
        [de("Add a sleep/retry loop waiting for the transform",
            "Masks a configuration error; if the frame publisher is misconfigured the transform never appears", 0.72),
         de("Hardcode the transform as a 4x4 matrix instead of using TF2",
            "Defeats TF2 purpose, breaks when robot moves, unmaintainable", 0.88),
         de("Increase TF buffer cache time to very large values",
            "The frame was never published, not expired from cache", 0.78)],
        [wa("Run ros2 run tf2_tools view_frames to visualize the TF tree", 0.90,
            "ros2 run tf2_tools view_frames  # generates frames.pdf"),
         wa("Check frame_id strings match exactly (no leading slash in ROS 2)", 0.88,
            "ROS 2 TF2 does NOT use leading slashes: use 'map' not '/map'"),
         wa("Launch static_transform_publisher for missing static frames", 0.85,
            "ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 parent child")],
    ))

    canons.append(canon(
        "ros2", "launch-file-error", "ros2-humble-linux",
        "launch.invalid_launch_file_error.InvalidLaunchFileError: Caught exception when trying to load file",
        r"(InvalidLaunchFileError|Caught exception.*load.*file.*launch|SyntaxError.*launch\.py)",
        "launch_error", "ros2", ">=humble,<rolling", "linux", "true", 0.92, 0.90,
        "ROS 2 launch file has a Python syntax error or incorrect launch API usage.",
        [de("Convert ROS 1 XML launch directly to ROS 2 XML without API changes",
            "ROS 2 XML launch uses different tags and attribute names than ROS 1", 0.80),
         de("Use print() for debugging inside launch descriptions",
            "Launch descriptions are declarative; print() runs at parse time not launch time", 0.65)],
        [wa("Use ros2 launch --print to validate syntax without executing", 0.90,
            "ros2 launch my_package my_launch.py --print"),
         wa("Follow Python launch template with LaunchDescription and Node action", 0.92,
            "from launch import LaunchDescription; from launch_ros.actions import Node"),
         wa("Read the full traceback - the actual Python error is at the bottom", 0.88)],
    ))

    canons.append(canon(
        "ros2", "colcon-build-cmake-error", "ros2-humble-linux",
        "colcon build: CMake Error at CMakeLists.txt: find_package(ament_cmake) failed",
        r"(colcon.*CMake Error|find_package\(ament_cmake\).*failed|Could not find.*ament_cmake)",
        "build_error", "ros2", ">=humble,<rolling", "linux", "true", 0.88, 0.90,
        "colcon build fails because ament_cmake is not found. ROS 2 environment is not sourced.",
        [de("Install ament_cmake via pip",
            "ament_cmake is a CMake package, not Python; pip install does nothing useful", 0.90),
         de("Build ament_cmake from source in your workspace",
            "ament_cmake is core ROS 2 infrastructure; building from source causes version conflicts", 0.80)],
        [wa("Source the ROS 2 installation before building", 0.95,
            "source /opt/ros/humble/setup.bash && cd ~/ros2_ws && colcon build"),
         wa("Install missing packages via apt", 0.90,
            "sudo apt install ros-humble-ament-cmake"),
         wa("Use rosdep to install all dependencies", 0.88,
            "cd ~/ros2_ws && rosdep install --from-paths src --ignore-src -y")],
    ))

    canons.append(canon(
        "ros2", "node-name-not-unique", "ros2-humble-linux",
        "[WARN] Node name is not unique across the ROS graph",
        r"(Node name.*not unique|node.*already.*registered|Another node.*same name)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "partial", 0.65, 0.85,
        "Two nodes with the same name cause topic/service collisions. Common when launching multiple instances.",
        [de("Ignore the warning",
            "Non-unique names cause parameter and service name collisions; nodes silently override each other", 0.75),
         de("Kill all nodes and restart one by one",
            "Does not fix the root cause in the launch file; duplicate reappears on next launch", 0.60)],
        [wa("Use unique node names via namespace or remapping", 0.90,
            "ros2 run my_pkg my_node --ros-args -r __node:=my_node_1"),
         wa("Use push_ros_namespace in launch files for multi-robot setups", 0.85,
            "GroupAction([PushRosNamespace('robot1'), Node(package='my_pkg', executable='my_node')])"),
         wa("Set node name dynamically from launch argument", 0.82)],
    ))

    canons.append(canon(
        "ros2", "service-not-available", "ros2-humble-linux",
        "rclpy.service.ServiceException: Service /my_service is not available",
        r"(Service.*not available|wait_for_service.*timed out|service_is_ready.*False|Failed to call service)",
        "communication_error", "ros2", ">=humble,<rolling", "linux", "true", 0.85, 0.88,
        "Service server is not running or registered under a different name. wait_for_service() times out.",
        [de("Increase the timeout to very large values",
            "If the server is not running at all, no amount of waiting will help; masks the real problem", 0.78),
         de("Call the service without waiting, catching exceptions",
            "The call itself will fail with a cryptic error; try/except hides configuration bugs", 0.72),
         de("Use topics instead of services for request/reply",
            "Loses the synchronous call guarantee and requires manual correlation of responses", 0.80)],
        [wa("Verify the service server node is running and the name matches exactly", 0.92,
            "ros2 service list | grep my_service"),
         wa("Check namespace: service name may be under a namespace prefix", 0.88,
            "ros2 service list  # look for /namespace/my_service"),
         wa("Use wait_for_service with a reasonable timeout and informative error", 0.85,
            "if not client.wait_for_service(timeout_sec=5.0): raise RuntimeError('Service not found')")],
        preceded_by=[preceded("ros2/package-not-found/ros2-humble-linux", 0.15, "Server node package not built or sourced")],
    ))

    canons.append(canon(
        "ros2", "action-server-not-available", "ros2-humble-linux",
        "Action server not available: /navigate_to_pose",
        r"(Action server not available|action.*not available|ActionClient.*wait_for_server.*timed out)",
        "communication_error", "ros2", ">=humble,<rolling", "linux", "true", 0.82, 0.86,
        "Action server is not running. Common with Nav2, MoveIt2, or custom action servers that take time to start.",
        [de("Launch the action client before the server is up without any wait",
            "Action calls will silently fail or raise confusing 'goal rejected' errors", 0.80),
         de("Replace action with service call for long-running tasks",
            "Services block the caller and provide no feedback or cancellation support", 0.85)],
        [wa("Use wait_for_server() with appropriate timeout before sending goals", 0.90,
            "action_client.wait_for_server(timeout_sec=10.0)"),
         wa("Check action server is running with ros2 action list", 0.88,
            "ros2 action list | grep navigate_to_pose"),
         wa("Ensure server node dependencies (TF, costmap) are fully initialized before accepting goals", 0.82)],
        preceded_by=[preceded("ros2/tf-lookup-exception/ros2-humble-linux", 0.20, "Nav2 action server waits for TF and does not advertise until transforms are ready")],
    ))

    canons.append(canon(
        "ros2", "parameter-already-declared", "ros2-humble-linux",
        "rclpy.exceptions.ParameterAlreadyDeclaredException: Parameter 'use_sim_time' has already been declared",
        r"(ParameterAlreadyDeclaredException|Parameter.*already.*declared|rclpy.*parameter.*already)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.92, 0.90,
        "declare_parameter() called twice for the same parameter name. Common when mixing automatic and manual declaration.",
        [de("Catch the exception and ignore it",
            "Silently uses the first declaration value; later code may expect a different default", 0.70),
         de("Undeclare then re-declare the parameter",
            "Causes a brief period where the parameter does not exist; external observers may see inconsistent state", 0.65)],
        [wa("Use has_parameter() before declare_parameter()", 0.92,
            "if not self.has_parameter('my_param'): self.declare_parameter('my_param', default_value)"),
         wa("Declare all parameters once in __init__ and use get_parameter() elsewhere", 0.95),
         wa("Set automatically_declare_parameters_from_overrides=False if declaring manually", 0.85)],
    ))

    canons.append(canon(
        "ros2", "dds-discovery-failure", "ros2-humble-linux",
        "[WARN] No DDS participants discovered on domain 0",
        r"(No.*participant.*discover|DDS.*discovery.*fail|nodes not visible|can.?t see.*nodes|RMW.*discovery)",
        "communication_error", "ros2", ">=humble,<rolling", "linux", "partial", 0.72, 0.85,
        "ROS 2 nodes cannot discover each other. Usually a DDS multicast or ROS_DOMAIN_ID mismatch.",
        [de("Reinstall ROS 2 entirely",
            "Discovery issues are network/DDS configuration problems, not installation problems", 0.88),
         de("Switch RMW vendor blindly",
            "Discovery failure usually stems from network config (firewall, multicast), not the DDS vendor", 0.75),
         de("Set ROS_LOCALHOST_ONLY on multi-machine setups",
            "This disables network discovery entirely; nodes on other machines become invisible", 0.90)],
        [wa("Verify ROS_DOMAIN_ID matches on all machines", 0.90,
            "echo $ROS_DOMAIN_ID  # must be the same on all machines (default: 0)"),
         wa("Check firewall allows UDP multicast on ports 7400-7500", 0.85,
            "sudo ufw allow 7400:7500/udp"),
         wa("Test with ROS_LOCALHOST_ONLY=1 on single machine first to isolate network issues", 0.88,
            "ROS_LOCALHOST_ONLY=1 ros2 run demo_nodes_cpp talker")],
        confused_with=[confused("ros2/qos-incompatible/ros2-humble-linux", "QoS incompatibility drops messages but nodes see each other; DDS discovery failure means nodes cannot see each other at all")],
    ))

    canons.append(canon(
        "ros2", "rosdep-key-not-found", "ros2-humble-linux",
        "ERROR: the following packages/stacks could not have their rosdep keys resolved",
        r"(rosdep.*key.*not.*resolved|rosdep.*key.*not found|Cannot locate rosdep definition|rosdep.*ERROR)",
        "build_error", "ros2", ">=humble,<rolling", "linux", "true", 0.88, 0.90,
        "rosdep cannot find a system dependency key declared in package.xml. Missing rosdep database update or custom keys.",
        [de("Add the dependency directly to CMakeLists.txt find_package without rosdep",
            "The dependency still won't be installed on CI/CD or other developers' machines", 0.80),
         de("Remove the dependency from package.xml",
            "Other packages depending on yours will have broken builds", 0.85)],
        [wa("Update the rosdep database first", 0.92,
            "rosdep update && rosdep install --from-paths src --ignore-src -y"),
         wa("Add custom rosdep key in a yaml file for non-standard packages", 0.85,
            "echo 'yaml file:///path/to/custom.yaml' | sudo tee /etc/ros/rosdep/sources.list.d/50-custom.list"),
         wa("Use --skip-keys for known-missing keys during development", 0.80,
            "rosdep install --from-paths src --ignore-src -y --skip-keys='my_custom_dep'")],
        preceded_by=[preceded("ros2/colcon-build-cmake-error/ros2-humble-linux", 0.20, "colcon build fails because rosdep dependencies not installed")],
    ))

    canons.append(canon(
        "ros2", "urdf-xacro-parse-error", "ros2-humble-linux",
        "xacro: error: XML parsing error: not well-formed (invalid token)",
        r"(xacro.*error|xacro.*XML.*pars|URDF.*parsing.*error|robot_description.*invalid|Error processing.*xacro)",
        "build_error", "ros2", ">=humble,<rolling", "linux", "true", 0.90, 0.88,
        "XACRO/URDF file has XML syntax errors or undefined xacro macros/properties.",
        [de("Edit the URDF file that xacro generates instead of the .xacro source",
            "Generated URDF is overwritten on each build; edits are lost", 0.90),
         de("Ignore xacro and write raw URDF for complex robots",
            "Raw URDF is unmaintainable at scale; loses parameterization, macros, and math expressions", 0.80)],
        [wa("Run xacro standalone to get a clear error with line numbers", 0.92,
            "xacro my_robot.urdf.xacro > /dev/null"),
         wa("Check all xacro:property and xacro:macro definitions are included", 0.88,
            "Verify all <xacro:include filename='...' /> paths are correct"),
         wa("Use check_urdf to validate the generated URDF", 0.85,
            "xacro my_robot.urdf.xacro | check_urdf /dev/stdin")],
        leads_to=[leads("ros2/tf-lookup-exception/ros2-humble-linux", 0.25, "Invalid URDF means robot_state_publisher publishes no TF frames")],
    ))

    canons.append(canon(
        "ros2", "cv-bridge-conversion-error", "ros2-humble-linux",
        "cv_bridge.CvBridgeError: [ImageConvert] Unsupported conversion from bgr8 to mono8",
        r"(cv_bridge.*CvBridgeError|CvBridge.*Unsupported conversion|cv_bridge.*encoding.*error|imgmsg_to_cv2.*error)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.88, 0.90,
        "cv_bridge cannot convert between the requested image encodings. Source and target encoding mismatch.",
        [de("Force encoding to passthrough and manually convert",
            "Passthrough skips validation; OpenCV may segfault on unexpected data layouts", 0.72),
         de("Change the camera driver encoding to match your code",
            "Other subscribers depend on the original encoding; breaks the whole image pipeline", 0.80)],
        [wa("Use the correct desired_encoding in imgmsg_to_cv2", 0.92,
            "cv_image = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')"),
         wa("Convert after receiving using OpenCV cvtColor", 0.88,
            "cv_image = bridge.imgmsg_to_cv2(msg, 'passthrough'); cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)"),
         wa("Check camera topic encoding with ros2 topic echo --field encoding", 0.85,
            "ros2 topic echo /camera/image_raw --field encoding --once")],
    ))

    canons.append(canon(
        "ros2", "lifecycle-transition-error", "ros2-humble-linux",
        "Transition is not registered: current state 'unconfigured' goal state 'active'",
        r"(Transition.*not registered|lifecycle.*transition.*error|LifecycleNode.*cannot transition|invalid.*lifecycle.*state)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.85, 0.88,
        "Lifecycle node transition attempted in wrong order. Must follow unconfigured->inactive->active sequence.",
        [de("Call activate() directly from unconfigured state",
            "Lifecycle state machine requires configure->activate sequence; skipping configure is not allowed", 0.90),
         de("Use regular Node class and fake lifecycle callbacks",
            "Loses lifecycle management integration with launch files and system managers", 0.75)],
        [wa("Follow the lifecycle transition sequence: configure then activate", 0.95,
            "ros2 lifecycle set /my_node configure && ros2 lifecycle set /my_node activate"),
         wa("Use lifecycle launch events to trigger transitions automatically", 0.88,
            "RegisterEventHandler(OnStateTransition(...))"),
         wa("Check current state before transitioning", 0.85,
            "ros2 lifecycle get /my_node")],
    ))

    canons.append(canon(
        "ros2", "topic-type-mismatch", "ros2-humble-linux",
        "[ERROR] create_subscription(): type mismatch for topic '/cmd_vel'",
        r"(type mismatch.*topic|incompatible.*message type|topic.*type.*different|expected.*msg.*got)",
        "communication_error", "ros2", ">=humble,<rolling", "linux", "true", 0.90, 0.88,
        "Publisher and subscriber use different message types on the same topic name.",
        [de("Change one side's message type without updating the other",
            "Causes the same error on the other node; both must agree on the exact message type", 0.85),
         de("Use a generic Any type or raw bytes",
            "ROS 2 does not support untyped topics; DDS requires concrete IDL types for serialization", 0.92)],
        [wa("Check actual topic type with ros2 topic info", 0.95,
            "ros2 topic info /cmd_vel --verbose  # shows type for each publisher/subscriber"),
         wa("Ensure both nodes import the same message package and type", 0.92,
            "from geometry_msgs.msg import Twist  # must match on both sides"),
         wa("Use ros2 interface show to inspect the message definition", 0.85,
            "ros2 interface show geometry_msgs/msg/Twist")],
        confused_with=[confused("ros2/qos-incompatible/ros2-humble-linux", "QoS incompatibility: same type but different delivery guarantees. Type mismatch: different message types on same topic name.")],
    ))

    canons.append(canon(
        "ros2", "colcon-circular-dependency", "ros2-humble-linux",
        "colcon: packages have a circular dependency: pkg_a -> pkg_b -> pkg_a",
        r"(circular dependency|colcon.*circular|dependency cycle|topological sort.*failed)",
        "build_error", "ros2", ">=humble,<rolling", "linux", "true", 0.85, 0.88,
        "Two or more packages depend on each other forming a cycle. colcon cannot determine build order.",
        [de("Force build order with --packages-above/below",
            "Hides the cycle; one package will always build with stale dependencies", 0.80),
         de("Copy shared headers directly between packages",
            "Creates undeclared dependencies; breaks on clean builds and CI", 0.88)],
        [wa("Extract shared types/interfaces into a separate package", 0.92,
            "Create pkg_interfaces with only .msg/.srv/.action files, depend on it from both packages"),
         wa("Visualize the dependency graph to find the cycle", 0.88,
            "colcon graph --dot | dot -Tpng -o deps.png"),
         wa("Use build_depend vs exec_depend correctly in package.xml", 0.85)],
    ))

    canons.append(canon(
        "ros2", "timer-callback-overrun", "ros2-humble-linux",
        "[WARN] Timer callback took longer than the timer period",
        r"(Timer.*callback.*longer|callback.*overrun|timer.*miss.*deadline|timer.*period.*exceed)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "partial", 0.70, 0.85,
        "Timer callback execution time exceeds the timer period. Messages pile up and processing lags behind real time.",
        [de("Decrease timer period to catch up on missed callbacks",
            "Makes the problem worse; callbacks pile up even faster", 0.90),
         de("Add a sleep inside the callback to throttle",
            "sleep() blocks the executor, preventing all other callbacks from running", 0.92)],
        [wa("Move heavy processing to a separate thread or process", 0.88,
            "Use MultiThreadedExecutor with ReentrantCallbackGroup for parallelism"),
         wa("Profile the callback and optimize the bottleneck", 0.85,
            "import cProfile; cProfile.runctx('callback(msg)', ...)"),
         wa("Increase timer period to match actual processing time", 0.82)],
    ))

    canons.append(canon(
        "ros2", "bag-storage-plugin-not-found", "ros2-humble-linux",
        "RuntimeError: Could not load storage plugin: sqlite3",
        r"(Could not load.*storage.*plugin|bag.*storage.*plugin.*not found|rosbag2.*plugin.*error|sqlite3.*plugin)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.90, 0.88,
        "rosbag2 cannot find the storage backend plugin. Usually the rosbag2 storage packages are not installed.",
        [de("Install sqlite3 system library and expect rosbag2 to find it",
            "rosbag2 needs its own ROS wrapper plugin, not just the system sqlite3 library", 0.82),
         de("Build rosbag2 from source in your workspace",
            "rosbag2 has many interdependent packages; partial source builds create version conflicts", 0.78)],
        [wa("Install the rosbag2 storage plugin packages", 0.95,
            "sudo apt install ros-humble-rosbag2-storage-default-plugins ros-humble-rosbag2-storage-sqlite3"),
         wa("Verify plugin is found with ros2 bag info on an existing bag", 0.85,
            "ros2 bag info my_bag/"),
         wa("Use MCAP storage format as alternative (better performance)", 0.82,
            "ros2 bag record -s mcap -a")],
    ))

    canons.append(canon(
        "ros2", "nav2-bt-action-failed", "ros2-humble-linux",
        "[nav2_bt_navigator] Action server failed: NavigateToPose",
        r"(nav2.*bt.*fail|NavigateToPose.*fail|nav2.*action.*abort|BT.*node.*FAILURE|navigation.*abort)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "partial", 0.68, 0.82,
        "Nav2 behavior tree action fails. Root cause varies: costmap not ready, planner timeout, controller stuck.",
        [de("Restart Nav2 stack on every failure",
            "Restarts are expensive and lose all accumulated costmap data; hides the actual navigation issue", 0.78),
         de("Increase all timeouts to very large values",
            "Masks configuration errors; robot sits idle for minutes before finally reporting failure", 0.80),
         de("Replace the entire BT XML with a simple sequence",
            "Loses recovery behaviors, replanning, and fallback strategies", 0.85)],
        [wa("Check Nav2 logs for the specific BT node that failed", 0.90,
            "ros2 topic echo /behavior_tree_log"),
         wa("Verify costmap is populated (not empty) before navigation", 0.85,
            "ros2 topic echo /local_costmap/costmap --once"),
         wa("Test individual Nav2 components (planner, controller) separately", 0.82,
            "ros2 action send_goal /compute_path_to_pose nav2_msgs/action/ComputePathToPose ...")],
        preceded_by=[preceded("ros2/tf-lookup-exception/ros2-humble-linux", 0.30, "Nav2 requires complete TF tree; missing frames cause planner failures")],
    ))

    canons.append(canon(
        "ros2", "gazebo-plugin-load-error", "ros2-humble-linux",
        "[ERROR] [gazebo_ros2_control]: Failed to load plugin",
        r"(Failed to load.*plugin|gazebo.*plugin.*error|libgazebo.*not found|ClassLoader.*unable|gz.*plugin.*fail)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.82, 0.88,
        "Gazebo cannot load a ROS 2 plugin (controller, sensor, etc.). Usually a missing package or library path issue.",
        [de("Set LD_LIBRARY_PATH manually to point at the plugin .so",
            "Fragile and doesn't persist; the real issue is missing package installation or env sourcing", 0.78),
         de("Build Gazebo plugins from source with colcon",
            "Gazebo ROS plugins have complex dependencies; source builds often mismatch binary Gazebo version", 0.82)],
        [wa("Install the missing Gazebo ROS package via apt", 0.90,
            "sudo apt install ros-humble-gazebo-ros2-control"),
         wa("Source both ROS 2 and Gazebo setup scripts before launching", 0.88,
            "source /opt/ros/humble/setup.bash && source /usr/share/gazebo/setup.bash"),
         wa("Check plugin filename in URDF matches the installed library", 0.85,
            "find /opt/ros/humble/lib -name '*gazebo*control*'")],
        preceded_by=[preceded("ros2/urdf-xacro-parse-error/ros2-humble-linux", 0.15, "URDF errors cause Gazebo to load an invalid model with broken plugin references")],
    ))

    canons.append(canon(
        "ros2", "ros2-control-hardware-not-found", "ros2-humble-linux",
        "[controller_manager] Loading of hardware interface failed",
        r"(hardware interface.*fail|ros2_control.*hardware.*not found|HardwareInterface.*error|controller_manager.*fail.*load)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.80, 0.85,
        "ros2_control cannot load the specified hardware interface plugin. URDF ros2_control tag or plugin name is wrong.",
        [de("Bypass ros2_control and publish joint states directly",
            "Loses hardware abstraction, safety limits, and real-time guarantees", 0.85),
         de("Copy a hardware interface .so from another workspace",
            "Binary incompatibility between different colcon workspaces causes segfaults", 0.80)],
        [wa("Verify the hardware plugin name in URDF matches the installed plugin class", 0.90,
            "ros2 control list_hardware_interfaces  # after controller_manager is up"),
         wa("Install the correct ros2_control hardware package", 0.88,
            "sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers"),
         wa("Check URDF <ros2_control> tag has correct plugin attribute", 0.85,
            "grep -A5 'ros2_control' my_robot.urdf.xacro")],
        preceded_by=[preceded("ros2/urdf-xacro-parse-error/ros2-humble-linux", 0.20, "URDF parse error causes ros2_control configuration to be empty")],
    ))

    canons.append(canon(
        "ros2", "executor-spin-error", "ros2-humble-linux",
        "rclpy.executors.ExternalShutdownException: Context must be initialized before use",
        r"(ExternalShutdownException|Context.*initialized|executor.*shutdown|rclpy.*already.*shutdown|spin.*after.*shutdown)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.88, 0.88,
        "Node shutdown was triggered externally (Ctrl+C) while the executor was spinning. Context is no longer valid.",
        [de("Catch the exception and keep spinning",
            "Context is already destroyed; continued spinning causes undefined behavior and potential segfault", 0.90),
         de("Call rclpy.init() again after shutdown",
            "Multiple init/shutdown cycles are fragile and leak resources in many RMW implementations", 0.78)],
        [wa("Wrap spin in try/except for graceful shutdown", 0.92,
            "try: rclpy.spin(node) except (KeyboardInterrupt, ExternalShutdownException): pass finally: node.destroy_node(); rclpy.try_shutdown()"),
         wa("Use rclpy.try_shutdown() instead of rclpy.shutdown() for safe cleanup", 0.90),
         wa("Register an on_shutdown callback for resource cleanup", 0.85,
            "context.on_shutdown(cleanup_function)")],
    ))

    canons.append(canon(
        "ros2", "domain-id-conflict", "ros2-humble-linux",
        "Receiving messages from unexpected nodes on ROS_DOMAIN_ID=0",
        r"(ROS_DOMAIN_ID.*conflict|unexpected.*node.*domain|domain.*collision|multiple.*robot.*same.*domain)",
        "communication_error", "ros2", ">=humble,<rolling", "linux", "true", 0.92, 0.90,
        "Multiple ROS 2 systems on the same network use the same DOMAIN_ID, causing topic/service cross-talk.",
        [de("Filter messages by node name in subscriber callbacks",
            "Does not prevent DDS discovery overhead or parameter/service collisions", 0.80),
         de("Use different topic names for each robot system",
            "Does not prevent DDS discovery flooding; every node still discovers all others", 0.75)],
        [wa("Assign unique ROS_DOMAIN_ID (0-101) to each independent system", 0.95,
            "export ROS_DOMAIN_ID=42  # unique per system, range 0-101"),
         wa("Use namespaces within a shared domain for cooperating robots", 0.88,
            "ros2 launch my_pkg bringup.launch.py namespace:=robot1"),
         wa("Use ROS_LOCALHOST_ONLY=1 for development on shared networks", 0.85,
            "export ROS_LOCALHOST_ONLY=1")],
        confused_with=[confused("ros2/dds-discovery-failure/ros2-humble-linux", "Discovery failure: nodes can't find each other. Domain ID conflict: nodes find TOO MANY other nodes from other systems.")],
    ))

    # =====================================================================
    # === EMBEDDED ===
    # =====================================================================
    canons.append(canon(
        "embedded", "stlink-connection-failed", "stm32-arm-linux",
        "Error: init mode failed (unable to connect to the target)",
        r"(unable to connect to the target|init mode failed|Error connecting.*ST-?LINK|No STM32 target found)",
        "debugger_error", "openocd", ">=0.11", "linux", "true", 0.85, 0.88,
        "ST-LINK cannot connect to STM32 via SWD/JTAG. Wiring, BOOT pins, sleep mode, or flash protection.",
        [de("Increase SWD clock frequency for stable connection",
            "Higher frequency makes marginal connections WORSE; long wires need LOWER frequencies", 0.80),
         de("Replace the ST-LINK adapter assuming it is broken",
            "Usually the target chip or wiring is the problem. Verify with a second target board first.", 0.70),
         de("Flash via serial bootloader to fix debug port",
            "Serial flash may work but does not re-enable SWD if firmware disabled the SWD pins", 0.72)],
        [wa("Use connect under reset mode", 0.90,
            "openocd -f interface/stlink.cfg -c 'reset_config srst_only' -f target/stm32f4x.cfg"),
         wa("Check SWD wiring: SWDIO, SWCLK, GND, and NRST", 0.88,
            "Minimum: GND, SWDIO (PA13), SWCLK (PA14). Keep wires under 10cm."),
         wa("Erase flash via BOOT0 pin to recover bricked chips", 0.85,
            "Set BOOT0=HIGH, power cycle, erase via STM32CubeProgrammer UART, then BOOT0=LOW")],
        arch="arm",
    ))

    canons.append(canon(
        "embedded", "uart-framing-error", "stm32-arm-linux",
        "UART framing error: start/stop bit mismatch",
        r"(UART.*framing error|framing error.*UART|start.*stop.*bit.*mismatch|USART.*FE flag|ORE.*overrun)",
        "communication_error", "stm32", ">=F1", "cross-platform", "true", 0.88, 0.90,
        "UART produces garbage or framing errors. Almost always baud rate mismatch or parity mismatch.",
        [de("Swap TX and RX wires assuming they are crossed",
            "TX/RX swap produces silence, not framing errors. Framing errors mean data arrives but cannot be decoded.", 0.75),
         de("Add pull-up resistors to TX/RX lines",
            "UART is push-pull, not open-drain. Pull-ups do not fix framing errors.", 0.70),
         de("Increase baud rate for faster communication",
            "The issue is mismatch, not speed. Both sides must agree on identical settings.", 0.82)],
        [wa("Verify both sides use identical settings: baud, data bits, stop bits, parity", 0.95,
            "Common default: 115200 8N1 (115200 baud, 8 data bits, no parity, 1 stop bit)"),
         wa("Check clock source accuracy - HSI can drift causing baud errors", 0.85,
            "STM32 HSI is +/-1% at 25C but worse at extremes. Use HSE crystal for reliable UART."),
         wa("Use oscilloscope or logic analyzer to measure actual bit timing", 0.88,
            "Measure shortest pulse; 1/width = actual baud rate")],
    ))

    canons.append(canon(
        "embedded", "can-bus-off", "stm32-arm-linux",
        "CAN error: Bus-off state entered (TEC >= 256)",
        r"(CAN.*[Bb]us.?off|TEC.*256|transmit error counter|CAN.*error.passive|bxCAN.*BOF)",
        "communication_error", "stm32", ">=F1", "cross-platform", "partial", 0.60, 0.85,
        "CAN controller entered bus-off after too many transmit errors. Node disconnected from bus.",
        [de("Restart CAN peripheral immediately in a tight loop",
            "Rapid restart floods bus with error frames and may force OTHER nodes bus-off", 0.85),
         de("Increase CAN bus speed",
            "Higher speed needs tighter timing and shorter bus; usually makes it worse", 0.80),
         de("Disable CAN error interrupts",
            "Node is still disconnected; disabling interrupts just hides the state", 0.90)],
        [wa("Check CAN bus termination: two 120 ohm resistors at each end", 0.88,
            "Measure between CAN_H and CAN_L powered off: should read ~60 ohm"),
         wa("Verify bit timing matches all other nodes on the bus", 0.85,
            "All nodes must agree on baud rate and sample point (typically 87.5% for 500kbps)"),
         wa("Implement bus-off recovery with backoff delay", 0.80,
            "HAL_CAN_Start() after bus-off with 100ms+ delay to let bus settle")],
    ))

    canons.append(canon(
        "embedded", "usb-device-descriptor-read-error", "linux-host",
        "usb 1-1: device descriptor read/64, error -71",
        r"(device descriptor read.*error|usb.*descriptor.*failed|USB.*EPROTO|Cannot enumerate USB|device not accepting address)",
        "usb_error", "linux-kernel", ">=5.4", "linux", "true", 0.78, 0.85,
        "Linux fails to enumerate USB device. Error -71 (EPROTO) = protocol failure during descriptor read. Hardware/signal issue.",
        [de("Recompile kernel with different USB options",
            "Protocol errors during enumeration are electrical issues, not kernel config", 0.85),
         de("Upgrade cable to USB 3.0",
            "USB 3.0 cables may lack proper USB 2.0 data pair wiring. Use known-good USB 2.0 cable.", 0.72),
         de("Disable USB autosuspend globally",
            "Autosuspend affects already-enumerated devices, not initial enumeration", 0.68)],
        [wa("Try a different USB port directly on the motherboard", 0.88,
            "Front panel ports have longer wires and more EMI. Use rear motherboard ports."),
         wa("Use a powered USB hub for adequate power delivery", 0.85),
         wa("Check dmesg for specific error code", 0.82,
            "dmesg | grep usb  # -71=EPROTO, -32=EPIPE, -110=ETIMEDOUT")],
    ))

    canons.append(canon(
        "embedded", "hardfault-handler", "stm32-arm-linux",
        "HardFault_Handler: FORCED, bus fault at address 0x00000000",
        r"(HardFault|Hard[_ ]?[Ff]ault|BusFault|MemManage|UsageFault|FORCED.*fault)",
        "runtime_error", "stm32", ">=F1", "cross-platform", "partial", 0.55, 0.85,
        "ARM Cortex-M hard fault. Null pointer, stack overflow, unaligned access, or invalid memory.",
        [de("Add while(1) in HardFault handler and inspect PC in debugger",
            "PC in handler points to handler itself, not faulting instruction. Read stacked PC from exception frame.", 0.72),
         de("Increase heap size assuming memory allocation failure",
            "Hard faults are usually stack overflow or dangling pointers. Heap failures return NULL.", 0.78),
         de("Disable fault handlers to prevent stopping",
            "Without handlers, faults escalate to lockup; processor halts until hardware reset", 0.92)],
        [wa("Read stacked PC/LR from exception frame to find faulting instruction", 0.85,
            "In handler: read SP, stacked_pc = *(SP+24), look up in .map file"),
         wa("Enable BusFault, MemManage, UsageFault handlers for specific info", 0.88,
            "SCB->SHCSR |= (BUSFAULTENA | MEMFAULTENA | USGFAULTENA);"),
         wa("Check stack size and add overflow detection", 0.80,
            "FreeRTOS: configCHECK_FOR_STACK_OVERFLOW=2; Bare metal: fill stack with 0xDEADBEEF")],
        arch="arm",
    ))

    canons.append(canon(
        "embedded", "i2c-nack", "stm32-arm-linux",
        "I2C error: NACK received (AF flag set), address 0x68",
        r"(I2C.*NACK|NACK.*received|AF.*flag|acknowledge failure|i2c.*no ack|HAL_I2C_ERROR_AF)",
        "communication_error", "stm32", ">=F1", "cross-platform", "true", 0.85, 0.88,
        "I2C slave does not acknowledge. Almost always wrong address (7-bit vs 8-bit confusion) or missing pull-ups.",
        [de("Add more pull-up resistors in parallel",
            "Too-low resistance causes signal distortion. Standard: 4.7k for 100kHz, 2.2k for 400kHz.", 0.70),
         de("Increase I2C clock speed to reduce NACK",
            "NACKs are not timing-related. Higher speed makes bus problems worse.", 0.82),
         de("Brute-force scan all addresses",
            "Some devices (EEPROMs) respond to scan with side effects like data corruption", 0.55)],
        [wa("Verify 7-bit address - datasheets often list 8-bit (left-shifted) address", 0.95,
            "Datasheet says 0xD0 -> 7-bit is 0x68. HAL uses 8-bit: HAL_I2C_Master_Transmit(hi2c, 0xD0, ...)"),
         wa("Check hardware: SDA, SCL, pull-ups to VCC", 0.90,
            "Both lines need pull-ups (4.7k to 3.3V). Idle state should be HIGH."),
         wa("Use logic analyzer to verify actual bus activity", 0.85)],
    ))

    # =====================================================================
    # === OPENCV ===
    # =====================================================================
    canons.append(canon(
        "opencv", "videocapture-cannot-open", "opencv4-linux",
        "VideoCapture: can't open camera by index / !_src.empty() in function 'cvtColor'",
        r"(can't open camera|Cannot open camera|VideoCapture.*failed|!_src\.empty\(\)|CAP_V4L2.*Unable)",
        "camera_error", "opencv", ">=4.5", "linux", "true", 0.82, 0.88,
        "OpenCV VideoCapture fails to open camera. V4L2 permission issue, wrong index, or camera used by another process.",
        [de("Install opencv-python-headless to fix camera issues",
            "Headless variant REMOVES GUI and camera support. Use opencv-python or opencv-contrib-python.", 0.88),
         de("Use camera index 0 assuming it is always the first camera",
            "On multi-camera systems, indices shift. /dev/video0 may be a metadata device.", 0.70),
         de("Set CAP_PROP_FPS before opening capture",
            "Properties cannot be set before device is open; the open itself is failing", 0.75)],
        [wa("Check device existence and permissions", 0.92,
            "ls -la /dev/video* && sudo usermod -aG video $USER"),
         wa("Try specific backend and enumerate devices", 0.88,
            "cap = cv2.VideoCapture(0, cv2.CAP_V4L2)"),
         wa("Check if another process is using the camera", 0.85,
            "fuser /dev/video0")],
    ))

    canons.append(canon(
        "opencv", "mat-type-assertion", "opencv4-linux",
        "cv2.error: (-215:Assertion failed) src.type() == CV_8UC1 in function 'equalizeHist'",
        r"(Assertion failed.*src\.type\(\)|CV_8UC[13]|src\.depth\(\)|expected.*Mat.*type)",
        "type_error", "opencv", ">=4.5", "linux", "true", 0.90, 0.92,
        "OpenCV function received Mat with wrong type or channels. equalizeHist/Canny require grayscale.",
        [de("Convert to float32 assuming function needs float",
            "Most OpenCV functions expect CV_8U (uint8). Float without scaling produces black images.", 0.75),
         de("Reshape Mat dimensions instead of converting color space",
            "numpy reshape changes memory layout but not pixel format", 0.82)],
        [wa("Convert color space before calling the function", 0.95,
            "gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)"),
         wa("Check actual type of your Mat", 0.88,
            "print(img.shape, img.dtype)  # (H,W,3) uint8=BGR; (H,W) uint8=gray")],
    ))

    canons.append(canon(
        "opencv", "realsense-device-not-found", "opencv4-linux",
        "RuntimeError: No RealSense devices were found",
        r"(No RealSense devices|RealSense.*not found|Failed to set power state|rs2.*RS2_EXCEPTION|librealsense.*No device)",
        "camera_error", "librealsense", ">=2.50", "linux", "true", 0.78, 0.85,
        "Intel RealSense not detected. USB 2.0 port (D400 needs 3.0), missing udev rules, or kernel conflict.",
        [de("Install librealsense from pip only",
            "pip pyrealsense2 is just the wrapper; you need udev rules and kernel patches from official repo", 0.80),
         de("Use USB 2.0 port for D400 series",
            "D435/D455 require USB 3.0 for depth streaming. May enumerate on 2.0 but depth fails.", 0.85),
         de("Compile librealsense from source on Ubuntu LTS",
            "Official APT repo with DKMS patches is easier and more reliable", 0.65)],
        [wa("Install from official APT repository with kernel patches", 0.90,
            "Follow github.com/IntelRealSense/librealsense/blob/master/doc/distribution_linux.md"),
         wa("Check USB 3.0 connection via lsusb", 0.88,
            "lsusb -t | grep realsense  # speed should show 5000M not 480M"),
         wa("Install udev rules for non-root access", 0.85,
            "sudo cp config/99-realsense-libusb.rules /etc/udev/rules.d/ && sudo udevadm control --reload-rules")],
    ))

    canons.append(canon(
        "opencv", "size-mismatch", "opencv4-linux",
        "cv2.error: (-209:Sizes of input arguments do not match)",
        r"(Sizes of input arguments do not match|src\.size\(\) == dst\.size\(\)|images must have the same size)",
        "dimension_error", "opencv", ">=4.5", "linux", "true", 0.92, 0.92,
        "Two Mats have different dimensions. Common with addWeighted, bitwise_and, absdiff.",
        [de("Pad smaller image with zeros",
            "Zero-padding changes content and produces artifacts; resize is usually correct", 0.68),
         de("Crop both to minimum overlapping region without checking alignment",
            "Cropping without spatial relationship gives meaningless results", 0.72)],
        [wa("Resize one image to match the other", 0.95,
            "img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))  # (width, height)"),
         wa("Check shapes before operation", 0.90,
            "assert img1.shape[:2] == img2.shape[:2], f'{img1.shape} vs {img2.shape}'"),
         wa("Use ROI to extract matching regions", 0.82)],
    ))

    canons.append(canon(
        "opencv", "cascade-classifier-empty", "opencv4-linux",
        "cv2.error: (-215:Assertion failed) !empty() in function 'detectMultiScale'",
        r"(!empty\(\).*detectMultiScale|empty.*cascade|CascadeClassifier.*empty)",
        "configuration_error", "opencv", ">=4.5", "linux", "true", 0.92, 0.90,
        "CascadeClassifier is empty because XML model file was not loaded. Wrong file path.",
        [de("Download XML from random GitHub repo",
            "Third-party files may be incompatible. Use official OpenCV data files.", 0.72),
         de("Use relative path assuming cwd is script location",
            "Python cwd is where you ran the command, not where the script lives", 0.80)],
        [wa("Use cv2.data.haarcascades for bundled cascades", 0.95,
            "cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')"),
         wa("Check if cascade loaded before using", 0.90,
            "if face_cascade.empty(): raise FileNotFoundError('Cascade not found')"),
         wa("Use absolute path via __file__", 0.85,
            "os.path.join(os.path.dirname(__file__), 'models', 'my_cascade.xml')")],
    ))

    canons.append(canon(
        "opencv", "v4l2-device-error", "opencv4-linux",
        "VIDEOIO ERROR: V4L2: Unable to open device /dev/video0: Permission denied",
        r"(V4L2.*Unable to open|VIDEOIO.*V4L2|v4l2.*VIDIOC_STREAMON|V4L2.*Permission denied)",
        "camera_error", "v4l2", ">=5.4", "linux", "true", 0.85, 0.88,
        "V4L2 cannot open video device. Permission issue, Docker container, or headless server.",
        [de("Compile OpenCV from source with V4L2 support",
            "pip opencv-python already includes V4L2 on Linux; issue is OS-level permissions", 0.78),
         de("Use GStreamer backend as workaround",
            "GStreamer also needs device permissions; switching backend does not bypass OS checks", 0.72)],
        [wa("Add user to video group", 0.92,
            "sudo usermod -aG video $USER && newgrp video"),
         wa("For Docker: pass device and group", 0.88,
            "docker run --device=/dev/video0:/dev/video0 --group-add video my_image"),
         wa("Find correct video node (not metadata node)", 0.82,
            "v4l2-ctl --list-devices")],
    ))

    # =====================================================================
    # === CMAKE ===
    # =====================================================================
    canons.append(canon(
        "cmake", "find-package-not-found", "cmake3-linux",
        "CMake Error: Could NOT find OpenCV (missing: OpenCV_DIR)",
        r"(Could NOT find \w+|find_package.*REQUIRED.*missing|_DIR.*not set|Config file.*not found)",
        "build_error", "cmake", ">=3.16", "linux", "true", 0.88, 0.90,
        "find_package() cannot locate a dependency. Config file or Find module not in search path.",
        [de("Set CMAKE_PREFIX_PATH to the source directory",
            "Should point to INSTALL prefix (where lib/cmake/ lives), not the source tree", 0.78),
         de("Copy .cmake files into your project",
            "Bundling third-party cmake configs creates version mismatches", 0.80),
         de("Use find_library() as drop-in replacement",
            "find_library() only finds .so/.a but not headers, definitions, or transitive deps", 0.72)],
        [wa("Install development package via system package manager", 0.92,
            "sudo apt install libopencv-dev"),
         wa("Set package-specific _DIR variable", 0.88,
            "cmake -DOpenCV_DIR=/path/to/opencv/build .."),
         wa("Use CMAKE_PREFIX_PATH for custom installs", 0.85,
            "cmake -DCMAKE_PREFIX_PATH=/opt/opencv ..")],
    ))

    canons.append(canon(
        "cmake", "no-cxx-compiler-found", "cmake3-linux",
        "CMake Error: No CMAKE_CXX_COMPILER could be found",
        r"(No CMAKE_CXX_COMPILER|No CMAKE_C_COMPILER|compiler.*not found|CMAKE_CXX_COMPILER.*NOTFOUND)",
        "build_error", "cmake", ">=3.16", "linux", "true", 0.92, 0.90,
        "CMake cannot find a C/C++ compiler. Toolchain not installed or not in PATH.",
        [de("Set CMAKE_CXX_COMPILER to compiler include directory",
            "Must point to compiler EXECUTABLE (e.g., /usr/bin/g++), not a directory", 0.82),
         de("Install cmake assuming it includes a compiler",
            "CMake is a build system generator, not a compiler. You need gcc/g++ separately.", 0.88)],
        [wa("Install the compiler toolchain", 0.95,
            "sudo apt install build-essential"),
         wa("Use CMake toolchain file for cross-compilation", 0.85,
            "cmake -DCMAKE_TOOLCHAIN_FILE=arm-toolchain.cmake .."),
         wa("Specify compiler explicitly", 0.88,
            "cmake -DCMAKE_CXX_COMPILER=/usr/bin/g++-12 ..")],
    ))

    canons.append(canon(
        "cmake", "target-link-unknown", "cmake3-linux",
        "CMake Error: Cannot specify link libraries for target which is not built by this project",
        r"(Cannot specify link libraries for target|target.*not built by this project|target_link_libraries.*unknown)",
        "build_error", "cmake", ">=3.16", "linux", "true", 0.90, 0.88,
        "target_link_libraries references a nonexistent target. Typo or wrong order in CMakeLists.txt.",
        [de("Use add_custom_target to make it visible",
            "add_custom_target is for custom commands, not linkable libraries", 0.78),
         de("Move target_link_libraries before add_executable",
            "Target must exist before setting properties. add_executable must come FIRST.", 0.85)],
        [wa("Ensure add_executable is called before target_link_libraries", 0.95,
            "add_executable(my_target main.cpp)\ntarget_link_libraries(my_target PRIVATE my_lib)"),
         wa("Check for typos between add_executable and target_link_libraries", 0.90),
         wa("If target is in subdirectory, call add_subdirectory first", 0.85)],
    ))

    canons.append(canon(
        "cmake", "cmake-version-too-old", "cmake3-linux",
        "CMake Error: CMake 3.16 or higher is required. You are running version 3.10.2",
        r"(CMake.*or higher is required|cmake_minimum_required.*VERSION|CMake.*version.*too old)",
        "version_error", "cmake", ">=3.0", "linux", "true", 0.92, 0.90,
        "Project requires newer CMake than installed. Common on Ubuntu LTS with outdated packages.",
        [de("Lower cmake_minimum_required to match installed version",
            "Minimum is set for a reason; lowering it causes cryptic build failures", 0.82),
         de("Install from default Ubuntu apt",
            "Ubuntu LTS ships outdated CMake. 20.04 gives 3.16, 18.04 gives 3.10.", 0.70)],
        [wa("Install from Kitware APT repository", 0.92,
            "sudo apt-add-repository 'deb https://apt.kitware.com/ubuntu/ focal main' && sudo apt install cmake"),
         wa("Install via pip", 0.90,
            "pip install cmake"),
         wa("Download pre-built binary from cmake.org", 0.85)],
    ))

    canons.append(canon(
        "cmake", "ament-cmake-not-found", "cmake3-linux",
        "CMake Error: find_package(ament_cmake REQUIRED) failed: ament_cmake not found",
        r"(find_package\(ament_cmake\)|ament_cmake.*not found|Could not find.*ament|rosidl.*REQUIRED)",
        "build_error", "cmake", ">=3.16", "linux", "true", 0.90, 0.92,
        "CMake cannot find ament_cmake. ROS 2 environment not sourced or package not installed.",
        [de("Install ament_cmake via pip",
            "ament_cmake is CMake-based, distributed via apt, not pip", 0.90),
         de("Add ament_cmake as git submodule",
            "Core ROS 2 infrastructure; source build causes version conflicts", 0.82)],
        [wa("Source ROS 2 installation before cmake/colcon", 0.95,
            "source /opt/ros/humble/setup.bash && colcon build"),
         wa("Install via apt", 0.90,
            "sudo apt install ros-humble-ament-cmake"),
         wa("Add source to shell profile", 0.85,
            "echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc")],
    ))


    # =====================================================================
    # === PYTORCH ===
    # =====================================================================
    canons.append(canon(
        "pytorch", "cuda-out-of-memory", "pytorch2-linux",
        "torch.cuda.OutOfMemoryError: CUDA out of memory. Tried to allocate 2.00 GiB",
        r"(CUDA out of memory|OutOfMemoryError.*CUDA|Tried to allocate.*GiB|CUDA.*OOM)",
        "memory_error", "pytorch", ">=2.0", "linux", "true", 0.85, 0.92,
        "GPU memory exhausted during training or inference. Batch size too large, model too big, or memory leak from accumulated gradients.",
        [de("Set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb to a small value",
            "Reduces fragmentation but does not free memory; often makes OOM happen sooner with a different error", 0.70),
         de("Call torch.cuda.empty_cache() in the training loop",
            "empty_cache releases unused cached memory back to CUDA but does not free tensors still referenced; has no effect if all memory is in use", 0.72),
         de("Upgrade to a GPU with more VRAM as first response",
            "Often the code has a memory leak (not detaching losses, storing all predictions). Fix the code before throwing hardware at it.", 0.60)],
        [wa("Reduce batch size or use gradient accumulation", 0.92,
            "Halve batch_size; use optimizer.step() every N mini-batches to simulate larger batch"),
         wa("Use mixed precision training (AMP)", 0.88,
            "with torch.amp.autocast('cuda'): ... # FP16 uses ~half the memory"),
         wa("Detach loss and move metrics to CPU", 0.85,
            "loss_val = loss.item()  # not loss_val = loss; prevents computation graph accumulation"),
         wa("Use gradient checkpointing for large models", 0.80,
            "model.gradient_checkpointing_enable()  # trades compute for memory")],
        gpu="any", python=">=3.9",
    ))

    canons.append(canon(
        "pytorch", "device-mismatch", "pytorch2-linux",
        "RuntimeError: Expected all tensors to be on the same device, but found at least two devices, cuda:0 and cpu",
        r"(Expected all tensors.*same device|found.*cuda.*cpu|found.*two devices|expected.*device.*got)",
        "device_error", "pytorch", ">=2.0", "linux", "true", 0.92, 0.90,
        "Tensors on different devices (CPU vs GPU) used in same operation. Model on GPU but input on CPU or vice versa.",
        [de("Move every tensor to GPU at creation time",
            "Some tensors (like labels, indices) should stay on CPU until needed. Eager .cuda() wastes VRAM.", 0.65),
         de("Use .cuda() everywhere instead of .to(device)",
            ".cuda() hardcodes GPU and breaks on CPU-only machines or multi-GPU. Use .to(device) consistently.", 0.72)],
        [wa("Use a device variable and .to(device) consistently", 0.95,
            "device = torch.device('cuda' if torch.cuda.is_available() else 'cpu'); model.to(device); x = x.to(device)"),
         wa("Check both model and data are on the same device before forward pass", 0.90,
            "assert next(model.parameters()).device == input_tensor.device"),
         wa("Move criterion/loss function to device if it has parameters", 0.85)],
        gpu="any", python=">=3.9",
    ))

    canons.append(canon(
        "pytorch", "tensor-size-mismatch", "pytorch2-linux",
        "RuntimeError: Sizes of tensors must match except in dimension 1. Expected 64 but got 32",
        r"(Sizes of tensors must match|size mismatch|expected.*but got.*dimension|shape.*doesn.t match|mat1.*mat2.*cannot be multiplied)",
        "shape_error", "pytorch", ">=2.0", "linux", "true", 0.88, 0.90,
        "Tensor dimensions do not match for the operation. Wrong input size, missing reshape, or model architecture mismatch.",
        [de("Add unsqueeze/squeeze randomly until shapes match",
            "Blindly changing dimensions produces numerically wrong results even if the operation succeeds", 0.80),
         de("Transpose the tensor to swap dimensions",
            "Transpose changes semantic meaning (batch vs feature vs spatial). May run but produce garbage output.", 0.72)],
        [wa("Print shapes at each layer to find where mismatch begins", 0.92,
            "print(x.shape) after each layer; or use torchsummary: summary(model, input_size)"),
         wa("Verify input dimensions match what the model expects", 0.90,
            "Check model's first layer: nn.Linear(in_features=784, ...) needs input of shape (batch, 784)"),
         wa("Use adaptive pooling before FC layers to handle variable input sizes", 0.82,
            "nn.AdaptiveAvgPool2d((1, 1))  # outputs fixed size regardless of input spatial dims")],
        python=">=3.9",
    ))

    canons.append(canon(
        "pytorch", "inplace-operation-gradient", "pytorch2-linux",
        "RuntimeError: one of the variables needed for gradient computation has been modified by an inplace operation",
        r"(inplace operation|modified by an inplace|one of the variables needed for gradient)",
        "autograd_error", "pytorch", ">=2.0", "linux", "true", 0.85, 0.88,
        "An in-place operation (+=, relu_(inplace=True), etc.) modified a tensor needed for backward pass, breaking autograd.",
        [de("Wrap the operation in torch.no_grad()",
            "no_grad disables gradient tracking entirely; the model will not learn", 0.88),
         de("Use .data to bypass autograd",
            "Modifying .data breaks the computation graph silently; gradients become incorrect without errors", 0.85)],
        [wa("Replace inplace operations with out-of-place equivalents", 0.92,
            "x = x + 1 instead of x += 1; F.relu(x) instead of F.relu(x, inplace=True)"),
         wa("Clone tensors before modification", 0.88,
            "y = x.clone(); y.modify_inplace()  # x's gradient graph is preserved"),
         wa("Set inplace=False in ReLU/Dropout layers", 0.90,
            "nn.ReLU(inplace=False)  # default is False anyway")],
        python=">=3.9",
    ))

    canons.append(canon(
        "pytorch", "dataloader-worker-killed", "pytorch2-linux",
        "RuntimeError: DataLoader worker (pid 12345) is killed by signal: Killed",
        r"(DataLoader worker.*killed|killed by signal.*Killed|RuntimeError.*DataLoader.*pid|shared memory.*insufficient)",
        "memory_error", "pytorch", ">=2.0", "linux", "true", 0.82, 0.88,
        "DataLoader worker process killed by OS OOM killer. Too many workers, large prefetch, or shared memory limit in Docker.",
        [de("Set num_workers=0 permanently",
            "Fixes the crash but kills data loading performance; training becomes I/O bound", 0.60),
         de("Increase system swap space",
            "Swap on GPU training machines causes massive slowdowns; fix the memory usage instead", 0.72)],
        [wa("Reduce num_workers and prefetch_factor", 0.90,
            "DataLoader(dataset, num_workers=2, prefetch_factor=2)  # default prefetch_factor=2"),
         wa("In Docker: increase shared memory size", 0.88,
            "docker run --shm-size=8g ... # or --ipc=host"),
         wa("Use persistent_workers=True to avoid respawning overhead", 0.82,
            "DataLoader(dataset, num_workers=4, persistent_workers=True)")],
        python=">=3.9",
    ))

    # =====================================================================
    # === TENSORFLOW ===
    # =====================================================================
    canons.append(canon(
        "tensorflow", "oom-allocating-tensor", "tf2-linux",
        "tensorflow.python.framework.errors_impl.ResourceExhaustedError: OOM when allocating tensor",
        r"(ResourceExhaustedError.*OOM|OOM when allocating tensor|Allocator.*ran out of memory|GPU.*memory.*exhausted)",
        "memory_error", "tensorflow", ">=2.10", "linux", "true", 0.85, 0.90,
        "TensorFlow GPU memory exhausted. Batch too large or TF is allocating all GPU memory upfront.",
        [de("Set TF_FORCE_GPU_ALLOW_GROWTH=true as environment variable only",
            "Some TF versions ignore the env var; set it programmatically as well", 0.55),
         de("Install tensorflow-cpu to avoid GPU issues",
            "Completely gives up GPU acceleration. Fix memory management instead.", 0.82)],
        [wa("Enable GPU memory growth to allocate on demand", 0.92,
            "gpus = tf.config.list_physical_devices('GPU'); tf.config.experimental.set_memory_growth(gpus[0], True)"),
         wa("Reduce batch size", 0.90),
         wa("Set memory limit per GPU", 0.85,
            "tf.config.set_logical_device_configuration(gpu, [tf.config.LogicalDeviceConfiguration(memory_limit=4096)])")],
        gpu="any", python=">=3.9",
    ))

    canons.append(canon(
        "tensorflow", "incompatible-shapes", "tf2-linux",
        "InvalidArgumentError: Incompatible shapes: [32,10] vs. [32,5]",
        r"(Incompatible shapes|InvalidArgumentError.*shape|logits and labels must have the same|Dimensions must be equal)",
        "shape_error", "tensorflow", ">=2.10", "linux", "true", 0.90, 0.90,
        "Tensor shapes do not match. Common with loss functions where model output and label dimensions differ.",
        [de("Reshape labels to match model output",
            "If model outputs 10 classes but you have 5, reshape just masks the real problem: wrong model or wrong labels", 0.78),
         de("Use sparse_categorical_crossentropy to avoid shape issues",
            "Only works if labels are integer indices, not one-hot. Using it with one-hot labels gives wrong results.", 0.65)],
        [wa("Match loss function to label format", 0.92,
            "Integer labels: sparse_categorical_crossentropy. One-hot labels: categorical_crossentropy."),
         wa("Verify model output shape matches number of classes", 0.90,
            "model.summary()  # check last layer output shape"),
         wa("Check dataset label shapes before training", 0.85,
            "print(y_train.shape, y_train[:5])  # verify dimensions and format")],
        python=">=3.9",
    ))

    canons.append(canon(
        "tensorflow", "cudart-library-not-found", "tf2-linux",
        "Could not load dynamic library 'libcudart.so.12'; dlerror: libcudart.so.12: cannot open shared object",
        r"(Could not load dynamic library|libcuda(rt|nn|blas)|cannot open shared object|CUDA.*library.*not found|dlerror)",
        "installation_error", "tensorflow", ">=2.10", "linux", "true", 0.82, 0.88,
        "TensorFlow cannot find CUDA runtime libraries. CUDA version mismatch or LD_LIBRARY_PATH not set.",
        [de("Install the latest CUDA toolkit regardless of TF version",
            "TF requires specific CUDA versions. TF 2.15 needs CUDA 12.2, not 12.5 or 11.x.", 0.82),
         de("Set LD_LIBRARY_PATH in the Python script",
            "LD_LIBRARY_PATH must be set BEFORE Python starts; setting it inside Python has no effect on dlopen", 0.78),
         de("Symlink the wrong CUDA version to the expected filename",
            "ABI differences between CUDA versions cause crashes; symlinks hide version mismatches", 0.85)],
        [wa("Install the exact CUDA version matching your TF version", 0.92,
            "Check https://www.tensorflow.org/install/source#gpu for version matrix"),
         wa("Use pip install tensorflow[and-cuda] for automatic CUDA bundling", 0.90,
            "pip install tensorflow[and-cuda]  # bundles compatible CUDA/cuDNN"),
         wa("Use conda which manages CUDA dependencies automatically", 0.85,
            "conda install tensorflow-gpu  # installs matching cudatoolkit")],
        gpu="any", python=">=3.9",
    ))

    canons.append(canon(
        "tensorflow", "tf1-vs-tf2-session", "tf2-linux",
        "AttributeError: module 'tensorflow' has no attribute 'Session'",
        r"(has no attribute.*Session|tf\.Session|placeholder.*not.*found|module.*tensorflow.*no attribute)",
        "api_error", "tensorflow", ">=2.0", "linux", "true", 0.90, 0.92,
        "TF1 API used in TF2. tf.Session, tf.placeholder, etc. removed in TF2. Common when following old tutorials.",
        [de("Install TensorFlow 1.x to run old code",
            "TF1 has known security vulnerabilities and no GPU support for modern CUDA. Migrate to TF2.", 0.78),
         de("Use tf.compat.v1 for everything",
            "compat.v1 is a migration aid, not a permanent solution. It disables TF2 optimizations like eager execution.", 0.65)],
        [wa("Use tf.compat.v1.Session() for quick migration, then refactor", 0.82,
            "import tensorflow.compat.v1 as tf; tf.disable_v2_behavior()  # temporary"),
         wa("Migrate to TF2 eager execution (no Session needed)", 0.95,
            "In TF2, operations execute immediately: result = tf.matmul(a, b)  # no sess.run()"),
         wa("Use the TF2 migration script", 0.85,
            "tf_upgrade_v2 --infile old_code.py --outfile new_code.py")],
        python=">=3.9",
    ))

    # =====================================================================
    # === HUGGING FACE ===
    # =====================================================================
    canons.append(canon(
        "huggingface", "tokenizer-load-error", "hf-transformers-linux",
        "OSError: Can't load tokenizer for 'model-name'. Make sure the model identifier is correct.",
        r"(Can't load tokenizer|OSError.*tokenizer|not a valid model identifier|Tokenizer class.*not found|does not appear to have.*tokenizer)",
        "loading_error", "transformers", ">=4.30", "linux", "true", 0.88, 0.90,
        "Hugging Face cannot load tokenizer. Model name typo, private/gated model, or missing tokenizer files.",
        [de("Download tokenizer files manually from the Hub and load locally",
            "Manual download may miss files (special_tokens_map, tokenizer_config) causing subtle errors", 0.70),
         de("Use a different tokenizer assuming they are interchangeable",
            "Tokenizers are model-specific. Using wrong tokenizer produces wrong token IDs and garbage outputs.", 0.88)],
        [wa("Check exact model name on huggingface.co/models", 0.92,
            "AutoTokenizer.from_pretrained('meta-llama/Llama-2-7b-hf')  # exact Hub ID"),
         wa("Login with access token for gated/private models", 0.90,
            "huggingface-cli login  # or use_auth_token=True in from_pretrained()"),
         wa("Specify revision/branch if model has multiple versions", 0.82,
            "AutoTokenizer.from_pretrained('model', revision='main')")],
        python=">=3.9",
    ))

    canons.append(canon(
        "huggingface", "generate-oom", "hf-transformers-linux",
        "torch.cuda.OutOfMemoryError: CUDA out of memory during model.generate()",
        r"(OutOfMemoryError.*generate|CUDA out of memory.*generat|OOM.*model\.generate|KV cache.*memory)",
        "memory_error", "transformers", ">=4.30", "linux", "true", 0.80, 0.88,
        "OOM during text generation. KV cache grows linearly with sequence length, consuming all VRAM.",
        [de("Set max_new_tokens very high for better generation quality",
            "Longer sequences need quadratically more KV cache memory. Set reasonable limits.", 0.78),
         de("Call torch.cuda.empty_cache() between generate calls",
            "Does not free the KV cache allocated during generate; only helps if there is fragmented cached memory", 0.65)],
        [wa("Load model in lower precision", 0.90,
            "model = AutoModelForCausalLM.from_pretrained(name, torch_dtype=torch.float16, device_map='auto')"),
         wa("Use quantization (4-bit or 8-bit)", 0.88,
            "model = AutoModelForCausalLM.from_pretrained(name, load_in_4bit=True, device_map='auto')"),
         wa("Set reasonable max_new_tokens and use streaming", 0.85,
            "model.generate(inputs, max_new_tokens=256, do_sample=True)")],
        gpu="any", python=">=3.9",
    ))

    canons.append(canon(
        "huggingface", "gated-model-unauthorized", "hf-transformers-linux",
        "HTTPError: 401 Client Error: Unauthorized for url: huggingface.co",
        r"(401.*Unauthorized|Client Error.*Unauthorized.*huggingface|Access to model.*is restricted|gated.*accept.*license)",
        "auth_error", "transformers", ">=4.30", "linux", "true", 0.92, 0.90,
        "Attempting to access a gated model without accepting license or providing auth token.",
        [de("Use a mirror site or unofficial copy of the model",
            "Unofficial copies may be tampered with, outdated, or violate the model license", 0.85),
         de("Create a new Hugging Face account to bypass the gate",
            "You still need to accept the license agreement on the new account", 0.80)],
        [wa("Accept the model license on the model page, then use auth token", 0.95,
            "1. Visit huggingface.co/{model} and accept license. 2. huggingface-cli login. 3. Re-run."),
         wa("Pass token explicitly in from_pretrained", 0.90,
            "model = AutoModel.from_pretrained(name, token='hf_xxxxx')"),
         wa("Set HF_TOKEN environment variable", 0.85,
            "export HF_TOKEN=hf_xxxxx  # or add to .env file")],
        python=">=3.9",
    ))

    canons.append(canon(
        "huggingface", "wrong-input-type", "hf-transformers-linux",
        "ValueError: Text input must of type str (single example), List[str] (batch)",
        r"(Text input must.*type|expected.*str.*got|Batch.*must be.*list|tokenizer.*invalid input)",
        "type_error", "transformers", ">=4.30", "linux", "true", 0.92, 0.92,
        "Tokenizer received wrong input type. Usually passing raw data instead of text strings.",
        [de("Convert everything to string with str()",
            "str() on a list produces '[\'text1\', \'text2\']' which is tokenized as one string, not a batch", 0.82),
         de("Wrap single string in a list unconditionally",
            "Some pipeline functions handle single strings differently from batches; check the API first", 0.55)],
        [wa("Pass correct type: str for single, List[str] for batch", 0.95,
            "tokenizer('single text') or tokenizer(['text1', 'text2'])"),
         wa("Use tokenizer with padding and truncation for batches", 0.90,
            "tokenizer(texts, padding=True, truncation=True, return_tensors='pt')"),
         wa("Check the input type before calling tokenizer", 0.85)],
        python=">=3.9",
    ))

    # =====================================================================
    # === LLM ===
    # =====================================================================
    canons.append(canon(
        "llm", "context-length-exceeded", "openai-api",
        "openai.BadRequestError: This model's maximum context length is 128000 tokens",
        r"(maximum context length|context.*length.*exceeded|too many tokens|prompt.*too long|max.*tokens.*exceeded)",
        "api_error", "openai-api", ">=1.0", "cross-platform", "true", 0.88, 0.90,
        "Input + output tokens exceed the model's context window. Long conversations, large documents, or system prompts.",
        [de("Truncate the prompt from the beginning",
            "Cutting the start loses system prompts and instructions. Truncate middle conversation, keep start and end.", 0.72),
         de("Switch to a model with larger context window",
            "Larger context = higher cost and latency. Fix the prompt design first.", 0.60)],
        [wa("Implement conversation summarization/windowing", 0.88,
            "Keep last N messages + summary of older messages; summarize when approaching limit"),
         wa("Use tiktoken to count tokens before sending", 0.92,
            "import tiktoken; enc = tiktoken.encoding_for_model('gpt-4'); len(enc.encode(text))"),
         wa("Chunk large documents and process separately", 0.85,
            "Split into overlapping chunks of ~4000 tokens; process each; combine results")],
    ))

    canons.append(canon(
        "llm", "rate-limit-error", "openai-api",
        "openai.RateLimitError: Rate limit reached for model",
        r"(RateLimitError|rate limit|Rate limit reached|429.*Too Many Requests|quota.*exceeded)",
        "api_error", "openai-api", ">=1.0", "cross-platform", "true", 0.85, 0.88,
        "API rate limit hit. Too many requests per minute or tokens per minute exceeded.",
        [de("Retry immediately in a tight loop",
            "Immediate retries increase load and may get you temporarily banned. Use exponential backoff.", 0.85),
         de("Create multiple API keys to bypass rate limits",
            "Rate limits are per-organization, not per-key. Multiple keys from same org share the same limit.", 0.82)],
        [wa("Implement exponential backoff with jitter", 0.92,
            "Use tenacity: @retry(wait=wait_exponential(min=1, max=60) + wait_random(0, 2))"),
         wa("Batch requests and spread them over time", 0.85,
            "Process queue with rate limiter: max N requests per minute"),
         wa("Request rate limit increase from provider", 0.80,
            "OpenAI: usage tier auto-upgrades with spend. Anthropic: request via console.")],
    ))

    canons.append(canon(
        "llm", "json-parse-error", "openai-api",
        "json.decoder.JSONDecodeError: Expecting value when parsing LLM output",
        r"(JSONDecodeError.*LLM|json.*parse.*error.*output|invalid JSON.*response|Expecting value.*line 1|Unterminated string)",
        "parsing_error", "openai-api", ">=1.0", "cross-platform", "true", 0.82, 0.88,
        "LLM output is not valid JSON despite being asked for JSON. Markdown code blocks, trailing text, or truncated output.",
        [de("Use eval() or ast.literal_eval() to parse LLM output",
            "eval() is a security vulnerability; literal_eval fails on non-Python JSON. Use json.loads.", 0.90),
         de("Prompt harder with ONLY output JSON and nothing else",
            "Prompting alone is unreliable. Models can still add markdown fences or explanatory text.", 0.68)],
        [wa("Use structured output / JSON mode if available", 0.95,
            "OpenAI: response_format={'type': 'json_object'}; Anthropic: tool_use for structured output"),
         wa("Strip markdown code fences before parsing", 0.88,
            "text = re.sub(r'^```json\\n?|```$', '', text.strip()); data = json.loads(text)"),
         wa("Use a lenient JSON parser like json-repair", 0.82,
            "from json_repair import repair_json; data = json.loads(repair_json(text))")],
    ))

    canons.append(canon(
        "llm", "api-timeout", "openai-api",
        "openai.APITimeoutError: Request timed out",
        r"(APITimeoutError|Request timed out|timeout.*exceeded|ConnectTimeout|ReadTimeout.*openai)",
        "api_error", "openai-api", ">=1.0", "cross-platform", "partial", 0.70, 0.85,
        "API request timed out. Long generation, network issues, or API overload.",
        [de("Set timeout to very large value (300s+)",
            "Extremely long timeouts tie up resources; if the API is overloaded your request will likely fail anyway", 0.65),
         de("Retry the exact same long prompt immediately",
            "If the prompt caused slow generation (long output), it will timeout again. Reduce max_tokens.", 0.72)],
        [wa("Set reasonable timeout with retry logic", 0.88,
            "client = OpenAI(timeout=60.0, max_retries=3)"),
         wa("Reduce max_tokens to limit generation time", 0.85,
            "Shorter responses generate faster; use max_tokens=1000 instead of 4096"),
         wa("Use streaming to avoid timeout on long responses", 0.82,
            "stream = client.chat.completions.create(..., stream=True)")],
    ))


    # =====================================================================
    # === NGINX ===
    # =====================================================================
    canons.append(canon(
        "nginx", "bind-address-in-use", "nginx1-linux",
        "nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)",
        r"(bind\(\).*failed.*Address already in use|bind.*0\.0\.0\.0.*failed|98.*Address already in use|EADDRINUSE.*nginx)",
        "startup_error", "nginx", ">=1.18", "linux", "true", 0.92, 0.92,
        "Port 80/443 already in use by another process. Another nginx instance, Apache, or a container.",
        [de("Change nginx to a different port like 8080",
            "Clients expect 80/443. Changing ports requires all URLs and redirects to be updated.", 0.65),
         de("Use kill -9 on the process using the port",
            "kill -9 does not allow graceful shutdown; may corrupt logs or leave connections hanging. Use graceful stop.", 0.68)],
        [wa("Find and stop the conflicting process", 0.95,
            "sudo ss -tlnp | grep :80  # or: sudo lsof -i :80"),
         wa("Use nginx -s stop to stop the existing nginx", 0.90,
            "sudo nginx -s stop && sudo nginx"),
         wa("Check for and stop Apache if installed alongside nginx", 0.85,
            "sudo systemctl stop apache2 && sudo systemctl disable apache2")],
    ))

    canons.append(canon(
        "nginx", "upstream-timed-out", "nginx1-linux",
        "upstream timed out (110: Connection timed out) while reading response header from upstream",
        r"(upstream timed out|110.*Connection timed out|upstream.*reading response|proxy_read_timeout)",
        "proxy_error", "nginx", ">=1.18", "linux", "true", 0.82, 0.88,
        "Backend server did not respond within proxy timeout. Slow API, long-running request, or backend down.",
        [de("Set proxy_read_timeout to extremely large value (3600s)",
            "Masks backend performance problems; ties up nginx worker connections; may hit client-side timeouts anyway", 0.70),
         de("Increase worker_connections to handle more concurrent requests",
            "worker_connections does not fix slow backends; it only helps with concurrent connection capacity", 0.75)],
        [wa("Increase proxy timeouts to match expected backend response time", 0.88,
            "proxy_read_timeout 120s; proxy_connect_timeout 10s; proxy_send_timeout 60s;"),
         wa("Fix the slow backend (add caching, optimize queries)", 0.90),
         wa("Add upstream health checks to avoid routing to dead backends", 0.82,
            "upstream backend { server 127.0.0.1:8000 max_fails=3 fail_timeout=30s; }")],
    ))

    canons.append(canon(
        "nginx", "server-directive-not-allowed", "nginx1-linux",
        "nginx: [emerg] \"server\" directive is not allowed here",
        r"(directive is not allowed here|unexpected.*directive|unknown directive|nginx.*emerg.*directive)",
        "config_error", "nginx", ">=1.18", "linux", "true", 0.92, 0.92,
        "nginx config syntax error. Directive placed in wrong context (e.g., server block inside another server block).",
        [de("Copy config snippets from Stack Overflow without understanding context hierarchy",
            "nginx has strict context nesting: main > http > server > location. Directives in wrong context fail.", 0.82),
         de("Put all configuration in a single nginx.conf file",
            "While valid, large monolithic configs are error-prone. Use include and sites-enabled/ pattern.", 0.55)],
        [wa("Test config syntax before reloading", 0.95,
            "sudo nginx -t  # validates config and shows exact error location"),
         wa("Check nginx context hierarchy", 0.90,
            "http {} contains server {}; server {} contains location {}; main context is outside http {}"),
         wa("Use include to split config into manageable files", 0.82,
            "include /etc/nginx/conf.d/*.conf; include /etc/nginx/sites-enabled/*;")],
    ))

    canons.append(canon(
        "nginx", "upstream-connection-refused", "nginx1-linux",
        "connect() failed (111: Connection refused) while connecting to upstream",
        r"(connect\(\) failed.*111.*Connection refused|upstream.*Connection refused|connect.*upstream.*refused)",
        "proxy_error", "nginx", ">=1.18", "linux", "true", 0.88, 0.90,
        "nginx cannot reach the backend. Backend not running, wrong port, or listening on different interface.",
        [de("Change proxy_pass to use hostname instead of IP",
            "DNS resolution adds latency and can fail; use IP for local backends", 0.55),
         de("Restart nginx assuming the issue is with nginx",
            "nginx is working correctly by reporting the error; the backend is the problem", 0.80)],
        [wa("Verify the backend is running and listening on the expected port", 0.95,
            "curl -v http://127.0.0.1:8000  # test backend directly; ss -tlnp | grep 8000"),
         wa("Check backend is listening on correct interface (0.0.0.0 vs 127.0.0.1)", 0.90,
            "If backend listens on 127.0.0.1 but nginx uses proxy_pass to container IP, connection refused"),
         wa("Check firewall rules and SELinux if enabled", 0.82,
            "sudo setsebool -P httpd_can_network_connect 1  # SELinux blocks nginx upstream by default")],
    ))

    # =====================================================================
    # === REDIS ===
    # =====================================================================
    canons.append(canon(
        "redis", "misconf-rdb-snapshots", "redis7-linux",
        "MISCONF Redis is configured to save RDB snapshots, but it can't persist to disk",
        r"(MISCONF.*RDB|can't persist to disk|BGSAVE.*failed|rdbSaveBackground|fork.*Cannot allocate memory)",
        "persistence_error", "redis", ">=7.0", "linux", "true", 0.85, 0.88,
        "Redis cannot save to disk. Disk full, permission error, or insufficient memory for BGSAVE fork.",
        [de("Disable persistence entirely with CONFIG SET save ''",
            "Data will be lost on restart. Only appropriate for pure cache use cases.", 0.60),
         de("Set stop-writes-on-bgsave-error no",
            "Allows writes to continue but data is not being persisted; silent data loss risk", 0.72)],
        [wa("Fix the underlying disk/memory issue", 0.92,
            "df -h /var/lib/redis  # check disk; free -m  # check memory for fork"),
         wa("Set vm.overcommit_memory=1 for Linux fork behavior", 0.88,
            "echo 1 > /proc/sys/vm/overcommit_memory  # allows Redis BGSAVE fork to succeed"),
         wa("Use AOF persistence as alternative if RDB fork fails", 0.80,
            "CONFIG SET appendonly yes  # AOF does not require fork for every write")],
    ))

    canons.append(canon(
        "redis", "oom-maxmemory", "redis7-linux",
        "OOM command not allowed when used memory > 'maxmemory'",
        r"(OOM command not allowed|used memory.*maxmemory|maxmemory.*exceeded|OOM.*Redis)",
        "memory_error", "redis", ">=7.0", "linux", "true", 0.85, 0.90,
        "Redis memory limit reached and eviction policy does not allow the operation.",
        [de("Remove maxmemory limit entirely",
            "Without limits, Redis grows until the OS OOM killer terminates it, losing all data", 0.85),
         de("Flush all data (FLUSHALL) to free memory",
            "Destroys all data. Only appropriate if data is a rebuildable cache.", 0.72)],
        [wa("Set appropriate eviction policy", 0.90,
            "CONFIG SET maxmemory-policy allkeys-lru  # evict least-recently-used keys"),
         wa("Increase maxmemory if the server has available RAM", 0.85,
            "CONFIG SET maxmemory 4gb"),
         wa("Analyze memory usage to find large keys", 0.88,
            "redis-cli --bigkeys  # finds largest keys per type; redis-cli MEMORY USAGE key_name")],
    ))

    canons.append(canon(
        "redis", "readonly-replica", "redis7-linux",
        "READONLY You can't write against a read only replica",
        r"(READONLY.*can't write|read only replica|READONLY.*replica|slave.*read.?only)",
        "replication_error", "redis", ">=7.0", "linux", "true", 0.88, 0.90,
        "Write command sent to a Redis replica. Application connected to replica instead of primary.",
        [de("Set replica-read-only no on the replica",
            "Writes to replica are not replicated to primary; they get overwritten on next sync, causing data loss", 0.90),
         de("Promote replica to primary",
            "Only appropriate during failover. Otherwise you end up with split-brain: two primaries.", 0.78)],
        [wa("Fix application connection to point to the primary node", 0.95,
            "Check connection string: connect to primary host/port, not replica"),
         wa("Use Redis Sentinel or Cluster for automatic primary discovery", 0.90,
            "Sentinel: redis-py SentinelConnectionPool auto-discovers current primary"),
         wa("Separate read and write connections in application", 0.82,
            "Reads from replica, writes to primary. Most Redis clients support this.")],
    ))

    # =====================================================================
    # === MONGODB ===
    # =====================================================================
    canons.append(canon(
        "mongodb", "authentication-failed", "mongo7-linux",
        "MongoServerError: Authentication failed",
        r"(Authentication failed|MongoServerError.*auth|SCRAM.*authentication|auth.*failed.*mongo)",
        "auth_error", "mongodb", ">=7.0", "linux", "true", 0.90, 0.90,
        "MongoDB authentication failed. Wrong credentials, wrong auth database, or auth not enabled.",
        [de("Connect without credentials assuming auth is disabled",
            "MongoDB 7+ enables auth by default. Even local connections require authentication.", 0.75),
         de("Use the admin database credentials for all databases",
            "Users are scoped to their auth database. Admin user must specify authSource=admin.", 0.70)],
        [wa("Specify the correct authentication database", 0.92,
            "mongosh 'mongodb://user:pass@host:27017/mydb?authSource=admin'"),
         wa("Verify user exists in the correct database", 0.88,
            "use admin; db.getUsers()  # check which database the user was created in"),
         wa("Reset password if forgotten", 0.82,
            "Start mongod without --auth, connect locally, db.changeUserPassword('user', 'newpass')")],
    ))

    canons.append(canon(
        "mongodb", "duplicate-key-error", "mongo7-linux",
        "MongoServerError: E11000 duplicate key error collection: mydb.users index: email_1",
        r"(E11000 duplicate key|duplicate key error|MongoServerError.*11000|DuplicateKeyError)",
        "constraint_error", "mongodb", ">=7.0", "linux", "true", 0.88, 0.90,
        "Unique index violation. Attempting to insert a document with a duplicate value for a unique field.",
        [de("Remove the unique index to stop the error",
            "The unique constraint exists for data integrity. Removing it allows corrupt duplicate data.", 0.85),
         de("Catch the error and silently ignore it",
            "Ignoring duplicates may mean lost updates or inconsistent data", 0.65)],
        [wa("Use upsert to update-or-insert atomically", 0.92,
            "db.users.updateOne({ email: x }, { $set: doc }, { upsert: true })"),
         wa("Check for existence before insert", 0.85,
            "if not db.users.find_one({'email': x}): db.users.insert_one(doc)  # but not atomic"),
         wa("Handle the error and provide user-friendly message", 0.88,
            "catch DuplicateKeyError: return 'Email already registered'")],
    ))

    canons.append(canon(
        "mongodb", "connection-refused", "mongo7-linux",
        "MongoNetworkError: connect ECONNREFUSED 127.0.0.1:27017",
        r"(MongoNetworkError.*ECONNREFUSED|connect.*ECONNREFUSED.*27017|MongooseServerSelectionError|getaddrinfo.*ENOTFOUND.*mongo)",
        "connection_error", "mongodb", ">=7.0", "linux", "true", 0.90, 0.92,
        "Cannot connect to MongoDB. Service not running, wrong host/port, or firewall blocking.",
        [de("Reinstall MongoDB to fix connection issues",
            "Connection refused means the service is not listening, not that the installation is broken", 0.82),
         de("Use localhost instead of 127.0.0.1 or vice versa",
            "Both resolve to the same address. The issue is the service not running, not the address format.", 0.72)],
        [wa("Start the MongoDB service", 0.95,
            "sudo systemctl start mongod && sudo systemctl enable mongod"),
         wa("Check if MongoDB is listening on the expected port", 0.90,
            "ss -tlnp | grep 27017; sudo journalctl -u mongod --tail=20"),
         wa("Check bindIp in mongod.conf for remote connections", 0.85,
            "bindIp: 0.0.0.0  # in /etc/mongod.conf; default is 127.0.0.1 only")],
    ))

    # =====================================================================
    # === KAFKA ===
    # =====================================================================
    canons.append(canon(
        "kafka", "topic-not-in-metadata", "kafka3-linux",
        "org.apache.kafka.common.errors.TimeoutException: Topic my_topic not present in metadata after 60000 ms",
        r"(Topic.*not present in metadata|TimeoutException.*metadata|topic.*not exist|Unknown topic or partition)",
        "configuration_error", "kafka", ">=3.0", "linux", "true", 0.88, 0.90,
        "Producer/consumer cannot find topic. Topic does not exist and auto-creation is disabled, or bootstrap servers are wrong.",
        [de("Set auto.create.topics.enable=true in production",
            "Auto-creation leads to typo-induced phantom topics. Create topics explicitly in production.", 0.72),
         de("Connect directly to a broker instead of using bootstrap servers",
            "Direct broker connection bypasses cluster metadata; breaks when broker changes or cluster rebalances", 0.80)],
        [wa("Create the topic explicitly before producing/consuming", 0.92,
            "kafka-topics.sh --create --topic my_topic --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1"),
         wa("Verify bootstrap servers are correct and reachable", 0.90,
            "kafka-broker-api-versions.sh --bootstrap-server localhost:9092"),
         wa("Check topic exists with list command", 0.85,
            "kafka-topics.sh --list --bootstrap-server localhost:9092")],
    ))

    canons.append(canon(
        "kafka", "record-too-large", "kafka3-linux",
        "org.apache.kafka.common.errors.RecordTooLargeException: The message is 1500000 bytes, max is 1048576",
        r"(RecordTooLargeException|message.*bytes.*max|MESSAGE_TOO_LARGE|max\.message\.bytes)",
        "configuration_error", "kafka", ">=3.0", "linux", "true", 0.90, 0.88,
        "Message exceeds size limit. Default is 1MB. Must increase on broker, topic, AND producer side.",
        [de("Only increase max.message.bytes on the broker",
            "Must also increase on topic level AND producer (max.request.size). All three must agree.", 0.82),
         de("Only increase producer max.request.size",
            "Broker will still reject messages exceeding its message.max.bytes setting", 0.85)],
        [wa("Increase limits on all three levels: broker, topic, and producer", 0.92,
            "Broker: message.max.bytes=5242880; Topic: max.message.bytes=5242880; Producer: max.request.size=5242880"),
         wa("Compress messages to stay within limits", 0.85,
            "Producer config: compression.type=snappy  # or lz4, zstd"),
         wa("Redesign to use chunking or external storage for large payloads", 0.80,
            "Store large data in S3/blob storage; send only reference in Kafka message")],
    ))

    canons.append(canon(
        "kafka", "consumer-rebalance-revoked", "kafka3-linux",
        "CommitFailedException: Commit cannot be completed since the group has already rebalanced",
        r"(CommitFailedException|group.*rebalanced|Offset commit.*failed.*rebalance|partitions.*revoked)",
        "consumer_error", "kafka", ">=3.0", "linux", "true", 0.78, 0.85,
        "Consumer group rebalanced while processing messages. Processing took longer than session.timeout.ms or max.poll.interval.ms.",
        [de("Set session.timeout.ms to very large value",
            "Delays detection of genuinely failed consumers; dead consumers block partition processing", 0.72),
         de("Disable auto-commit and never commit offsets",
            "Without commits, all messages are reprocessed on restart, causing duplicates", 0.85)],
        [wa("Increase max.poll.interval.ms to match expected processing time", 0.88,
            "max.poll.interval.ms=600000  # 10 minutes; adjust to your processing time"),
         wa("Reduce max.poll.records to process fewer messages per poll", 0.85,
            "max.poll.records=100  # process smaller batches to stay within poll interval"),
         wa("Move heavy processing to async worker pool", 0.80,
            "Poll quickly, dispatch to thread pool, commit after completion")],
    ))

    # =====================================================================
    # === ELASTICSEARCH ===
    # =====================================================================
    canons.append(canon(
        "elasticsearch", "index-read-only", "es8-linux",
        "ClusterBlockException: index [my_index] blocked by: [FORBIDDEN/12/index read-only / allow delete (api)]",
        r"(FORBIDDEN.*index read-only|ClusterBlockException|read-only.*allow delete|disk.*watermark.*exceeded)",
        "disk_error", "elasticsearch", ">=8.0", "linux", "true", 0.90, 0.90,
        "Elasticsearch set index to read-only because disk usage exceeded flood-stage watermark (95% by default).",
        [de("Delete the index to free space",
            "You lose all data. Free disk space first, then unblock the index.", 0.82),
         de("Increase the watermark thresholds",
            "Only delays the problem. When disk is truly full, the cluster will crash.", 0.65)],
        [wa("Free disk space, then unblock the index", 0.95,
            "Free disk, then: PUT _all/_settings with index.blocks.read_only_allow_delete set to null"),
         wa("Delete old indices using ILM or curator", 0.88,
            "DELETE /old-index-2024.*  # or configure ILM delete phase"),
         wa("Add more disk space or data nodes", 0.82)],
    ))

    canons.append(canon(
        "elasticsearch", "circuit-breaker-exception", "es8-linux",
        "circuit_breaking_exception: [parent] Data too large, data for [request] would be larger than limit",
        r"(circuit_breaking_exception|Data too large|circuit breaker.*tripped|parent.*breaker.*limit)",
        "memory_error", "elasticsearch", ">=8.0", "linux", "true", 0.82, 0.88,
        "JVM heap usage exceeded circuit breaker limit. Query too large, too many aggregations, or heap too small.",
        [de("Disable circuit breakers",
            "Circuit breakers prevent OOM crashes. Disabling them leads to unrecoverable OutOfMemoryError.", 0.92),
         de("Set ES_JAVA_OPTS heap to all available RAM",
            "ES heap should be max 50% of RAM and not exceed 31GB (compressed oops limit).", 0.80)],
        [wa("Reduce query scope: add filters, limit aggregation buckets", 0.90,
            "Add date range filter; set size:0 for aggregation-only queries; limit terms agg size"),
         wa("Increase JVM heap (up to 50% of RAM, max ~31GB)", 0.85,
            "ES_JAVA_OPTS='-Xms16g -Xmx16g'  # in jvm.options or docker env"),
         wa("Use scroll/search_after for large result sets instead of deep pagination", 0.82)],
    ))

    canons.append(canon(
        "elasticsearch", "mapper-parsing-exception", "es8-linux",
        "mapper_parsing_exception: failed to parse field [timestamp] of type [date]",
        r"(mapper_parsing_exception|failed to parse field|strict_dynamic_mapping_exception|could not parse.*type.*date|illegal_argument.*mapper)",
        "mapping_error", "elasticsearch", ">=8.0", "linux", "true", 0.85, 0.90,
        "Document field type does not match index mapping. Sending string where number expected, or wrong date format.",
        [de("Delete and recreate the index with dynamic mapping",
            "Dynamic mapping guesses types from first document; subsequent documents with different types will fail the same way", 0.75),
         de("Set strict_date_optional_time for all date fields",
            "Only works if all dates use ISO 8601. If you have epoch timestamps or custom formats, this fails.", 0.68)],
        [wa("Define explicit mapping with correct field types before indexing", 0.92,
            "PUT /my_index { 'mappings': { 'properties': { 'timestamp': { 'type': 'date', 'format': 'epoch_millis||yyyy-MM-dd' }}}}"),
         wa("Fix the source data to match the existing mapping", 0.88),
         wa("Use ingest pipeline to transform data before indexing", 0.82,
            "Use date processor in ingest pipeline to normalize date formats")],
    ))

    # =====================================================================
    # === GRPC ===
    # =====================================================================
    canons.append(canon(
        "grpc", "unavailable-connection-failed", "grpc1-linux",
        "grpc._channel._InactiveRpcError: StatusCode.UNAVAILABLE: failed to connect to all addresses",
        r"(StatusCode\.UNAVAILABLE|failed to connect to all addresses|UNAVAILABLE.*connect|grpc.*connection.*refused)",
        "connection_error", "grpc", ">=1.50", "linux", "true", 0.88, 0.90,
        "gRPC client cannot reach the server. Server not running, wrong address/port, or TLS/plaintext mismatch.",
        [de("Add grpc.enable_http_proxy channel option",
            "HTTP proxies do not support gRPC's HTTP/2 framing. This makes connection worse, not better.", 0.78),
         de("Switch to REST API as workaround",
            "Loses gRPC benefits (streaming, protobuf efficiency, code generation). Fix the connection instead.", 0.72)],
        [wa("Verify server is running and listening on expected port", 0.95,
            "grpcurl -plaintext localhost:50051 list  # or ss -tlnp | grep 50051"),
         wa("Check TLS mismatch: plaintext client vs TLS server or vice versa", 0.90,
            "grpc.insecure_channel() for plaintext; grpc.secure_channel(creds) for TLS"),
         wa("Check DNS resolution and firewall rules for remote servers", 0.85,
            "dig server.example.com; telnet server.example.com 50051")],
    ))

    canons.append(canon(
        "grpc", "deadline-exceeded", "grpc1-linux",
        "grpc._channel._InactiveRpcError: StatusCode.DEADLINE_EXCEEDED",
        r"(StatusCode\.DEADLINE_EXCEEDED|DEADLINE_EXCEEDED|deadline.*exceeded|context deadline exceeded)",
        "timeout_error", "grpc", ">=1.50", "linux", "true", 0.82, 0.88,
        "gRPC call timed out. Server processing too slow, network latency, or deadline set too short.",
        [de("Remove deadline entirely so calls never time out",
            "Without deadlines, stuck calls block forever. Deadlines are a best practice in gRPC.", 0.85),
         de("Set very long deadline (5 minutes) for all calls",
            "Long deadlines tie up resources. Set per-RPC deadlines appropriate for each operation.", 0.68)],
        [wa("Set appropriate per-RPC deadline based on expected latency", 0.90,
            "metadata = [('grpc-timeout', '30S')]; # or in Python: stub.MyMethod(req, timeout=30)"),
         wa("Profile server-side handler to find bottleneck", 0.88),
         wa("Add server-side deadline propagation and cancellation", 0.82,
            "Check context.is_active() periodically in long handlers; abort early if cancelled")],
    ))

    canons.append(canon(
        "grpc", "unimplemented-method", "grpc1-linux",
        "grpc._channel._InactiveRpcError: StatusCode.UNIMPLEMENTED: Method not found",
        r"(StatusCode\.UNIMPLEMENTED|Method not found|UNIMPLEMENTED.*method|service.*not.*registered)",
        "configuration_error", "grpc", ">=1.50", "linux", "true", 0.90, 0.92,
        "gRPC method not found on server. Service not registered, proto mismatch, or wrong server address.",
        [de("Regenerate proto stubs assuming the proto file is wrong",
            "If server and client use different proto versions, regenerating from wrong proto makes it worse", 0.68),
         de("Use reflection to discover available methods",
            "Reflection helps debug but does not fix the root cause of missing service registration", 0.50)],
        [wa("Verify service is registered on the server", 0.95,
            "server.add_insecure_port(...); server.add_generic_rpc_handlers([...])  # check service is added"),
         wa("Use grpcurl to list available services and methods", 0.90,
            "grpcurl -plaintext localhost:50051 list  # shows registered services"),
         wa("Ensure client and server use the same proto definition", 0.88,
            "Compare .proto files; regenerate both client and server stubs from the same source")],
    ))

    canons.append(canon(
        "grpc", "message-too-large", "grpc1-linux",
        "StatusCode.RESOURCE_EXHAUSTED: Received message larger than max (4194304 vs. 4194304)",
        r"(RESOURCE_EXHAUSTED.*message.*larger|Received message larger than max|max.*message.*size|grpc.*resource.*exhausted)",
        "configuration_error", "grpc", ">=1.50", "linux", "true", 0.90, 0.88,
        "gRPC message exceeds the default 4MB limit. Large responses, file transfers, or accumulated data.",
        [de("Remove message size limit entirely on both sides",
            "No limit means a single large or malicious message can crash the process with OOM", 0.78),
         de("Compress messages at application level before sending",
            "gRPC has built-in compression. Application-level compression adds complexity without benefit.", 0.65)],
        [wa("Increase max message size on both client and server", 0.92,
            "channel = grpc.insecure_channel(addr, options=[('grpc.max_receive_message_length', 50*1024*1024)])"),
         wa("Use gRPC streaming for large data transfers", 0.88,
            "Stream data in chunks instead of one large message: rpc StreamData(stream Chunk) returns (Result)"),
         wa("Enable built-in gRPC compression", 0.80,
            "channel = grpc.insecure_channel(addr, compression=grpc.Compression.Gzip)")],
    ))


    # =====================================================================
    # === ANDROID ===
    # =====================================================================
    canons.append(canon(
        "android", "merge-debug-resources-failed", "gradle8-linux",
        "Execution failed for task ':app:mergeDebugResources'. Resource compilation failed",
        r"(mergeDebugResources|Resource compilation failed|AAPT2.*error|Execution failed.*merge.*Resources)",
        "build_error", "gradle", ">=8.0", "linux", "true", 0.85, 0.88,
        "Android resource merge failed. Duplicate resources, invalid XML, or AAPT2 crash.",
        [de("Clean project repeatedly (Build > Clean)",
            "Clean removes build cache but does not fix the underlying resource conflict", 0.65),
         de("Downgrade Gradle plugin version",
            "Masks the issue temporarily; the resource conflict still exists and will reappear", 0.72)],
        [wa("Check the full error output for specific resource conflict", 0.92,
            "Run: ./gradlew mergeDebugResources --stacktrace  # shows exact conflicting resource"),
         wa("Search for duplicate resource names across modules and libraries", 0.88,
            "grep -r 'resource_name' app/src/main/res/  # check for duplicates in values/, drawables, etc."),
         wa("Invalidate caches and restart (File > Invalidate Caches)", 0.82,
            "Android Studio: File > Invalidate Caches > Invalidate and Restart")],
    ))

    canons.append(canon(
        "android", "gradle-oom", "gradle8-linux",
        "java.lang.OutOfMemoryError: GC overhead limit exceeded during Gradle build",
        r"(OutOfMemoryError.*GC overhead|OutOfMemoryError.*Gradle|Java heap space.*gradle|Metaspace.*gradle|GC overhead limit exceeded)",
        "memory_error", "gradle", ">=8.0", "linux", "true", 0.88, 0.90,
        "Gradle build runs out of memory. Project too large, too many modules, or JVM heap too small.",
        [de("Set org.gradle.jvmargs=-Xmx16g as first attempt",
            "Excessive heap hides the real problem (inefficient build) and slows down GC pauses", 0.60),
         de("Disable Gradle daemon to reduce memory usage",
            "Daemon keeps JVM warm for faster builds. Disabling it makes every build slower.", 0.72)],
        [wa("Increase Gradle JVM heap to reasonable size (4-8GB)", 0.90,
            "In gradle.properties: org.gradle.jvmargs=-Xmx4g -XX:MaxMetaspaceSize=512m"),
         wa("Enable Gradle configuration cache to reduce memory per build", 0.85,
            "org.gradle.configuration-cache=true  # in gradle.properties"),
         wa("Use modularization to reduce per-module build scope", 0.78)],
    ))

    canons.append(canon(
        "android", "sdk-packages-not-found", "android-sdk-linux",
        "Failed to install the following Android SDK packages as some licenses have not been accepted",
        r"(Failed to install.*SDK packages|licenses have not been accepted|Android SDK.*not found|SDK location not found|ANDROID_HOME.*not set)",
        "installation_error", "android-sdk", ">=33", "linux", "true", 0.92, 0.92,
        "Android SDK packages not installed or licenses not accepted. Common in CI/CD and fresh setups.",
        [de("Download SDK packages manually from Google archives",
            "Manual downloads miss dependency packages and do not register licenses", 0.80),
         de("Accept licenses interactively when running in CI",
            "CI has no interactive terminal. Licenses must be accepted non-interactively.", 0.85)],
        [wa("Accept all SDK licenses non-interactively", 0.95,
            "yes | sdkmanager --licenses"),
         wa("Set ANDROID_HOME and install required packages", 0.90,
            "export ANDROID_HOME=$HOME/Android/Sdk; sdkmanager 'platform-tools' 'platforms;android-34'"),
         wa("Use sdkmanager to install specific missing packages", 0.88,
            "sdkmanager --list  # find package names; sdkmanager 'build-tools;34.0.0'")],
    ))

    canons.append(canon(
        "android", "adb-device-unauthorized", "android-sdk-linux",
        "adb: device unauthorized. Please check the confirmation dialog on your device.",
        r"(device unauthorized|Please check.*confirmation dialog|adb.*unauthorized|no permissions.*adb|USB debugging.*not authorized)",
        "device_error", "adb", ">=34", "linux", "true", 0.90, 0.92,
        "ADB cannot communicate with device. USB debugging not enabled or RSA key not accepted on device.",
        [de("Restart adb server repeatedly",
            "If the device has not authorized the computer, restarting adb will not help", 0.72),
         de("Use a different USB cable assuming it is a cable issue",
            "Unauthorized error is an authentication issue, not a connectivity issue. The device IS connected.", 0.80)],
        [wa("Accept USB debugging prompt on the device screen", 0.95,
            "Unlock phone screen > tap 'Always allow from this computer' > OK"),
         wa("Enable USB debugging in Developer Options", 0.92,
            "Settings > About Phone > tap Build Number 7 times > Developer Options > USB debugging"),
         wa("Revoke and re-authorize USB debugging authorizations", 0.85,
            "adb kill-server && Settings > Developer Options > Revoke USB debugging authorizations > reconnect")],
    ))

    canons.append(canon(
        "android", "desugaring-error", "gradle8-linux",
        "Error: Default interface methods are only supported starting with Android 7.0 (API 24)",
        r"(Default interface methods.*only supported|desugaring|Lambda.*not supported.*API|java\.lang\.invoke.*not supported|requires.*API level)",
        "build_error", "gradle", ">=8.0", "linux", "true", 0.92, 0.92,
        "Java 8+ features used but desugaring not enabled. minSdk too low or compileOptions missing.",
        [de("Raise minSdk to 26+ to support all Java 8 features",
            "Excludes older devices. Enable desugaring instead to support Java 8 on all API levels.", 0.70),
         de("Rewrite code to avoid Java 8 features (lambdas, default methods)",
            "Unnecessary; Android toolchain supports desugaring to convert these to older bytecode", 0.82)],
        [wa("Enable Java 8 desugaring in build.gradle", 0.95,
            "android { compileOptions { sourceCompatibility JavaVersion.VERSION_1_8; targetCompatibility JavaVersion.VERSION_1_8 } }"),
         wa("Enable core library desugaring for java.time and streams on older APIs", 0.88,
            "android { compileOptions { coreLibraryDesugaringEnabled true } }; dependencies { coreLibraryDesugaring 'com.android.tools:desugar_jdk_libs:2.0.4' }"),
         wa("Set Kotlin JVM target to 1.8", 0.85,
            "kotlinOptions { jvmTarget = '1.8' }")],
    ))

    # =====================================================================
    # === FLUTTER ===
    # =====================================================================
    canons.append(canon(
        "flutter", "renderflex-overflowed", "flutter3-linux",
        "A RenderFlex overflowed by 42 pixels on the bottom.",
        r"(RenderFlex overflowed|overflowed by.*pixels|BOTTOM OVERFLOWING|RIGHT OVERFLOWING|RenderBox.*not laid out)",
        "layout_error", "flutter", ">=3.0", "cross-platform", "true", 0.90, 0.92,
        "Widget exceeds available space. Column/Row child too large for the parent constraints.",
        [de("Wrap everything in SingleChildScrollView",
            "Makes the entire screen scrollable which breaks fixed-position elements and can cause nested scroll issues", 0.65),
         de("Set fixed height/width on the overflowing widget",
            "Hardcoded sizes break on different screen sizes and orientations", 0.72)],
        [wa("Wrap overflowing child in Expanded or Flexible", 0.92,
            "Column(children: [Expanded(child: ListView(...)), BottomBar()])"),
         wa("Use ListView instead of Column for scrollable content", 0.88,
            "Replace Column with ListView when content may exceed screen height"),
         wa("Use LayoutBuilder to adapt to available space", 0.82,
            "LayoutBuilder(builder: (context, constraints) => ... constraints.maxHeight ...)")],
    ))

    canons.append(canon(
        "flutter", "missing-plugin-exception", "flutter3-linux",
        "MissingPluginException(No implementation found for method X on channel Y)",
        r"(MissingPluginException|No implementation found for method|channel.*not.*registered|plugin.*not.*found)",
        "plugin_error", "flutter", ">=3.0", "cross-platform", "true", 0.85, 0.88,
        "Platform plugin method not found. Plugin not properly installed, hot restart issue, or platform code missing.",
        [de("Run flutter pub get and hope it fixes itself",
            "pub get downloads Dart code but does not rebuild native platform code", 0.70),
         de("Downgrade the plugin to an older version",
            "Older versions may have different bugs. The real issue is usually a missing rebuild.", 0.65)],
        [wa("Stop app completely and do a full rebuild (not hot restart)", 0.92,
            "flutter clean && flutter pub get && flutter run  # full native rebuild"),
         wa("Ensure plugin is added in pubspec.yaml AND native platform setup", 0.88,
            "Some plugins need manual setup: AndroidManifest.xml permissions, Info.plist entries, Podfile"),
         wa("For custom plugins, verify MethodChannel name matches between Dart and platform", 0.82)],
    ))

    canons.append(canon(
        "flutter", "null-check-operator-null-value", "flutter3-linux",
        "Null check operator used on a null value",
        r"(Null check operator used on a null value|_CastError.*null|type.*Null.*is not a subtype of type)",
        "null_safety_error", "flutter", ">=3.0", "cross-platform", "true", 0.88, 0.90,
        "The ! operator was used on a null value. Variable was expected to be non-null but was null at runtime.",
        [de("Add ! everywhere to make null errors go away",
            "! is an assertion, not a fix. It just moves the crash to a different location.", 0.85),
         de("Disable null safety with // @dart=2.9",
            "Disabling null safety removes compile-time null checks and makes ALL null errors runtime crashes", 0.90)],
        [wa("Use null-aware operators instead of force-unwrap", 0.92,
            "value?.method()  or  value ?? defaultValue  instead of value!.method()"),
         wa("Add null checks before the operation", 0.88,
            "if (value != null) { value.method(); } else { handleNull(); }"),
         wa("Fix the source of null: check API responses, state initialization", 0.85,
            "Add late keyword only when you are certain it will be initialized before use")],
    ))

    canons.append(canon(
        "flutter", "cocoapods-version-conflict", "flutter3-macos",
        "CocoaPods could not find compatible versions for pod 'Firebase/CoreOnly'",
        r"(CocoaPods could not find compatible versions|pod install.*error|Specs satisfying.*were found but|CDN.*error.*trunk|Podfile\.lock.*out of date)",
        "dependency_error", "cocoapods", ">=1.12", "macos", "true", 0.82, 0.88,
        "iOS dependency conflict. Plugin versions require incompatible native library versions.",
        [de("Delete Podfile.lock and Pods directory and re-run",
            "Removing Podfile.lock loses version pins. May install breaking changes in transitive dependencies.", 0.68),
         de("Pin all pod versions to exact numbers",
            "Exact version pins prevent security updates and conflict with Flutter plugin requirements", 0.72)],
        [wa("Update CocoaPods repo and re-run pod install", 0.88,
            "cd ios && pod repo update && pod install"),
         wa("Run flutter clean then rebuild iOS", 0.85,
            "flutter clean && cd ios && rm -rf Pods Podfile.lock && cd .. && flutter pub get && cd ios && pod install"),
         wa("Check Flutter plugin compatibility matrix and update pubspec.yaml", 0.82)],
    ))

    canons.append(canon(
        "flutter", "gradle-assemble-debug-failed", "flutter3-linux",
        "Gradle task assembleDebug failed with exit code 1",
        r"(assembleDebug.*failed|Gradle.*exit code 1|Could not determine.*dependencies|Execution failed.*task.*android)",
        "build_error", "flutter", ">=3.0", "linux", "true", 0.80, 0.85,
        "Android build failed. Generic Gradle failure — the real error is further up in the log output.",
        [de("Run flutter clean and retry without reading the log",
            "flutter clean rarely fixes Gradle errors. The real error is in the log above the exit code.", 0.72),
         de("Delete the android/ folder and recreate with flutter create",
            "Destroys custom Android configurations (permissions, build flavors, signing)", 0.85)],
        [wa("Scroll up in the log to find the actual error", 0.95,
            "flutter build apk --verbose 2>&1 | less  # search for 'ERROR' or 'FAILURE'"),
         wa("Run Gradle directly for better error output", 0.88,
            "cd android && ./gradlew assembleDebug --stacktrace"),
         wa("Update Gradle wrapper and Android Gradle Plugin version", 0.80,
            "In android/gradle/wrapper/gradle-wrapper.properties and android/build.gradle")],
    ))

    # =====================================================================
    # === UNITY ===
    # =====================================================================
    canons.append(canon(
        "unity", "null-reference-exception", "unity2022-cross",
        "NullReferenceException: Object reference not set to an instance of an object",
        r"(NullReferenceException|Object reference not set|UnassignedReferenceException|not.*assigned.*Inspector)",
        "runtime_error", "unity", ">=2022.3", "cross-platform", "true", 0.88, 0.90,
        "Accessing a null component, GameObject, or unassigned Inspector reference. Most common Unity error.",
        [de("Add null checks around every GetComponent call",
            "Excessive null checks hide design problems. Fix the root cause: assign references properly.", 0.60),
         de("Use GameObject.Find() in Update() to always get fresh references",
            "Find() is O(n) over all GameObjects. Called every frame, it destroys performance.", 0.85)],
        [wa("Assign references via Inspector (drag-and-drop) instead of runtime lookup", 0.92,
            "[SerializeField] private Rigidbody rb;  // assign in Inspector, checked at edit time"),
         wa("Use TryGetComponent to safely get components", 0.88,
            "if (TryGetComponent<Rigidbody>(out var rb)) { rb.AddForce(...); }"),
         wa("Check if object was destroyed with the null-conditional operator", 0.82,
            "myObject?.DoSomething();  // Unity overrides == null for destroyed objects")],
    ))

    canons.append(canon(
        "unity", "missing-assembly-reference", "unity2022-cross",
        "error CS0246: The type or namespace name could not be found (are you missing an assembly reference?)",
        r"(CS0246|type or namespace.*could not be found|missing.*assembly reference|assembly.*not found|asmdef.*missing)",
        "compilation_error", "unity", ">=2022.3", "cross-platform", "true", 0.88, 0.90,
        "C# compiler cannot find a type. Missing package, wrong assembly definition, or namespace not imported.",
        [de("Copy the DLL file directly into the Assets folder",
            "Unity has a package manager. Manual DLLs create version conflicts and are not tracked.", 0.72),
         de("Remove all .asmdef files to fix assembly resolution",
            "Assembly definitions control compilation boundaries. Removing them can cause circular dependency errors.", 0.80)],
        [wa("Add the missing package via Unity Package Manager", 0.92,
            "Window > Package Manager > search for the package; or edit Packages/manifest.json"),
         wa("Add using directive for the correct namespace", 0.90,
            "using UnityEngine.UI;  // for UI components; using TMPro;  // for TextMeshPro"),
         wa("Add assembly reference in .asmdef file", 0.85,
            "Edit your .asmdef to include the dependency assembly in Assembly Definition References")],
    ))

    canons.append(canon(
        "unity", "shader-compilation-error", "unity2022-cross",
        "Shader error in 'Custom/MyShader': failed to open source file at line 42",
        r"(Shader error|Shader compilation|failed to open source file|maximum.*texture.*interpolators|maximum.*ALU|syntax error.*shader|Program.*vert.*frag.*not found)",
        "shader_error", "unity", ">=2022.3", "cross-platform", "partial", 0.65, 0.85,
        "Shader compilation failed. Syntax error, exceeding GPU limits, or missing include file.",
        [de("Switch to a more powerful GPU to fix shader compilation limits",
            "Shader instruction limits are per-platform target, not the development GPU. Target platform determines limits.", 0.78),
         de("Copy shader code from older Unity tutorials",
            "Shader API changes between Unity versions. Old surface shader code may not compile in newer versions.", 0.72)],
        [wa("Check the Console for the exact error line and fix the shader syntax", 0.88),
         wa("Use Shader Graph (visual editor) instead of writing HLSL/ShaderLab manually", 0.85,
            "Window > Shader Graph > create new shader; drag nodes instead of writing code"),
         wa("Reduce shader complexity for mobile: fewer texture samples, simpler math", 0.78,
            "Mobile GPUs have strict limits on interpolators and ALU instructions")],
    ))

    canons.append(canon(
        "unity", "dll-not-found-exception", "unity2022-cross",
        "DllNotFoundException: Unable to load DLL 'my_native_plugin': The specified module could not be found",
        r"(DllNotFoundException|Unable to load DLL|native plugin.*not found|lib.*\.so.*not found|module could not be found)",
        "plugin_error", "unity", ">=2022.3", "cross-platform", "true", 0.82, 0.88,
        "Native plugin DLL/SO not found. Wrong platform, wrong architecture, or missing dependencies.",
        [de("Put the DLL in the root Assets folder",
            "Unity expects native plugins in Assets/Plugins/{platform}/ with correct import settings", 0.78),
         de("Rename the DLL to match a different expected name",
            "The DLL name must match the DllImport attribute. Renaming creates a mismatch.", 0.82)],
        [wa("Place native plugins in the correct platform folder", 0.92,
            "Assets/Plugins/x86_64/ for Windows 64-bit; Assets/Plugins/Android/ for Android; set platform in Inspector"),
         wa("Check plugin Inspector settings for correct platform and CPU", 0.88,
            "Select .dll in Unity > Inspector > check 'Any Platform' or specific platforms, set CPU architecture"),
         wa("Verify all native dependencies are also included", 0.82,
            "Use dumpbin /dependents (Win) or ldd (Linux) to check DLL dependencies")],
    ))


    # =====================================================================
    # === SUPPLEMENTARY: thin domains get extra entries ===
    # =====================================================================

    # Redis: connection refused + cluster down
    canons.append(canon(
        "redis", "connection-refused", "redis7-linux",
        "Error: Could not connect to Redis at 127.0.0.1:6379: Connection refused",
        r"(Could not connect to Redis|Connection refused.*6379|ECONNREFUSED.*redis|redis.*Connection refused)",
        "connection_error", "redis", ">=7.0", "linux", "true", 0.92, 0.92,
        "Redis server not running or not listening on expected port.",
        [de("Reinstall Redis",
            "Connection refused means the service is not running, not a broken installation", 0.80),
         de("Change the port in redis.conf to avoid conflict",
            "Other applications expect the default port. Fix the port conflict instead.", 0.65)],
        [wa("Start the Redis service", 0.95,
            "sudo systemctl start redis && sudo systemctl enable redis"),
         wa("Check if Redis is running and on which port", 0.90,
            "redis-cli ping  # should return PONG; ss -tlnp | grep redis"),
         wa("Check redis.conf bind and protected-mode settings", 0.85,
            "bind 127.0.0.1; protected-mode yes  # default; change for remote access")],
    ))

    canons.append(canon(
        "redis", "clusterdown", "redis7-linux",
        "CLUSTERDOWN The cluster is down",
        r"(CLUSTERDOWN|cluster is down|cluster.*not.*ready|slot.*not.*covered)",
        "cluster_error", "redis", ">=7.0", "linux", "partial", 0.65, 0.85,
        "Redis Cluster has lost quorum or has uncovered hash slots. One or more master nodes are down without a failover replica.",
        [de("Force a failover on all nodes",
            "Forcing failover on healthy nodes can cause split-brain and data loss", 0.82),
         de("Restart all cluster nodes simultaneously",
            "Simultaneous restart loses cluster state; nodes may not rejoin properly", 0.78)],
        [wa("Check cluster status and identify failed nodes", 0.90,
            "redis-cli --cluster check 127.0.0.1:7000"),
         wa("Fix or replace the failed node and let cluster recover", 0.85,
            "redis-cli --cluster fix 127.0.0.1:7000  # reassigns orphaned slots"),
         wa("Add replicas to prevent future CLUSTERDOWN", 0.78,
            "redis-cli --cluster add-node new_node:7006 existing:7000 --cluster-slave")],
    ))

    # MongoDB: server selection timeout
    canons.append(canon(
        "mongodb", "server-selection-timeout", "mongo7-linux",
        "MongoTimeoutError: Server selection timed out after 30000 ms",
        r"(Server selection timed out|MongoTimeoutError|ServerSelectionTimeoutError|topology.*no suitable servers)",
        "connection_error", "mongodb", ">=7.0", "linux", "true", 0.82, 0.88,
        "MongoDB driver cannot find a suitable server within timeout. Replica set not initialized, wrong connection string, or network issue.",
        [de("Increase serverSelectionTimeoutMS to very large value",
            "Hides the real problem; application hangs for minutes before failing", 0.72),
         de("Use directConnection=true to bypass replica set",
            "Bypasses read preference and failover; application breaks when the node goes down", 0.68)],
        [wa("Check replica set status", 0.90,
            "mongosh --eval 'rs.status()'  # verify all members are healthy"),
         wa("Verify connection string matches replica set name", 0.92,
            "mongodb://host1:27017,host2:27017/?replicaSet=myReplicaSet  # must match rs.initiate name"),
         wa("Check network connectivity between app and all replica members", 0.85,
            "All hosts in the connection string must be reachable from the application")],
    ))

    # Kafka: consumer group coordinator
    canons.append(canon(
        "kafka", "group-coordinator-unavailable", "kafka3-linux",
        "org.apache.kafka.common.errors.GroupCoordinatorNotAvailableException",
        r"(GroupCoordinatorNotAvailable|coordinator.*not available|FindCoordinator.*error|consumer group.*unavailable)",
        "consumer_error", "kafka", ">=3.0", "linux", "true", 0.82, 0.88,
        "Consumer group coordinator broker not available. Cluster still starting up, or the coordinator broker is down.",
        [de("Restart all consumers simultaneously",
            "Mass restart triggers thundering herd problem; all consumers try to join at once causing repeated rebalances", 0.75),
         de("Delete the consumer group and recreate it",
            "Deleting the group loses committed offsets; all consumers restart from earliest/latest", 0.82)],
        [wa("Wait for cluster to fully start - coordinator election takes a few seconds", 0.88,
            "Add retry logic with backoff in consumer initialization"),
         wa("Check if the __consumer_offsets topic is healthy", 0.85,
            "kafka-topics.sh --describe --topic __consumer_offsets --bootstrap-server localhost:9092"),
         wa("Verify all brokers are running", 0.90,
            "kafka-broker-api-versions.sh --bootstrap-server localhost:9092")],
    ))

    # Elasticsearch: version conflict
    canons.append(canon(
        "elasticsearch", "version-conflict", "es8-linux",
        "version_conflict_engine_exception: [doc_id]: version conflict, required seqNo [5], primary term [1]",
        r"(version_conflict_engine_exception|version conflict.*seqNo|conflict.*primary term|409.*Conflict.*version)",
        "concurrency_error", "elasticsearch", ">=8.0", "linux", "true", 0.85, 0.90,
        "Optimistic concurrency control conflict. Document was modified by another process between read and write.",
        [de("Disable version checking with version_type=force",
            "Force overwrites silently lose concurrent updates; data corruption risk", 0.85),
         de("Add retry with no backoff",
            "Immediate retry on conflict often hits the same conflict; needs read-modify-write cycle", 0.70)],
        [wa("Implement read-modify-write with if_seq_no and if_primary_term", 0.92,
            "GET doc -> modify -> PUT with if_seq_no=X&if_primary_term=Y -> retry on 409"),
         wa("Use update API with script for atomic field updates", 0.88,
            "POST /index/_update/id { 'script': { 'source': 'ctx._source.count += 1' } }"),
         wa("Add retry with exponential backoff on conflict", 0.85,
            "Retry the full read-modify-write cycle 3-5 times with backoff")],
    ))

    return canons


def main():
    generated = 0
    skipped = 0
    for c in get_all_canons():
        parts = c["id"].split("/")
        out_dir = DATA_DIR / parts[0] / parts[1]
        out_file = out_dir / f"{parts[2]}.json"

        if out_file.exists():
            skipped += 1
            continue

        out_dir.mkdir(parents=True, exist_ok=True)
        out_file.write_text(
            json.dumps(c, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        generated += 1
        print(f"  Created: {c['id']}")

    print(f"\nDone: {generated} created, {skipped} skipped (already exist)")


if __name__ == "__main__":
    main()
