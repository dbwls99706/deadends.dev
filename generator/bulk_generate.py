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

    canons.append(canon(
        "ros2", "moveit2-planning-failed", "ros2-humble-linux",
        "MoveIt failed to compute a plan to the goal state",
        r"(MoveIt.*failed.*plan|planning.*failed.*goal|No motion plan found|PLANNING_FAILED|moveit.*plan.*fail)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "partial", 0.65, 0.82,
        "MoveIt2 motion planner cannot find a collision-free path. Caused by tight spaces, IK failures, or planning scene misconfiguration.",
        [de("Increase planning time to 60+ seconds unconditionally",
            "If the goal is unreachable or in collision, no amount of planning time will help", 0.78),
         de("Disable collision checking to get a plan",
            "Produces paths that collide with obstacles or the robot itself; dangerous on real hardware", 0.95),
         de("Switch planner to RRTConnect for every motion",
            "RRTConnect is already the default; the issue is usually the goal or scene, not the planner", 0.70)],
        [wa("Check if goal pose is reachable with IK: computeIK before planning", 0.88,
            "ros2 service call /compute_ik moveit_msgs/srv/GetPositionIK ..."),
         wa("Visualize the planning scene in RViz to check for unexpected collision objects", 0.90,
            "Add PlanningScene display in RViz2; check for stale collision objects"),
         wa("Use cartesian path planning for constrained motions", 0.80,
            "fraction = move_group.compute_cartesian_path(waypoints, 0.01, 0.0)")],
        preceded_by=[preceded("ros2/tf-lookup-exception/ros2-humble-linux", 0.25, "Missing TF frames cause MoveIt to fail at IK stage"),
                     preceded("ros2/urdf-xacro-parse-error/ros2-humble-linux", 0.20, "Invalid URDF breaks MoveIt's robot model")],
    ))

    canons.append(canon(
        "ros2", "robot-state-publisher-joint-not-found", "ros2-humble-linux",
        "[robot_state_publisher] Joint 'wheel_left_joint' not found in URDF",
        r"(robot_state_publisher.*Joint.*not found|joint.*not.*in.*URDF|Unknown joint.*robot_description|joint_state.*mismatch)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.88, 0.88,
        "robot_state_publisher receives joint states for joints not defined in the URDF. Joint names don't match.",
        [de("Rename joints in joint_states topic without updating URDF",
            "Creates inconsistency; TF tree publishes wrong transforms for renamed joints", 0.82),
         de("Suppress the warning and ignore missing joints",
            "TF tree will be incomplete; downstream nodes (navigation, manipulation) will fail", 0.85)],
        [wa("Verify joint names match between URDF and joint_state_publisher", 0.92,
            "ros2 topic echo /joint_states --once  # compare joint names with URDF"),
         wa("Check URDF joint names with check_urdf", 0.88,
            "xacro robot.urdf.xacro | check_urdf /dev/stdin | grep joint"),
         wa("Ensure hardware driver publishes the exact joint names from URDF", 0.85)],
        preceded_by=[preceded("ros2/urdf-xacro-parse-error/ros2-humble-linux", 0.30, "URDF modifications may change joint names")],
        leads_to=[leads("ros2/tf-lookup-exception/ros2-humble-linux", 0.35, "Missing joints mean missing TF frames")],
    ))

    canons.append(canon(
        "ros2", "message-filters-sync-drop", "ros2-humble-linux",
        "message_filters: Dropped messages due to synchronization timeout",
        r"(message_filters.*drop|ApproximateTimeSynchronizer.*drop|sync.*timeout.*message|TimeSynchronizer.*no match)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "partial", 0.72, 0.85,
        "message_filters TimeSynchronizer drops messages because sensor timestamps don't align within the tolerance window.",
        [de("Set slop (time tolerance) to very large values like 10 seconds",
            "Pairs messages from completely different time instants; fuses stale data producing wrong results", 0.80),
         de("Use exact time synchronizer for hardware sensors",
            "Hardware sensors almost never have exactly matching timestamps; drops all messages", 0.90)],
        [wa("Use ApproximateTimeSynchronizer with appropriate slop for your sensor rates", 0.88,
            "ats = ApproximateTimeSynchronizer([sub1, sub2], queue_size=10, slop=0.1)"),
         wa("Check that all sensors use the same time source (use_sim_time consistency)", 0.85,
            "ros2 param get /camera use_sim_time; ros2 param get /lidar use_sim_time"),
         wa("Increase queue_size if sensors have different publication rates", 0.82)],
    ))

    canons.append(canon(
        "ros2", "pluginlib-class-not-found", "ros2-humble-linux",
        "pluginlib::ClassLoader: Unable to find class 'my_plugin/MyPlugin'",
        r"(pluginlib.*ClassLoader.*Unable|pluginlib.*class.*not.*found|plugin.*not.*registered|ClassLoader.*fail.*load)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.85, 0.88,
        "pluginlib cannot find the plugin class. Usually a missing export in package.xml or wrong plugin description XML.",
        [de("Add the plugin .so to LD_LIBRARY_PATH manually",
            "pluginlib uses its own class registry, not LD_LIBRARY_PATH; the plugin must be exported via package.xml", 0.85),
         de("Copy the plugin XML from another package",
            "Plugin XML must reference the exact library name and class from your package", 0.78)],
        [wa("Verify plugin is exported in package.xml with <pluginlib> tag", 0.92,
            "<export><pluginlib plugin=\"${prefix}/plugins.xml\" /></export>"),
         wa("Check plugins.xml has correct library path and class name", 0.88,
            "<class name=\"my_ns/MyPlugin\" type=\"my_ns::MyPlugin\" base_class_type=\"base_ns::Base\">"),
         wa("Rebuild and re-source after modifying plugin registration", 0.85,
            "colcon build --packages-select my_plugin_pkg && source install/setup.bash")],
    ))

    canons.append(canon(
        "ros2", "ament-python-setup-deprecated", "ros2-humble-linux",
        "SetuptoolsDeprecationWarning: setup.py install is deprecated",
        r"(SetuptoolsDeprecationWarning.*setup\.py.*deprecated|setup\.py.*install.*deprecated|ament_python.*setuptools.*warn)",
        "build_error", "ros2", ">=humble,<rolling", "linux", "true", 0.85, 0.88,
        "setuptools deprecated setup.py install. Affects ament_python packages. Warning may become error in future setuptools versions.",
        [de("Downgrade setuptools to suppress the warning",
            "Pins to old version; breaks other packages that need modern setuptools features", 0.78),
         de("Switch ament_python package to ament_cmake",
            "Requires rewriting the entire build system; ament_python is correct for pure Python packages", 0.82)],
        [wa("Pin setuptools < 58.2.0 only in your build virtualenv", 0.80,
            "pip install 'setuptools==58.2.0'  # temporary, for colcon build only"),
         wa("Migrate to pyproject.toml with [build-system] entry point", 0.88,
            "Add pyproject.toml with [build-system] requires=[setuptools, ament-package]"),
         wa("Set PYTHONDONTWRITEBYTECODE=1 and ignore the warning if builds succeed", 0.75)],
    ))

    canons.append(canon(
        "ros2", "colcon-symlink-stale", "ros2-humble-linux",
        "colcon build --symlink-install: Changes not reflected after rebuild",
        r"(symlink.*install.*stale|symlink.*not.*reflect|colcon.*symlink.*change.*not|--symlink-install.*outdated)",
        "build_error", "ros2", ">=humble,<rolling", "linux", "true", 0.88, 0.90,
        "After colcon build --symlink-install, Python or launch file changes are not picked up. Stale install directory.",
        [de("Delete install/ and rebuild every time",
            "Loses the speed benefit of symlink install; wastes minutes on full rebuilds", 0.75),
         de("Copy files manually into install/",
            "Manual copies get overwritten on next build and mask the real symlink issue", 0.85)],
        [wa("Re-source install/setup.bash after rebuilding", 0.92,
            "colcon build --symlink-install && source install/setup.bash"),
         wa("For Python packages, ensure entry_points are in setup.cfg, not just setup.py", 0.85),
         wa("Delete install/<pkg> and rebuild just that package for fresh symlinks", 0.88,
            "rm -rf install/my_pkg && colcon build --symlink-install --packages-select my_pkg")],
    ))

    canons.append(canon(
        "ros2", "image-transport-plugin-not-found", "ros2-humble-linux",
        "image_transport: No plugin found for transport 'compressed'",
        r"(image_transport.*plugin.*not found|transport.*compressed.*not.*available|image_transport.*No.*plugin|compressed.*transport.*missing)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.92, 0.90,
        "image_transport cannot find the compressed/theora/raw transport plugin. Missing package installation.",
        [de("Manually compress images in the subscriber callback",
            "Bypasses image_transport entirely; loses bandwidth-efficient transport and standard interface", 0.80),
         de("Use raw transport and accept the bandwidth cost",
            "Raw HD images over WiFi or limited bandwidth saturate the link; drops frames", 0.70)],
        [wa("Install image_transport plugins package", 0.95,
            "sudo apt install ros-humble-image-transport-plugins"),
         wa("Verify available transports with ros2 run image_transport list_transports", 0.88,
            "ros2 run image_transport list_transports"),
         wa("Re-source workspace after installing new transport plugins", 0.85)],
    ))

    canons.append(canon(
        "ros2", "micro-ros-agent-connection-failed", "ros2-humble-linux",
        "[micro-ROS Agent] No connection from micro-ROS client",
        r"(micro.?ROS.*Agent.*no connection|micro.?ros.*agent.*fail|micro.?ROS.*client.*not.*found|uxr.*agent.*timeout)",
        "communication_error", "ros2", ">=humble,<rolling", "linux", "partial", 0.70, 0.82,
        "micro-ROS agent cannot connect to the embedded MCU client. Serial/UDP transport misconfiguration.",
        [de("Increase agent timeout to minutes",
            "If the MCU is not running the micro-ROS client, no timeout will help", 0.78),
         de("Flash firmware without matching the agent transport",
            "Serial agent needs serial firmware config; UDP agent needs WiFi/Ethernet firmware", 0.88)],
        [wa("Verify serial port and baud rate match between agent and firmware", 0.90,
            "ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0 -b 115200"),
         wa("Check that the MCU firmware was built with the correct RMW and transport", 0.85,
            "colcon build --packages-select micro_ros_setup --cmake-args -DRMW_UXRCE_TRANSPORT=serial"),
         wa("Use minicom/screen to verify the serial port is alive before starting agent", 0.82,
            "screen /dev/ttyUSB0 115200  # should see micro-ROS handshake bytes")],
    ))

    canons.append(canon(
        "ros2", "fastdds-shared-memory-error", "ros2-humble-linux",
        "[RTPS_TRANSPORT_SHM] Failed to create shared memory segment",
        r"(RTPS_TRANSPORT_SHM.*fail|shared memory.*segment.*error|SHM.*transport.*fail|shm.*open.*fail.*fastdds)",
        "communication_error", "ros2", ">=humble,<rolling", "linux", "true", 0.85, 0.88,
        "Fast DDS shared memory transport fails. Common in Docker containers or when /dev/shm is too small.",
        [de("Disable Fast DDS entirely and switch RMW",
            "The fix is simpler: just configure SHM correctly or disable only the SHM transport", 0.75),
         de("Increase system shared memory to very large values",
            "If running in Docker, the host /dev/shm size is what matters, not sysctl settings", 0.70)],
        [wa("Increase Docker --shm-size if running in containers", 0.92,
            "docker run --shm-size=512m ... or add shm_size: 512m in docker-compose"),
         wa("Disable SHM transport via Fast DDS XML profile", 0.88,
            "Export FASTRTPS_DEFAULT_PROFILES_FILE=no_shm.xml with <transport_descriptor><type>UDPv4</type></transport_descriptor>"),
         wa("Set RMW_FASTRTPS_USE_QOS_FROM_XML=1 for full control over transport", 0.82)],
    ))

    canons.append(canon(
        "ros2", "param-yaml-load-error", "ros2-humble-linux",
        "Failed to parse parameters YAML file: Invalid YAML",
        r"(Failed to parse.*parameters.*YAML|param.*yaml.*error|Invalid.*parameter.*YAML|yaml.*load.*param.*fail)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.90, 0.90,
        "ROS 2 parameter YAML file has syntax errors or wrong structure. Parameters must be under /**/ros__parameters.",
        [de("Use flat key=value format without proper YAML nesting",
            "ROS 2 requires specific YAML structure: node_name.ros__parameters.param_name", 0.85),
         de("Use ROS 1 style rosparam YAML format",
            "ROS 2 parameter YAML has different structure with ros__parameters namespace", 0.88)],
        [wa("Follow the correct ROS 2 parameter YAML structure", 0.95,
            "/my_node:\\n  ros__parameters:\\n    param1: value1\\n    param2: value2"),
         wa("Use /** wildcard to apply parameters to any node name", 0.88,
            "/**:\\n  ros__parameters:\\n    use_sim_time: true"),
         wa("Validate YAML syntax with python -c 'import yaml; yaml.safe_load(open(f))'", 0.85,
            "python3 -c \"import yaml; yaml.safe_load(open('params.yaml'))\"")],
    ))

    canons.append(canon(
        "ros2", "pointcloud-field-mismatch", "ros2-humble-linux",
        "RuntimeError: PointCloud2 field 'intensity' not found in message",
        r"(PointCloud2.*field.*not found|pointcloud.*field.*mismatch|pcl.*field.*missing|sensor_msgs.*PointCloud2.*error)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.85, 0.88,
        "PointCloud2 message does not contain expected fields. LiDAR drivers produce different field names/types.",
        [de("Cast the entire PointCloud2 to a fixed struct assuming field layout",
            "Different LiDAR models have different field layouts; hardcoded offsets cause data corruption", 0.88),
         de("Ignore the missing field and use default values",
            "Downstream algorithms (SLAM, segmentation) produce wrong results with fabricated data", 0.80)],
        [wa("Read available fields from the PointCloud2 message header", 0.92,
            "for field in msg.fields: print(field.name, field.datatype, field.offset)"),
         wa("Use point_cloud2.read_points() with field_names parameter", 0.88,
            "from sensor_msgs_py import point_cloud2; pts = point_cloud2.read_points(msg, field_names=['x','y','z'])"),
         wa("Remap field names in the LiDAR driver launch configuration", 0.82)],
    ))

    canons.append(canon(
        "ros2", "costmap-layer-plugin-error", "ros2-humble-linux",
        "[costmap_2d] Failed to load plugin: nav2_costmap_2d::ObstacleLayer",
        r"(costmap_2d.*Failed.*load.*plugin|costmap.*layer.*plugin.*error|nav2_costmap_2d.*plugin.*not found|costmap.*plugin.*ClassLoader)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.85, 0.88,
        "Nav2 costmap cannot load a layer plugin. Missing package or wrong plugin name in parameters.",
        [de("Write a custom costmap layer from scratch",
            "Standard layers (obstacle, inflation, voxel) cover 90% of use cases; custom layers are complex", 0.82),
         de("Remove the layer from configuration and navigate without it",
            "Removing obstacle layer means robot cannot see obstacles; will collide", 0.92)],
        [wa("Install the missing Nav2 costmap plugin package", 0.92,
            "sudo apt install ros-humble-nav2-costmap-2d"),
         wa("Verify plugin names in nav2_params.yaml match installed plugins", 0.90,
            "plugin_names: ['static_layer', 'obstacle_layer', 'inflation_layer']"),
         wa("Check plugin type string matches exactly with ros2 plugin list", 0.85,
            "ros2 pkg prefix nav2_costmap_2d && cat install/nav2_costmap_2d/share/nav2_costmap_2d/plugins.xml")],
        preceded_by=[preceded("ros2/nav2-bt-action-failed/ros2-humble-linux", 0.15, "Costmap failure causes Nav2 actions to abort")],
    ))

    canons.append(canon(
        "ros2", "joint-state-broadcaster-not-configured", "ros2-humble-linux",
        "[controller_manager] joint_state_broadcaster is not configured",
        r"(joint_state_broadcaster.*not configured|JointStateBroadcaster.*error|joint.*broadcaster.*fail|controller_manager.*broadcaster.*not)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.88, 0.88,
        "ros2_control joint_state_broadcaster not loaded or configured. Robot state is not published to /joint_states.",
        [de("Publish joint states manually from your own node",
            "Bypasses ros2_control safety and timing guarantees; joint states may be inconsistent with actual hardware", 0.85),
         de("Load the broadcaster before controller_manager is ready",
            "Controller manager must be fully initialized before loading controllers; race condition", 0.78)],
        [wa("Configure joint_state_broadcaster in ros2_control YAML parameters", 0.92,
            "controller_manager:\\n  ros__parameters:\\n    joint_state_broadcaster:\\n      type: joint_state_broadcaster/JointStateBroadcaster"),
         wa("Load and activate via launch file with spawner node", 0.90,
            "Node(package='controller_manager', executable='spawner', arguments=['joint_state_broadcaster'])"),
         wa("Verify hardware interface exports the correct joint names", 0.85,
            "ros2 control list_hardware_interfaces")],
        leads_to=[leads("ros2/robot-state-publisher-joint-not-found/ros2-humble-linux", 0.30, "If broadcaster publishes wrong joints, robot_state_publisher reports mismatch")],
    ))

    canons.append(canon(
        "ros2", "rviz2-display-error", "ros2-humble-linux",
        "[rviz2] Display 'LaserScan' has encountered an error: Transform [Error]",
        r"(rviz2.*Display.*error|rviz.*Transform.*Error|rviz.*display.*fail|RViz.*Global Status.*Error)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.85, 0.88,
        "RViz2 display shows transform error. The display's fixed frame does not match the TF tree, or TF data is missing.",
        [de("Change RViz Fixed Frame to 'map' without a map publisher running",
            "If no node publishes map frame, all displays depending on it will error", 0.82),
         de("Ignore the error assuming it is cosmetic",
            "RViz displays with transform errors render nothing or render in wrong positions", 0.78)],
        [wa("Set Fixed Frame to a frame that exists in your TF tree", 0.92,
            "Set Fixed Frame to 'base_link' or 'odom' — check available frames with ros2 run tf2_tools view_frames"),
         wa("Verify TF is being published at sufficient rate", 0.85,
            "ros2 topic hz /tf  # should be >= 10 Hz for smooth display"),
         wa("Check the topic name and message type for each display", 0.88,
            "Click the display in RViz, verify Topic matches ros2 topic list output")],
        preceded_by=[preceded("ros2/tf-lookup-exception/ros2-humble-linux", 0.35, "Missing TF frames cause all RViz displays to error")],
    ))

    canons.append(canon(
        "ros2", "diagnostic-updater-stale", "ros2-humble-linux",
        "[diagnostic_aggregator] Stale diagnostic: /sensors/imu",
        r"(diagnostic.*stale|diagnostic_aggregator.*stale|diagnostic.*timeout|diagnostics.*not.*updating)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "partial", 0.70, 0.82,
        "diagnostic_updater reports stale status because the hardware driver stopped publishing diagnostics within the expected period.",
        [de("Increase the stale timeout to hide the warning",
            "Stale diagnostics usually mean the hardware is actually not responding; hiding delays fault detection", 0.80),
         de("Remove the diagnostic from the aggregator config",
            "Loses monitoring capability for that hardware component", 0.75)],
        [wa("Check if the hardware driver node is still running", 0.90,
            "ros2 node list | grep driver_node && ros2 topic hz /diagnostics"),
         wa("Verify diagnostic_updater frequency matches the driver's publication rate", 0.85,
            "Set diagnostic_updater period to match or slightly exceed the driver rate"),
         wa("Add a hardware watchdog that restarts the driver on failure", 0.78)],
    ))

    canons.append(canon(
        "ros2", "ros2-bag-play-clock-error", "ros2-humble-linux",
        "ros2 bag play: Clock time is not being published",
        r"(ros2 bag.*play.*clock|bag.*play.*time.*error|use_sim_time.*bag.*play|clock.*not.*publish.*bag)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.90, 0.88,
        "Nodes use use_sim_time:=true but ros2 bag play is not publishing /clock, or vice versa.",
        [de("Set use_sim_time on some nodes but not others",
            "Causes TF extrapolation errors: some nodes use wall clock, others use sim time", 0.90),
         de("Publish /clock manually at a fixed rate",
            "Clock must advance with bag time, not independently; manual clock causes data-time mismatch", 0.82)],
        [wa("Use --clock flag when playing bags", 0.95,
            "ros2 bag play my_bag --clock 100  # publishes /clock at 100 Hz"),
         wa("Set use_sim_time:=true on ALL nodes when replaying bags", 0.90,
            "ros2 launch my_pkg replay.launch.py use_sim_time:=true"),
         wa("Use --rate to control playback speed while keeping clock consistent", 0.85,
            "ros2 bag play my_bag --clock 100 --rate 0.5  # half speed")],
    ))

    canons.append(canon(
        "ros2", "rclcpp-callback-group-deadlock", "ros2-humble-linux",
        "Deadlock detected: callback waiting for another callback in same MutuallyExclusiveCallbackGroup",
        r"(deadlock.*callback.*group|MutuallyExclusive.*deadlock|callback.*group.*block|SingleThreadedExecutor.*deadlock|service.*call.*inside.*callback)",
        "runtime_error", "ros2", ">=humble,<rolling", "linux", "true", 0.82, 0.88,
        "Calling a service synchronously inside a callback deadlocks the executor. The service response callback cannot run.",
        [de("Use a longer timeout on the synchronous service call",
            "The call can never complete because the executor is blocked; timeout just delays the deadlock detection", 0.92),
         de("Create a new single-threaded executor per service call",
            "Multiple executors on the same node cause undefined behavior with callbacks", 0.85)],
        [wa("Use async service calls (call_async) inside callbacks", 0.92,
            "future = client.call_async(request); rclpy.spin_until_future_complete(self, future)"),
         wa("Use MultiThreadedExecutor with ReentrantCallbackGroup for the service client", 0.90,
            "cb_group = ReentrantCallbackGroup(); client = self.create_client(srv_type, name, callback_group=cb_group)"),
         wa("Move the service call to a separate thread", 0.82,
            "import threading; threading.Thread(target=sync_service_call).start()")],
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

    # =====================================================================
    # === API / SERVICE QUIRKS ===
    # =====================================================================
    canons.append(canon(
        "api", "stripe-webhook-duplicate-delivery", "stripe-api-any",
        "Stripe webhook event received multiple times despite 200 response",
        r"(duplicate.*webhook|webhook.*delivered.*twice|idempotency.*key.*conflict)",
        "webhook_reliability", "stripe-api", ">=2023-10-16", "any", "true", 0.88, 0.90,
        "Stripe retries webhooks if your endpoint takes >5s to respond 200, even if it eventually succeeds. Docs say 'up to 3 days' but don't clarify the 5s window clearly.",
        [de("Return 200 after processing the event fully",
            "If processing takes >5s, Stripe assumes failure and retries. You get duplicate events with same event ID.", 0.85),
         de("Rely on Stripe's 'at-most-once' delivery assumption",
            "Stripe explicitly guarantees 'at-least-once' delivery. Duplicates are expected behavior, not a bug.", 0.90)],
        [wa("Return 200 immediately, then process asynchronously via queue", 0.95,
            "Receive webhook -> store raw event in DB/queue -> return 200 -> process from queue"),
         wa("Implement idempotency using event.id as dedup key", 0.92,
            "if Event.objects.filter(stripe_event_id=event['id']).exists(): return 200"),
         wa("Use Stripe's event retrieval API to verify event authenticity instead of trusting payload", 0.85,
            "event = stripe.Event.retrieve(event_id) # re-fetch from Stripe API")],
    ))

    canons.append(canon(
        "api", "github-secondary-rate-limit", "github-api-any",
        "HTTP 403: You have exceeded a secondary rate limit. Please wait a few minutes before you try again.",
        r"(secondary rate limit|abuse detection|HTTP 403.*rate limit)",
        "rate_limiting", "github-api", ">=2022-01", "any", "partial", 0.72, 0.85,
        "GitHub has undocumented 'secondary' rate limits separate from the 5000 req/hr primary limit. Triggered by concurrent requests, rapid content creation, or polling. Not visible in X-RateLimit headers.",
        [de("Check X-RateLimit-Remaining header and stay under 5000/hr",
            "Secondary rate limits are separate and invisible in standard rate limit headers. You can hit them at 100 req/hr if requests are concurrent.", 0.88),
         de("Use a personal access token instead of GitHub App token",
            "Secondary rate limits apply to all authentication methods equally. PATs are not exempt.", 0.80),
         de("Retry immediately after 403",
            "GitHub may escalate to longer bans if you retry too aggressively after secondary rate limit.", 0.75)],
        [wa("Add 1s sleep between mutating requests (POST/PATCH/PUT)", 0.90,
            "import time; time.sleep(1)  # between each write API call"),
         wa("Use conditional requests with ETags for polling endpoints", 0.88,
            "headers = {'If-None-Match': cached_etag}  # 304 responses don't count against limits"),
         wa("Implement exponential backoff starting at 60s on 403, with jitter", 0.85,
            "wait = 60 * (2 ** retry_count) + random.uniform(0, 10)")],
    ))

    canons.append(canon(
        "api", "s3-presigned-url-clock-skew", "aws-s3-any",
        "SignatureDoesNotMatch: The request signature we calculated does not match the signature you provided",
        r"(SignatureDoesNotMatch|presigned.*expired|clock.*skew.*S3)",
        "authentication", "aws-s3", ">=2023-01", "any", "true", 0.85, 0.88,
        "S3 presigned URLs embed the signing time. If the server generating the URL has clock skew >15 minutes from AWS, URLs are born expired. Docker containers and VMs are common culprits.",
        [de("Increase presigned URL expiry to 24 hours",
            "URLs still fail instantly if clock is ahead by >15 min. Longer expiry doesn't help when the start time is wrong.", 0.82),
         de("Regenerate the URL and retry",
            "Same server generates the same skewed signature. Retrying without fixing clock produces identical failures.", 0.78)],
        [wa("Sync system clock with NTP before generating presigned URLs", 0.95,
            "sudo ntpdate -s time.nist.gov  # or: sudo systemctl restart chronyd"),
         wa("Use STS to get server time and calculate offset for signing", 0.82,
            "aws_time = boto3.client('sts').get_caller_identity()  # response headers contain Date"),
         wa("In Docker, mount host clock: -v /etc/localtime:/etc/localtime:ro", 0.88,
            "docker run -v /etc/localtime:/etc/localtime:ro myapp")],
    ))

    canons.append(canon(
        "api", "google-oauth-refresh-token-revoked", "google-oauth-any",
        "google.auth.exceptions.RefreshError: ('invalid_grant: Token has been expired or revoked.',)",
        r"(invalid_grant|Token has been expired or revoked|refresh.*token.*revoked)",
        "authentication", "google-oauth", ">=v2", "any", "partial", 0.70, 0.82,
        "Google silently revokes refresh tokens after 6 months of inactivity, when user changes password, or when >50 tokens exist per client. The 50-token limit is barely documented.",
        [de("Store and reuse the refresh token indefinitely",
            "Google has a hidden 50 refresh token limit per user per OAuth client. Token 51 silently invalidates token 1. Also, 6 months inactivity = revocation.", 0.88),
         de("Request a new refresh token on every auth flow",
            "Each new token pushes out the oldest. If user has multiple devices, they kick each other out.", 0.75)],
        [wa("Store refresh tokens per-user and reuse existing ones via prompt=none", 0.85,
            "If user already has a refresh token in your DB, use it instead of initiating new OAuth flow"),
         wa("Implement re-authentication flow that gracefully handles revocation", 0.90,
            "try: creds.refresh(request) except RefreshError: redirect_to_oauth_consent()"),
         wa("Use service accounts for server-to-server auth instead of user OAuth", 0.88,
            "creds = service_account.Credentials.from_service_account_file('key.json', scopes=SCOPES)")],
    ))

    canons.append(canon(
        "api", "slack-mrkdwn-not-markdown", "slack-api-any",
        "Slack message displays raw markdown instead of formatted text in Block Kit",
        r"(mrkdwn.*not.*rendering|block.*kit.*markdown.*raw|slack.*formatting.*broken)",
        "formatting", "slack-api", ">=2023-01", "any", "true", 0.90, 0.88,
        "Slack Block Kit uses 'mrkdwn' (not 'markdown') as the type field. Also, mrkdwn is NOT standard Markdown - it uses *bold* (not **bold**), ~strike~ (not ~~strike~~), and doesn't support headers.",
        [de("Use type: 'markdown' in Block Kit blocks",
            "The field must be 'mrkdwn' (Slack's proprietary format). 'markdown' silently falls back to plain text with no error.", 0.92),
         de("Use standard Markdown syntax like **bold** and ~~strike~~",
            "Slack mrkdwn uses *bold* and ~strike~. Standard markdown bold (**) is treated as literal asterisks.", 0.88)],
        [wa("Use type: 'mrkdwn' and Slack-specific syntax", 0.95,
            '{"type": "section", "text": {"type": "mrkdwn", "text": "*bold* _italic_ ~strike~ `code`"}}'),
         wa("Use Slack Block Kit Builder to preview before sending", 0.88,
            "Test in Block Kit Builder to verify rendering before deploying")],
    ))

    canons.append(canon(
        "api", "openai-timeout-vs-max-tokens", "openai-api-any",
        "openai.APITimeoutError: Request timed out. or unexpected truncated response",
        r"(APITimeoutError|Request timed out|finish_reason.*length|response.*truncat)",
        "timeout", "openai-api", ">=v1.0", "any", "true", 0.85, 0.90,
        "OpenAI API timeout is client-side (default 600s). A long response can timeout before completion. Separately, max_tokens silently truncates without error - finish_reason becomes 'length' not 'stop'.",
        [de("Increase client timeout to avoid truncation",
            "Timeout and truncation are different issues. Timeout = client gave up waiting. Truncation = max_tokens limit hit. You may have both problems simultaneously.", 0.82),
         de("Assume response is complete if no error was raised",
            "finish_reason='length' means output was truncated but no exception is raised. You must check finish_reason explicitly.", 0.88)],
        [wa("Always check response.choices[0].finish_reason == 'stop'", 0.95,
            "if response.choices[0].finish_reason == 'length': # response was truncated, need continuation"),
         wa("Implement streaming for long responses to avoid timeout", 0.88,
            "stream = client.chat.completions.create(stream=True, ...); for chunk in stream: ...")],
    ))

    canons.append(canon(
        "api", "rest-pagination-cursor-invalidation", "rest-api-any",
        "HTTP 400/404: Invalid cursor or pagination token expired",
        r"(invalid.*cursor|pagination.*token.*expired|cursor.*not.*found|page.*token.*invalid)",
        "pagination", "rest-api", ">=any", "any", "partial", 0.68, 0.80,
        "Many APIs invalidate pagination cursors after data mutations or after a time window (15min-1hr). Cursor-based pagination docs rarely mention this.",
        [de("Cache cursor and resume pagination hours later",
            "Most API cursors expire within 15-60 minutes. Some (e.g., Elasticsearch scroll) expire in 1 minute by default.", 0.85),
         de("Use offset/limit pagination to avoid cursor issues",
            "Offset pagination skips items when rows are inserted/deleted between pages.", 0.78)],
        [wa("Complete pagination in a single session without long pauses", 0.85,
            "Process all pages in a tight loop. Store results locally, then process after pagination completes."),
         wa("Use keyset pagination (WHERE id > last_seen_id ORDER BY id)", 0.90,
            "SELECT * FROM items WHERE id > :last_id ORDER BY id LIMIT 100"),
         wa("Implement checkpoint-based restart: store last processed item ID", 0.88,
            "On cursor expiry, restart pagination with filter to skip already-processed items")],
    ))

    canons.append(canon(
        "api", "graphql-n-plus-one-dataloader", "graphql-node-any",
        "GraphQL query takes 30s+ with nested resolvers due to N+1 database queries",
        r"(N\+1.*quer|dataloader.*batch.*not.*firing|graphql.*slow.*nested)",
        "performance", "graphql", ">=any", "any", "true", 0.90, 0.92,
        "GraphQL resolvers execute per-field per-item. A query returning 100 users with posts generates 101 SQL queries. DataLoader batching fixes this but must be per-request scoped.",
        [de("Add database indexes to speed up individual resolver queries",
            "Indexes help per-query speed but don't reduce the 100+ query count. The bottleneck is round-trip overhead.", 0.80),
         de("Create a single global DataLoader instance",
            "DataLoader cache must be per-request. A global instance leaks data between users and grows unbounded.", 0.88)],
        [wa("Create DataLoader instances per-request in context", 0.95,
            "context = { userLoader: new DataLoader(ids => User.findByIds(ids)) }  // new per request"),
         wa("Use query complexity analysis to reject expensive queries", 0.85,
            "depthLimit(10), createComplexityLimitRule(1000)")],
    ))

    canons.append(canon(
        "api", "webhook-hmac-raw-body-mismatch", "webhook-node-any",
        "Webhook signature verification fails despite correct secret key",
        r"(webhook.*signature.*fail|HMAC.*mismatch|verify.*signature.*invalid)",
        "authentication", "webhook", ">=any", "any", "true", 0.92, 0.90,
        "Webhook HMAC signatures are computed over raw request body bytes. JSON.stringify(parsed) != original bytes due to key ordering, whitespace, and Unicode escaping differences.",
        [de("Compute HMAC over JSON.stringify(req.body)",
            "JSON.stringify produces different bytes than the original payload. Signature will never match.", 0.95),
         de("Use bodyParser.json() before webhook route in Express",
            "bodyParser consumes the raw body stream. The original bytes are gone by handler time.", 0.90)],
        [wa("Capture raw body before JSON parsing in Express", 0.95,
            "app.use('/webhook', express.raw({type: 'application/json'})); // req.body is Buffer"),
         wa("In Flask, use request.get_data() not request.json", 0.92,
            "raw_body = request.get_data(); sig = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()"),
         wa("Use timing-safe comparison for HMAC verification", 0.90,
            "crypto.timingSafeEqual(Buffer.from(computed), Buffer.from(received))")],
    ))

    canons.append(canon(
        "api", "twilio-webhook-retry-duplicate-sms", "twilio-api-any",
        "Twilio sends duplicate SMS because webhook endpoint returned non-2xx or timed out",
        r"(twilio.*duplicate|twilio.*retry.*webhook|duplicate.*SMS.*twilio)",
        "webhook_reliability", "twilio-api", ">=2023-01", "any", "true", 0.85, 0.88,
        "Twilio retries status callbacks up to 4 times if your endpoint doesn't return 2xx within 15 seconds. If the webhook triggers reply sending, each retry causes duplicate outbound messages.",
        [de("Return 200 only after sending the reply SMS",
            "If sending the reply takes >15s, Twilio retries. Your handler sends another reply on retry. User gets 2-4 duplicate SMS.", 0.88),
         de("Disable retries in Twilio console",
            "Status callback retries cannot be fully disabled for all webhook types. Some retries are hardcoded.", 0.72)],
        [wa("Return TwiML immediately, queue reply sending asynchronously", 0.92,
            "Return empty <Response/> immediately. Process and reply via REST API from a background job."),
         wa("Implement idempotency using MessageSid from Twilio", 0.90,
            "if db.exists(message_sid=request.form['MessageSid']): return '<Response/>'")],
    ))

    # =====================================================================
    # === CLOUD / INFRASTRUCTURE QUIRKS ===
    # =====================================================================
    canons.append(canon(
        "cloud", "aws-iam-eventual-consistency", "aws-iam-any",
        "AccessDenied: User is not authorized to perform this action even after policy is attached",
        r"(AccessDenied|not authorized|IAM.*policy.*attached.*denied|eventual.*consistency.*IAM)",
        "iam_permission", "aws-iam", ">=2023-01", "any", "true", 0.82, 0.90,
        "IAM policy changes take up to 60 seconds to propagate globally due to eventual consistency. AWS docs mention this in a footnote but most tutorials show attach-then-use immediately.",
        [de("Attach IAM policy and immediately make API call",
            "IAM is eventually consistent. Policy may take 10-60 seconds to propagate. First call almost always fails.", 0.90),
         de("Detach and reattach the policy thinking it didn't apply",
            "Reattaching resets the propagation timer. Makes the problem worse.", 0.82),
         de("Add a hardcoded sleep(5) after policy attachment",
            "5 seconds is often not enough. Propagation can take up to 60 seconds in some regions.", 0.72)],
        [wa("Implement retry with exponential backoff after IAM changes", 0.95,
            "for i in range(6): try: client.action() except AccessDenied: time.sleep(2**i)"),
         wa("Use STS AssumeRole to force fresh credential evaluation", 0.85,
            "After attaching policy, assume the role again to get fresh session credentials"),
         wa("Use IAM policy simulator API to verify propagation before proceeding", 0.80,
            "iam.simulate_principal_policy(PolicySourceArn=role_arn, ActionNames=['s3:GetObject'])")],
    ))

    canons.append(canon(
        "cloud", "aws-lambda-vpc-cold-start", "aws-lambda-linux",
        "AWS Lambda function times out or takes 10s+ on first invocation when in VPC",
        r"(Lambda.*VPC.*cold.*start|Lambda.*timeout.*VPC|ENI.*creation.*slow|Task timed out after)",
        "performance", "aws-lambda", ">=2023-01", "linux", "true", 0.88, 0.92,
        "Lambda functions in a VPC require ENI (Elastic Network Interface) creation on cold start. Before Hyperplane (2019+), this added 10-30s. Post-Hyperplane it's ~1-2s but still catches people. Provisioned concurrency is the real fix.",
        [de("Increase Lambda timeout to 5 minutes to handle cold start",
            "Longer timeout masks the problem. Users still experience 10s+ delays on every cold start.", 0.78),
         de("Use a CloudWatch scheduled event to keep Lambda warm",
            "Warming pings only keep 1 concurrent instance warm. Second concurrent request still cold starts.", 0.72),
         de("Remove VPC configuration to eliminate cold start",
            "Function loses access to VPC resources (RDS, ElastiCache, etc.). Defeats the purpose of VPC placement.", 0.85)],
        [wa("Use Provisioned Concurrency to eliminate cold starts", 0.95,
            "aws lambda put-provisioned-concurrency-config --function-name my-func --qualifier prod --provisioned-concurrent-executions 5"),
         wa("Use Lambda SnapStart (Java) or keep dependencies minimal to reduce init time", 0.85,
            "Reduce deployment package size. Use Lambda layers for shared deps. Lazy-load heavy SDKs."),
         wa("Use VPC endpoints (PrivateLink) instead of NAT Gateway for AWS service access", 0.82,
            "This lets Lambda access S3/DynamoDB/etc without full VPC setup, reducing cold start penalty")],
    ))

    canons.append(canon(
        "cloud", "terraform-state-lock-dynamodb", "terraform-aws-any",
        "Error: Error acquiring the state lock: ConditionalCheckFailedException",
        r"(Error acquiring the state lock|ConditionalCheckFailedException|state.*lock.*timeout|Lock Info)",
        "state_management", "terraform", ">=1.0", "any", "true", 0.90, 0.88,
        "Terraform S3 backend uses DynamoDB for state locking. If a previous terraform apply was killed (Ctrl+C, CI timeout, OOM), the lock remains forever. force-unlock is scary but sometimes necessary.",
        [de("Wait for the lock to expire automatically",
            "DynamoDB locks have no TTL by default. The lock will remain forever until manually removed.", 0.92),
         de("Run another terraform apply hoping it will override the lock",
            "Concurrent applies with locked state cause state corruption. Never run parallel applies.", 0.95),
         de("Delete the DynamoDB lock item directly from console",
            "Deleting the item works but bypasses Terraform's lock check. If another process IS running, state corruption follows.", 0.78)],
        [wa("Use terraform force-unlock with the lock ID", 0.92,
            "terraform force-unlock LOCK_ID  # Lock ID is shown in the error message"),
         wa("Check if another process is actually running before force-unlock", 0.95,
            "Check CI/CD pipelines, other terminals. Only force-unlock if you're SURE no other apply is running."),
         wa("Add -lock-timeout=5m to terraform commands in CI to handle transient locks", 0.85,
            "terraform apply -lock-timeout=300s  # wait up to 5 minutes for lock release")],
    ))

    canons.append(canon(
        "cloud", "aws-ecs-task-def-deregister-running", "aws-ecs-any",
        "Deregistered ECS task definition but old tasks are still running with old image",
        r"(task definition.*deregister.*still running|ECS.*old.*image|service.*not.*updating|ECS.*rolling.*stuck)",
        "deployment", "aws-ecs", ">=2023-01", "any", "true", 0.85, 0.88,
        "Deregistering an ECS task definition does NOT stop running tasks using it. It only prevents new tasks from using that revision. You must force a new deployment to replace running tasks.",
        [de("Deregister old task definition expecting running tasks to stop",
            "Deregistering only marks the revision as INACTIVE. Running tasks continue indefinitely with the old config.", 0.92),
         de("Update the task definition and wait for ECS to auto-deploy",
            "ECS services don't auto-deploy new task definitions. You must explicitly update the service or force a new deployment.", 0.88)],
        [wa("Force new deployment after updating task definition", 0.95,
            "aws ecs update-service --cluster my-cluster --service my-service --force-new-deployment"),
         wa("Update the service to use the new task definition revision", 0.92,
            "aws ecs update-service --cluster my-cluster --service my-service --task-definition my-task:NEW_REVISION"),
         wa("Use deployment circuit breaker to auto-rollback failed deployments", 0.85,
            "--deployment-configuration 'deploymentCircuitBreaker={enable=true,rollback=true}'")],
    ))

    canons.append(canon(
        "cloud", "gcp-pubsub-exactly-once-not-really", "gcp-pubsub-any",
        "GCP Pub/Sub delivers duplicate messages despite 'exactly-once delivery' being enabled",
        r"(Pub.*Sub.*duplicate|exactly.once.*duplicate|ack.*deadline.*duplicate|redelivery.*Pub.*Sub)",
        "message_delivery", "gcp-pubsub", ">=2023-01", "any", "partial", 0.65, 0.82,
        "GCP Pub/Sub 'exactly-once delivery' only guarantees exactly-once within the ack deadline. If processing takes longer than ack deadline (default 10s), the message is redelivered. Also, exactly-once is only supported on pull subscriptions.",
        [de("Enable exactly-once delivery and assume no duplicates",
            "Exactly-once only works within the ack deadline window. Slow consumers WILL see duplicates. Push subscriptions don't support it at all.", 0.88),
         de("Increase ack deadline to maximum (600s) to avoid redelivery",
            "600s max may still not be enough for slow processing. Also, increases message invisibility window on failure.", 0.72),
         de("Acknowledge message before processing it",
            "If processing fails after ack, the message is lost forever. No redelivery for acknowledged messages.", 0.90)],
        [wa("Implement idempotent message processing using message_id", 0.92,
            "if redis.setnx(f'processed:{message.message_id}', 1, ex=86400): process(message); message.ack()"),
         wa("Use modack to extend deadline during long processing", 0.85,
            "Periodically call modify_ack_deadline() in a background thread while processing"),
         wa("Design consumers to be idempotent regardless of delivery guarantees", 0.95,
            "Use database upserts, idempotency keys, or dedup tables. Never assume exactly-once from any message queue.")],
    ))

    canons.append(canon(
        "cloud", "aws-cloudformation-circular-dependency", "aws-cf-any",
        "Circular dependency between resources: [SecurityGroup, LaunchTemplate, SecurityGroup]",
        r"(Circular dependency between resources|circular.*reference|DependsOn.*circular)",
        "template_error", "aws-cloudformation", ">=2023-01", "any", "true", 0.85, 0.88,
        "CloudFormation circular dependencies often arise from security groups referencing each other, or EC2 instances referencing their own security group. The error message lists the cycle but the fix requires restructuring.",
        [de("Add explicit DependsOn to break the cycle",
            "DependsOn only adds dependencies, never removes them. Adding more DependsOn to a cycle makes it worse.", 0.88),
         de("Merge the circular resources into one resource",
            "Merging security groups loses fine-grained access control and makes the template harder to maintain.", 0.72)],
        [wa("Use SecurityGroupIngress/Egress as separate resources to break SG cycles", 0.95,
            "Instead of inline ingress in SG, create separate AWS::EC2::SecurityGroupIngress resource referencing both SGs"),
         wa("Split the stack into nested stacks with cross-stack references", 0.82,
            "Create SGs in one stack, reference them via Fn::ImportValue in another stack"),
         wa("Use Fn::GetAtt and separate the creation from the rule attachment", 0.88,
            "Create SGs with no rules -> Create rules as separate resources referencing SG IDs")],
    ))

    canons.append(canon(
        "cloud", "gcp-cloud-run-cold-start-large-image", "gcp-cloudrun-any",
        "Cloud Run request takes 30s+ on first invocation due to large container image",
        r"(Cloud Run.*cold start|container.*pull.*slow|Cloud Run.*startup.*timeout|min-instances.*cold)",
        "performance", "gcp-cloudrun", ">=2023-01", "any", "true", 0.85, 0.88,
        "Cloud Run pulls the container image on cold start. Images >1GB can take 10-30s+ to pull. Google's docs recommend small images but don't quantify the cold start penalty per image size.",
        [de("Set min-instances=1 and assume zero cold starts",
            "min-instances keeps 1 instance warm, but concurrent request spikes still trigger cold starts for additional instances.", 0.78),
         de("Use a health check endpoint to keep instances warm",
            "Cloud Run auto-scales to zero regardless of health checks. There's no built-in keep-alive mechanism.", 0.82)],
        [wa("Use multi-stage Docker builds to minimize image size", 0.92,
            "FROM golang:1.21 AS builder ... FROM gcr.io/distroless/static ... COPY --from=builder /app /app"),
         wa("Set min-instances > 0 AND set CPU to 'always allocated' for consistent performance", 0.90,
            "gcloud run deploy --min-instances=2 --cpu-boost --no-cpu-throttling"),
         wa("Use startup CPU boost to reduce cold start latency", 0.85,
            "gcloud run deploy --cpu-boost  # doubles CPU during startup for faster init")],
    ))

    canons.append(canon(
        "cloud", "azure-ad-token-cache-cross-tenant", "azure-ad-any",
        "Azure AD token works for wrong tenant or returns 'AADSTS50020: User account does not exist in tenant'",
        r"(AADSTS50020|cross.*tenant.*token|token.*wrong.*tenant|multi.*tenant.*auth.*fail)",
        "authentication", "azure-ad", ">=2023-01", "any", "true", 0.82, 0.85,
        "MSAL token cache uses authority URL as part of the cache key. If you create multiple ConfidentialClientApplication instances with different tenants but share the same cache, tokens leak across tenants.",
        [de("Use a single shared MSAL token cache for all tenants",
            "Tokens from tenant A may be served for tenant B requests. The cache key includes authority but bugs in cache partitioning cause cross-tenant leaks.", 0.88),
         de("Create a new ConfidentialClientApplication per request",
            "Bypasses caching entirely. Every request does a full token acquisition, adding 200-500ms latency.", 0.72)],
        [wa("Use separate token caches per tenant (partition by tenant_id)", 0.95,
            "cache = msal.SerializableTokenCache(); app = msal.ConfidentialClientApplication(client_id, authority=f'https://login.microsoftonline.com/{tenant_id}', token_cache=cache)"),
         wa("Use MSAL's built-in cache partitioning with partition_key", 0.90,
            "app.acquire_token_for_client(scopes, claims_challenge=None, data={'partition_key': tenant_id})")],
    ))

    canons.append(canon(
        "cloud", "aws-s3-list-objects-1000-limit", "aws-s3-any",
        "S3 list_objects returns only 1000 keys even though bucket has more objects",
        r"(list_objects.*1000|S3.*truncated|IsTruncated.*true|S3.*list.*incomplete|MaxKeys.*1000)",
        "pagination", "aws-s3", ">=2023-01", "any", "true", 0.92, 0.95,
        "S3 ListObjectsV2 returns max 1000 keys per call by default. The 'IsTruncated' flag and 'NextContinuationToken' must be checked. Many tutorials omit the pagination loop, leading to silently incomplete results.",
        [de("Call list_objects_v2 once and use all returned keys",
            "Default MaxKeys is 1000. If bucket has more objects, you silently miss everything beyond the first 1000.", 0.95),
         de("Set MaxKeys to a very large number",
            "MaxKeys cannot exceed 1000 per S3 API spec. Setting it higher is silently capped to 1000.", 0.88)],
        [wa("Use paginator to automatically handle continuation tokens", 0.95,
            "paginator = s3.get_paginator('list_objects_v2'); for page in paginator.paginate(Bucket='my-bucket'): ..."),
         wa("Manually loop with ContinuationToken until IsTruncated is False", 0.90,
            "while True: resp = s3.list_objects_v2(Bucket=b, ContinuationToken=token); if not resp['IsTruncated']: break")],
    ))

    canons.append(canon(
        "cloud", "aws-lambda-tmp-storage-512mb", "aws-lambda-linux",
        "OSError: [Errno 28] No space left on device in AWS Lambda /tmp",
        r"(No space left on device|ENOSPC|Lambda.*/tmp.*full|Errno 28.*Lambda)",
        "resource_limit", "aws-lambda", ">=2023-01", "linux", "true", 0.88, 0.90,
        "Lambda /tmp is limited to 512MB by default (expandable to 10GB since 2022). But /tmp persists across warm invocations! Previous invocation's temp files eat into the next invocation's quota.",
        [de("Increase Lambda memory to get more /tmp space",
            "Lambda memory and /tmp storage are independent. More memory does NOT increase /tmp. You must configure ephemeral storage separately.", 0.92),
         de("Write temp files and assume they're cleaned up between invocations",
            "/tmp is NOT cleaned between warm invocations. Files from previous invocations persist and accumulate.", 0.90)],
        [wa("Clean /tmp at the start of each invocation", 0.92,
            "import shutil, os; [os.remove(os.path.join('/tmp', f)) for f in os.listdir('/tmp')]"),
         wa("Configure ephemeral storage up to 10GB in Lambda config", 0.95,
            "aws lambda update-function-configuration --function-name my-func --ephemeral-storage '{\"Size\": 5120}'"),
         wa("Use S3 or EFS for large file processing instead of /tmp", 0.88,
            "Mount EFS filesystem or stream data to/from S3 instead of downloading to /tmp")],
    ))

    # =====================================================================
    # === LLM / AI SERVICE QUIRKS ===
    # =====================================================================
    canons.append(canon(
        "llm", "openai-function-calling-json-parse-stream", "openai-api-any",
        "json.decoder.JSONDecodeError when parsing OpenAI function call arguments in streaming mode",
        r"(JSONDecodeError.*function.*call|function_call.*argument.*parse|streaming.*tool_calls.*incomplete)",
        "streaming", "openai-api", ">=v1.0", "any", "true", 0.88, 0.90,
        "In streaming mode, function/tool call arguments arrive as partial JSON chunks. Each delta.tool_calls[].function.arguments is a string fragment, not valid JSON. You must concatenate all chunks before parsing.",
        [de("Parse delta.tool_calls[0].function.arguments as JSON per chunk",
            "Each streaming chunk contains a partial JSON string fragment like '{\"na' or 'me\": \"'. Parsing individual chunks always fails.", 0.95),
         de("Wait for finish_reason='function_call' then parse the last chunk",
            "The last chunk doesn't contain the full arguments. You need ALL chunks concatenated. finish_reason='tool_calls' signals completion.", 0.85)],
        [wa("Accumulate argument string chunks, parse only after finish_reason='tool_calls'", 0.95,
            "args_str = ''; for chunk in stream: delta = chunk.choices[0].delta; if delta.tool_calls: args_str += delta.tool_calls[0].function.arguments; # parse after stream ends"),
         wa("Use non-streaming mode for function calling if latency permits", 0.85,
            "response = client.chat.completions.create(stream=False, tools=tools)  # complete JSON in one response"),
         wa("Use structured output mode (response_format) instead of function calling for complex schemas", 0.82,
            "response_format={'type': 'json_schema', 'json_schema': {...}}  # enforced valid JSON output")],
    ))

    canons.append(canon(
        "llm", "temperature-zero-not-deterministic", "llm-api-any",
        "LLM produces different outputs for identical prompts even with temperature=0",
        r"(temperature.*0.*different|deterministic.*LLM|same.*prompt.*different.*output|non.*deterministic.*temperature)",
        "reproducibility", "llm-api", ">=2023-01", "any", "partial", 0.60, 0.85,
        "temperature=0 does NOT guarantee deterministic output. GPU floating point operations are non-deterministic, model weights may be updated, and batching/routing can affect results. OpenAI introduced 'seed' parameter but it's still best-effort.",
        [de("Set temperature=0 and expect identical outputs every time",
            "GPU parallel float operations have non-deterministic rounding. Different GPUs, batch sizes, or model shards produce different softmax distributions.", 0.88),
         de("Use seed parameter and assume perfect reproducibility",
            "OpenAI's seed parameter is 'best-effort'. system_fingerprint changes when infrastructure updates happen, breaking reproducibility.", 0.78)],
        [wa("Use seed parameter AND check system_fingerprint for change detection", 0.85,
            "response = client.chat.completions.create(seed=42, ...); print(response.system_fingerprint)  # track for changes"),
         wa("Implement output caching with (prompt_hash, model, system_fingerprint) as key", 0.90,
            "Cache responses keyed on hash(messages + model + system_fingerprint). Re-generate only on fingerprint change."),
         wa("Design systems to tolerate non-deterministic LLM output instead of depending on reproducibility", 0.92,
            "Use structured output validation, retry with parsing, and fuzzy matching instead of exact output comparison")],
    ))

    canons.append(canon(
        "llm", "tiktoken-count-mismatch-api", "openai-api-any",
        "tiktoken token count doesn't match actual API token usage in response",
        r"(tiktoken.*mismatch|token.*count.*differ|prompt_tokens.*unexpected|context.*length.*exceeded.*estimated)",
        "token_counting", "openai-api", ">=v1.0", "any", "partial", 0.70, 0.82,
        "tiktoken counts raw text tokens but doesn't account for chat message formatting overhead. Each message has ~4 tokens of overhead (role, delimiters). System messages, function definitions, and tool schemas add significant hidden tokens.",
        [de("Use tiktoken.encode(prompt_text) to count total prompt tokens",
            "Chat completions add ~4 tokens per message for role/delimiters, plus tokens for function schemas that aren't in your message text. Real count is always higher.", 0.88),
         de("Calculate context budget as model_max_tokens - tiktoken_count",
            "Underestimating prompt tokens means overestimating available completion tokens, leading to context length exceeded errors.", 0.82)],
        [wa("Use tiktoken with chat message overhead formula", 0.88,
            "tokens = sum(4 + len(enc.encode(m['content'])) for m in messages) + 2  # +2 for assistant reply priming"),
         wa("Use the API's actual token count from response.usage as ground truth for future estimates", 0.90,
            "actual = response.usage.prompt_tokens  # compare with your estimate to calibrate"),
         wa("Reserve 10-15% token budget as safety margin for overhead", 0.85,
            "safe_budget = int(model_max_tokens * 0.85) - estimated_prompt_tokens")],
    ))

    canons.append(canon(
        "llm", "embedding-dimension-mismatch-silent", "embedding-api-any",
        "Cosine similarity returns nonsense results or vector DB rejects insert due to dimension mismatch",
        r"(dimension.*mismatch|vector.*size.*differ|embedding.*dimension.*wrong|InvalidDimension)",
        "embedding", "embedding-api", ">=2023-01", "any", "true", 0.90, 0.92,
        "Different embedding models produce different dimension vectors (OpenAI ada-002=1536, text-embedding-3-small=1536, text-embedding-3-large=3072). Mixing models in the same vector DB index corrupts similarity search silently with no error.",
        [de("Switch embedding model and keep using the existing vector index",
            "New model produces different-dimension or differently-distributed vectors. Similarity scores become meaningless. Some DBs accept any dimension silently.", 0.92),
         de("Truncate or pad vectors to match dimensions",
            "Truncating loses semantic information. Padding with zeros distorts distance calculations. Neither preserves similarity semantics.", 0.88)],
        [wa("Re-embed all documents when changing embedding models", 0.95,
            "Switching models requires full re-indexing. Store original text alongside embeddings for re-embedding."),
         wa("Use model name as part of the vector index name for isolation", 0.90,
            "index_name = f'docs_{model_name}_{dimension}'  # separate index per model"),
         wa("Use OpenAI's dimensions parameter to control output size if supported", 0.82,
            "client.embeddings.create(model='text-embedding-3-small', input=text, dimensions=512)  # Matryoshka embedding")],
    ))

    canons.append(canon(
        "llm", "system-prompt-ignored-long-context", "llm-api-any",
        "LLM ignores system prompt instructions when user message or context is very long",
        r"(system.*prompt.*ignored|instruction.*not.*followed|long.*context.*forget|lost.*in.*middle)",
        "prompt_engineering", "llm-api", ">=2023-01", "any", "partial", 0.65, 0.80,
        "LLMs exhibit 'lost in the middle' effect where instructions at the start of context are weakened by large amounts of content. System prompts lose effectiveness when conversation history or RAG context grows large.",
        [de("Put all instructions in the system prompt and trust they'll be followed",
            "System prompt influence degrades as context length grows. At 50K+ tokens of content, earlier instructions can be effectively forgotten.", 0.82),
         de("Increase context window to fit more instructions",
            "Larger context windows amplify the 'lost in the middle' problem. More tokens = more dilution of instructions.", 0.75)],
        [wa("Repeat critical instructions at the end of the prompt, close to the expected output", 0.90,
            "Place key constraints in both system prompt AND as the final user message: 'Remember: output JSON only'"),
         wa("Use structured output (response_format/json_schema) to enforce format compliance", 0.92,
            "response_format={'type': 'json_schema', 'json_schema': schema}  # model-enforced structure"),
         wa("Chunk long context and process iteratively instead of single mega-prompt", 0.85,
            "Split 100K context into 10K chunks, process each with full instructions, then aggregate results")],
    ))

    canons.append(canon(
        "llm", "rag-chunk-size-vs-embedding-max", "rag-pipeline-any",
        "RAG retrieval returns irrelevant results despite relevant documents existing in the index",
        r"(RAG.*irrelevant|chunk.*too.*large|retrieval.*poor|semantic.*search.*miss|embedding.*truncat)",
        "retrieval", "rag-pipeline", ">=2023-01", "any", "true", 0.82, 0.88,
        "Embedding models have max token limits (e.g., 8191 for ada-002). Text beyond the limit is silently truncated. If chunks are larger than the embedding model's limit, only the beginning is semantically captured. Small chunks lose context.",
        [de("Use large chunk sizes (10K+ tokens) for more context per chunk",
            "Embedding model silently truncates beyond its max tokens. A 10K token chunk with 8191 limit embeds only the first 82%. The answer might be in the truncated part.", 0.85),
         de("Use very small chunks (50-100 tokens) for precision",
            "Small chunks lose surrounding context. 'It was resolved in v2.3' means nothing without knowing what 'it' refers to.", 0.78)],
        [wa("Set chunk size to 50-80% of embedding model's max token limit with overlap", 0.92,
            "chunk_size=512, chunk_overlap=64  # for models with 8191 max tokens. Overlap preserves context boundaries."),
         wa("Use parent-child chunking: embed small chunks but retrieve parent documents", 0.88,
            "Embed 256-token chunks. On retrieval, return the 2048-token parent document containing the matched chunk."),
         wa("Add metadata (title, section headers) to each chunk before embedding", 0.85,
            "chunk_text = f'Document: {title}\\nSection: {header}\\n\\n{chunk}'  # provides context for embedding")],
    ))

    canons.append(canon(
        "llm", "structured-output-hallucinated-enum", "llm-api-any",
        "LLM returns values not in the specified enum when generating structured JSON output",
        r"(hallucinated.*enum|invalid.*enum.*value|JSON.*schema.*violation|structured.*output.*invalid)",
        "structured_output", "llm-api", ">=2023-01", "any", "partial", 0.72, 0.80,
        "Even with JSON mode or function calling, LLMs can hallucinate enum values not in the schema. The model 'understands' the schema but doesn't guarantee constraint satisfaction. Only json_schema response_format with strict:true in OpenAI actually enforces enums.",
        [de("Define enum in function schema and trust the model to respect it",
            "Function calling schemas are treated as suggestions, not constraints. The model can return any string for an enum field.", 0.82),
         de("Use JSON mode (response_format: json_object) and assume schema compliance",
            "JSON mode only guarantees valid JSON syntax, NOT schema compliance. Fields can be missing, wrong type, or have invalid enum values.", 0.88)],
        [wa("Use strict: true with json_schema response_format (OpenAI)", 0.95,
            "response_format={'type': 'json_schema', 'json_schema': {'name': 'output', 'strict': True, 'schema': {...}}}"),
         wa("Validate LLM output against schema and retry on violation", 0.88,
            "for attempt in range(3): output = llm_call(); if validate(output, schema): return output  # retry loop"),
         wa("Post-process enum fields with fuzzy matching to nearest valid value", 0.78,
            "from difflib import get_close_matches; valid = get_close_matches(output_val, enum_values, n=1)")],
    ))

    canons.append(canon(
        "llm", "context-window-overflow-silent-truncation", "llm-api-any",
        "LLM response quality degrades sharply without any error when approaching context limit",
        r"(context.*window.*overflow|quality.*degrad|silent.*truncat|max.*context.*reached|output.*garbled)",
        "context_management", "llm-api", ">=2023-01", "any", "partial", 0.68, 0.82,
        "Some LLM APIs silently truncate input when context limit is exceeded (e.g., older Claude API). Others return errors. Even within limits, quality degrades as you approach the maximum. The 'effective' context is smaller than the 'advertised' context.",
        [de("Fill context to 95% of advertised limit and expect full quality",
            "LLM attention quality degrades significantly in the last 10-20% of context window. 128K context doesn't mean 128K of equally-attended tokens.", 0.82),
         de("Trust that the API will error if context is exceeded",
            "Some APIs silently truncate from the middle or beginning. You get a response but it's based on incomplete context.", 0.78)],
        [wa("Keep context usage under 80% of model's advertised limit", 0.88,
            "effective_limit = int(model_max_context * 0.80)  # reserve 20% for quality"),
         wa("Implement sliding window or summarization for long conversations", 0.92,
            "Keep last N messages + summarize older ones: system_msg = summarize(old_messages) + recent_messages"),
         wa("Pre-check token count and trim from the middle (not the end) of context", 0.85,
            "Keep system prompt + first/last messages. Trim middle of conversation. 'Lost in the middle' means middle has least impact.")],
    ))

    canons.append(canon(
        "llm", "fine-tune-catastrophic-forgetting", "llm-finetuning-any",
        "Fine-tuned model loses base capabilities after training on domain-specific data",
        r"(catastrophic.*forgetting|fine.*tun.*lost.*capabilit|fine.*tun.*degrad|base.*model.*better)",
        "fine_tuning", "llm-finetuning", ">=2023-01", "any", "partial", 0.62, 0.78,
        "Fine-tuning on narrow domain data causes catastrophic forgetting of base model capabilities. The model becomes an expert in your domain but loses general reasoning, instruction following, or other skills.",
        [de("Fine-tune on domain data only without including general examples",
            "Training exclusively on domain data overwrites general capabilities. The model forgets how to follow instructions, do math, or reason about non-domain topics.", 0.85),
         de("Fine-tune for many epochs to maximize domain performance",
            "More epochs = more forgetting. 3-5 epochs is usually optimal. Beyond that, validation loss increases while training loss decreases (overfitting).", 0.82)],
        [wa("Mix domain data with general instruction-following examples (80/20 ratio)", 0.88,
            "training_data = domain_examples + random.sample(general_examples, len(domain_examples) // 4)"),
         wa("Use LoRA/QLoRA instead of full fine-tuning to preserve base capabilities", 0.92,
            "Fine-tune only adapter weights (r=16, alpha=32). Base model weights remain frozen. Merge on inference."),
         wa("Use RAG + few-shot prompting before resorting to fine-tuning", 0.85,
            "Often retrieval-augmented generation with examples achieves similar quality without forgetting risks")],
    ))

    canons.append(canon(
        "llm", "api-response-format-instability", "llm-api-any",
        "LLM API response format changes between calls or after model updates",
        r"(response.*format.*changed|API.*breaking.*change|model.*update.*broke|parsing.*fail.*update)",
        "api_stability", "llm-api", ">=2023-01", "any", "partial", 0.65, 0.78,
        "LLM providers update models silently behind version aliases (e.g., 'gpt-4' points to different snapshots over time). Response formatting, JSON structure, and even reasoning patterns can change without notice.",
        [de("Parse LLM output with rigid regex or exact string matching",
            "Model updates change phrasing, formatting, and structure. Regex that worked yesterday fails after a silent model update.", 0.88),
         de("Use model alias (e.g., 'gpt-4') for production stability",
            "Aliases like 'gpt-4' are redirected to new snapshots periodically. Use pinned versions like 'gpt-4-0613' for stability.", 0.82)],
        [wa("Use pinned model versions (date-stamped) in production", 0.92,
            "model='gpt-4-0613'  # pinned, not 'gpt-4' which changes"),
         wa("Implement robust output parsing with fallbacks and validation", 0.90,
            "try: parse_json(output) except: try: parse_markdown(output) except: raw_text_fallback(output)"),
         wa("Use structured output mode to decouple format from model behavior", 0.88,
            "response_format with strict schema enforcement is more stable across model updates than free-form output")],
    ))

    # =====================================================================
    # === DATA FORMAT QUIRKS ===
    # =====================================================================
    canons.append(canon(
        "data", "csv-embedded-newlines-break-parser", "csv-parser-any",
        "CSV parser produces wrong number of fields or corrupted rows with multiline cell values",
        r"(CSV.*wrong.*field.*count|unexpected.*newline.*CSV|CSV.*corrupt|multiline.*cell.*break)",
        "parsing", "csv-parser", ">=any", "any", "true", 0.88, 0.92,
        "RFC 4180 allows newlines inside quoted fields. Naive line-by-line CSV parsing (split on newline, then split on comma) breaks on any cell containing a newline. Python csv module handles this; pandas read_csv does too, but shell tools like awk/cut don't.",
        [de("Read CSV line-by-line and split on commas",
            "Cells containing commas or newlines within quotes break this approach. A single multi-line cell becomes multiple corrupted rows.", 0.95),
         de("Use awk or cut to extract CSV columns",
            "Shell tools don't understand CSV quoting. A quoted comma is treated as a delimiter. A quoted newline splits the row.", 0.92)],
        [wa("Use a proper CSV parser that handles RFC 4180 (Python csv, pandas)", 0.95,
            "import csv; reader = csv.reader(open('file.csv')); for row in reader: ...  # handles quoted newlines"),
         wa("Use csvkit for shell-based CSV processing", 0.88,
            "csvcut -c 1,3 file.csv  # properly handles quoting, unlike cut -d, -f1,3"),
         wa("Pre-validate CSV with csvclean before processing", 0.82,
            "csvclean file.csv  # reports and optionally fixes quoting issues")],
    ))

    canons.append(canon(
        "data", "json-trailing-comma-parse-error", "json-parser-any",
        "json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes at trailing comma",
        r"(JSONDecodeError.*trailing comma|Expecting property name|trailing comma.*JSON|JSON.*parse.*error.*comma)",
        "parsing", "json-parser", ">=any", "any", "true", 0.92, 0.95,
        "Trailing commas are valid in JavaScript but invalid in JSON (RFC 8259). Many developers write JSON by hand or copy from JS and include trailing commas. JSON.parse and json.loads both reject them.",
        [de("Allow trailing commas because JSON is 'just JavaScript object notation'",
            "JSON is NOT JavaScript. JSON is a strict subset. Trailing commas, single quotes, unquoted keys, and comments are all invalid JSON.", 0.95),
         de("Use eval() or Function() to parse JSON with trailing commas",
            "eval() is a critical security vulnerability for untrusted data. Never use eval() to parse JSON.", 0.98)],
        [wa("Use json5 library for human-written config files that need comments/trailing commas", 0.90,
            "import json5; data = json5.load(open('config.json5'))  # allows trailing commas, comments"),
         wa("Strip trailing commas with regex before parsing (for trusted input only)", 0.82,
            "import re; clean = re.sub(r',\\s*([}\\]])', r'\\1', json_str); data = json.loads(clean)"),
         wa("Use a linter (jsonlint) to validate JSON before processing", 0.88,
            "npx jsonlint file.json  # or: python -m json.tool file.json")],
    ))

    canons.append(canon(
        "data", "utf8-bom-invisible-parse-failure", "text-parser-any",
        "File parsing fails or produces unexpected characters at the beginning despite looking correct in editor",
        r"(BOM.*error|\\xef\\xbb\\xbf|utf-8-sig|unexpected.*character.*beginning|invisible.*byte.*start)",
        "encoding", "text-parser", ">=any", "any", "true", 0.88, 0.90,
        "UTF-8 BOM (Byte Order Mark, 0xEF 0xBB 0xBF) is prepended by Windows editors (Notepad, Excel export). Most editors hide it, but parsers choke: JSON parsers reject it, CSV first column gets corrupted, shebang lines break.",
        [de("Open file as UTF-8 and assume clean content",
            "UTF-8 with BOM inserts 3 invisible bytes at the start. json.loads fails. CSV first header gets \\ufeff prefix. Dict lookups on first column fail.", 0.88),
         de("Manually strip first 3 bytes from file",
            "Only works if BOM is present. Stripping 3 bytes from non-BOM file corrupts the first character.", 0.72)],
        [wa("Open with encoding='utf-8-sig' in Python (auto-strips BOM if present)", 0.95,
            "open('file.csv', encoding='utf-8-sig')  # strips BOM if present, works normally if absent"),
         wa("Use dos2unix or sed to strip BOM from files in bulk", 0.85,
            "sed -i '1s/^\\xEF\\xBB\\xBF//' file.csv  # or: dos2unix --remove-bom file.csv"),
         wa("Configure editors to save as 'UTF-8 without BOM' by default", 0.82,
            "VS Code: 'files.encoding': 'utf8'  # not 'utf8bom'")],
    ))

    canons.append(canon(
        "data", "excel-date-serial-1900-bug", "excel-date-any",
        "Date calculations off by 1 day when converting Excel serial numbers, or Feb 29 1900 appears in data",
        r"(Excel.*date.*off.*1|serial.*number.*1900|Feb.*29.*1900|Lotus.*date.*bug|date.*epoch.*Excel)",
        "date_handling", "excel-date", ">=any", "any", "true", 0.85, 0.88,
        "Excel inherited a deliberate bug from Lotus 1-2-3: it treats 1900 as a leap year (Feb 29, 1900 exists as serial number 60). This makes all serial numbers before March 1, 1900 off by 1 day. Microsoft kept this for backwards compatibility.",
        [de("Convert Excel serial number to date by adding days to Jan 1, 1900",
            "Serial number 1 = Jan 1, 1900 in Excel, but the fake Feb 29 1900 means dates after Feb 28 1900 are correct while earlier dates are off by 1.", 0.82),
         de("Assume all Excel dates are correct after conversion",
            "Any date before March 1, 1900 is off by 1 day. Serial number 60 maps to the non-existent Feb 29, 1900.", 0.78)],
        [wa("Use xlrd, openpyxl, or pandas to read Excel dates (they handle the 1900 bug)", 0.92,
            "import pandas as pd; df = pd.read_excel('file.xlsx')  # automatically handles serial date conversion"),
         wa("If manually converting: subtract 1 from serial numbers <= 60, account for the epoch offset", 0.85,
            "from datetime import datetime, timedelta; date = datetime(1899, 12, 30) + timedelta(days=serial)  # note: Dec 30 not Jan 1"),
         wa("Validate by checking for Feb 29, 1900 as a sentinel for corrupted data", 0.78,
            "if date == datetime(1900, 2, 29): raise ValueError('Excel 1900 leap year bug detected')")],
    ))

    canons.append(canon(
        "data", "timezone-naive-comparison-silent-wrong", "datetime-any",
        "Datetime comparison produces silently wrong results when mixing timezone-aware and naive datetimes",
        r"(can't compare offset-naive|TypeError.*naive.*aware|timezone.*comparison.*wrong|datetime.*timezone.*silent)",
        "datetime", "datetime", ">=any", "any", "true", 0.90, 0.92,
        "Python 3 raises TypeError when comparing aware and naive datetimes. But many ORMs and serializers silently strip timezone info, producing naive datetimes that compare incorrectly. A UTC datetime and a local datetime can appear equal when they're hours apart.",
        [de("Compare datetimes without checking timezone awareness",
            "A naive datetime(2024,1,1,9,0) and an aware datetime(2024,1,1,9,0,tzinfo=UTC) may represent different instants. Python raises TypeError, but some frameworks auto-coerce.", 0.88),
         de("Use datetime.now() (naive) and assume it's UTC",
            "datetime.now() returns local time as naive datetime. datetime.utcnow() returns UTC as naive. Neither has timezone info, so comparisons with aware datetimes fail or are wrong.", 0.85)],
        [wa("Always use timezone-aware datetimes: datetime.now(timezone.utc)", 0.95,
            "from datetime import datetime, timezone; now = datetime.now(timezone.utc)  # NOT datetime.utcnow()"),
         wa("Normalize all datetimes to UTC before comparison or storage", 0.92,
            "stored_dt = aware_dt.astimezone(timezone.utc)  # store UTC, convert to local only for display"),
         wa("Use pendulum or arrow library for safer datetime handling", 0.85,
            "import pendulum; now = pendulum.now('UTC')  # always timezone-aware, easy conversion")],
    ))

    canons.append(canon(
        "data", "yaml-norway-problem-boolean-coercion", "yaml-1.1-any",
        "YAML file silently converts country code 'NO' to boolean False, or version '1.0' to float",
        r"(YAML.*NO.*false|YAML.*boolean.*coerci|Norway.*problem|YAML.*float.*version|YAML.*implicit.*type)",
        "parsing", "yaml-parser", ">=any", "any", "true", 0.92, 0.95,
        "YAML 1.1 aggressively coerces unquoted values: NO/no/off -> False, YES/yes/on -> True, 1.0 -> float, 1_000 -> integer. The 'Norway problem': country code NO becomes boolean False. YAML 1.2 fixed this but most tools use 1.1.",
        [de("Write YAML values without quotes and trust they stay as strings",
            "YAML 1.1 interprets: NO->false, YES->true, null->None, 1.0->float, 0o10->8(octal). Country codes, version numbers, and on/off flags are all affected.", 0.95),
         de("Upgrade to YAML 1.2 parser to fix the problem",
            "Most tools (Ansible, Kubernetes, Docker Compose, GitHub Actions) still use YAML 1.1 parsers. Your files must be compatible with consumers.", 0.82)],
        [wa("Always quote string values that could be misinterpreted", 0.95,
            'country: "NO"  # quoted to prevent boolean coercion; version: "1.0"  # prevents float coercion'),
         wa("Use YAML safe_load and add explicit !!str tags for ambiguous values", 0.88,
            "country: !!str NO  # explicit string tag prevents boolean interpretation"),
         wa("Use JSON for data interchange where type ambiguity is unacceptable", 0.82,
            "JSON has no implicit type coercion. Strings are always quoted. Consider JSON for config shared across tools.")],
    ))

    canons.append(canon(
        "data", "float-precision-json-serialization", "json-float-any",
        "JSON serialized float value 0.1 + 0.2 becomes 0.30000000000000004 causing comparison failures",
        r"(float.*precision|0\.30000000000000004|floating.*point.*JSON|decimal.*round|IEEE 754.*JSON)",
        "serialization", "json-float", ">=any", "any", "true", 0.85, 0.90,
        "IEEE 754 floats cannot represent 0.1 exactly. JSON serializes the full double representation. Downstream consumers comparing 0.3 != 0.30000000000000004 fail. Financial calculations with floats corrupt data silently.",
        [de("Use float for monetary/financial values and round at display time",
            "Rounding at display doesn't fix intermediate calculations. $0.1 + $0.2 stored as float = $0.30000000000000004 in the database.", 0.90),
         de("Round float to 2 decimal places before JSON serialization",
            "round(0.1 + 0.2, 2) == 0.3 in Python, but round(2.675, 2) == 2.67 (not 2.68) due to float representation of 2.675.", 0.82)],
        [wa("Use Decimal type for monetary values, serialize as string in JSON", 0.95,
            'from decimal import Decimal; json.dumps({"amount": str(Decimal("0.10") + Decimal("0.20"))})  # "0.30"'),
         wa("Use integer cents/smallest unit for money (avoid decimals entirely)", 0.92,
            "Store $1.50 as 150 cents (integer). No float precision issues. Convert to display format only at presentation."),
         wa("Use custom JSON encoder with controlled precision for scientific data", 0.82,
            "class PrecisionEncoder(json.JSONEncoder): def default(self, o): return round(o, 10) if isinstance(o, float) else super().default(o)")],
    ))

    canons.append(canon(
        "data", "csv-formula-injection", "csv-export-any",
        "Excel executes formulas when opening CSV exported from web application, enabling code execution",
        r"(CSV.*injection|formula.*injection|=CMD|DDE.*attack|spreadsheet.*injection)",
        "security", "csv-export", ">=any", "any", "true", 0.90, 0.92,
        "CSV cells starting with =, +, -, @ are interpreted as formulas by Excel/Google Sheets. Exported user data containing '=HYPERLINK(evil_url)' or '=CMD|...' executes code when opened. OWASP lists this as an injection vulnerability.",
        [de("Sanitize CSV output by HTML-encoding special characters",
            "HTML encoding doesn't help - Excel doesn't interpret HTML entities. The formula characters =+- must be escaped differently for CSV.", 0.85),
         de("Assume CSV is 'just text' and doesn't need sanitization",
            "Spreadsheet applications auto-execute formulas. A cell starting with = is executed, even if it came from user input.", 0.92)],
        [wa("Prefix dangerous cells with a single quote or tab character", 0.90,
            "if cell.startswith(('=', '+', '-', '@')): cell = \"'\" + cell  # single quote prevents formula execution"),
         wa("Wrap all cell values in double quotes and prepend space to formula-like values", 0.88,
            "if cell.lstrip().startswith(('=', '+', '-', '@', '\\t', '\\r')): cell = ' ' + cell"),
         wa("Serve CSV with Content-Type: text/csv and Content-Disposition: attachment to prevent browser rendering", 0.82,
            "response.headers['Content-Type'] = 'text/csv'; response.headers['Content-Disposition'] = 'attachment; filename=export.csv'")],
    ))

    canons.append(canon(
        "data", "iso8601-duration-parsing-inconsistent", "iso8601-any",
        "ISO 8601 duration P1M parsed as 1 minute instead of 1 month, or vice versa",
        r"(ISO.*8601.*duration.*wrong|P1M.*minute.*month|duration.*parsing.*inconsist|PT.*vs.*P.*duration)",
        "datetime", "iso8601", ">=any", "any", "true", 0.85, 0.88,
        "ISO 8601 durations use M for both months (P1M) and minutes (PT1M). P1M = 1 month, PT1M = 1 minute. The T separator is critical. Many parsers and developers confuse P1M30S (1 month 30 seconds) with PT1M30S (1 minute 30 seconds).",
        [de("Use P1M30S to mean 1 minute and 30 seconds",
            "P1M30S means 1 month and 30 seconds, NOT 1 minute 30 seconds. The T separator is required before time components: PT1M30S.", 0.92),
         de("Parse ISO 8601 durations with simple regex",
            "Duration semantics are complex: P1M = 28-31 days depending on month. P1Y = 365 or 366 days. Simple regex can't capture calendar-dependent semantics.", 0.78)],
        [wa("Always include T separator before time components in durations", 0.95,
            "PT1H30M = 1 hour 30 minutes; P1DT12H = 1 day 12 hours; P1M = 1 month (not 1 minute!)"),
         wa("Use isodate or dateutil library for robust ISO 8601 duration parsing", 0.90,
            "import isodate; duration = isodate.parse_duration('PT1M30S')  # timedelta(seconds=90)"),
         wa("Use total seconds representation for unambiguous duration serialization", 0.82,
            "Store durations as seconds (integer) internally. Convert to ISO 8601 only for API responses.")],
    ))

    canons.append(canon(
        "data", "base64-urlsafe-vs-standard-mismatch", "base64-encoding-any",
        "Base64 decoding fails with 'Invalid character' for URL-transmitted tokens or JWT segments",
        r"(base64.*invalid.*character|base64url.*decode.*fail|\\+.*\\/.*base64.*URL|padding.*base64.*error)",
        "encoding", "base64-encoding", ">=any", "any", "true", 0.88, 0.90,
        "Standard base64 uses +/ characters which are special in URLs. URL-safe base64 uses -_ instead. JWT uses URL-safe base64 WITHOUT padding (no = signs). Mixing these three variants causes silent corruption or decode errors.",
        [de("Use standard base64.b64decode() to decode JWT segments",
            "JWT uses URL-safe base64 WITHOUT padding. Standard b64decode fails on - and _ characters. Adding padding back is also needed.", 0.90),
         de("URL-encode standard base64 before putting in URL parameters",
            "URL encoding turns + into %2B and / into %2F. The result is valid but 33% longer. URL-safe base64 is the correct solution.", 0.72)],
        [wa("Use base64.urlsafe_b64decode() with padding restoration for JWT", 0.95,
            "import base64; padded = segment + '=' * (-len(segment) % 4); base64.urlsafe_b64decode(padded)"),
         wa("Use the correct base64 variant for each protocol", 0.92,
            "Standard (RFC 4648): +/ with =padding; URL-safe (RFC 4648 §5): -_ with =padding; JWT (RFC 7515): -_ WITHOUT padding"),
         wa("Use PyJWT or similar library that handles base64url internally", 0.88,
            "import jwt; decoded = jwt.decode(token, key, algorithms=['HS256'])  # handles base64url internally")],
    ))

    # =====================================================================
    # === SECURITY QUIRKS ===
    # =====================================================================
    canons.append(canon(
        "security", "jwt-alg-none-bypass", "jwt-auth-any",
        "JWT validation bypassed by changing algorithm to 'none' in token header",
        r"(alg.*none.*bypass|JWT.*algorithm.*none|InvalidAlgorithmError|jwt.*unsigned.*accepted)",
        "authentication", "jwt-auth", ">=any", "any", "true", 0.92, 0.95,
        "RFC 7519 defines 'none' as a valid JWT algorithm (unsecured JWS). If the server doesn't explicitly enforce the expected algorithm, an attacker can forge tokens by setting alg:none and removing the signature. Many JWT libraries accepted this by default.",
        [de("Validate JWT without specifying expected algorithms",
            "Without an explicit algorithm whitelist, libraries may accept alg:none tokens. The signature verification is skipped entirely for unsigned tokens.", 0.95),
         de("Check the alg field from the JWT header to decide verification method",
            "Attacker controls the JWT header. Using attacker-supplied alg means they choose the verification algorithm. Classic confused-deputy attack.", 0.92)],
        [wa("Always specify allowed algorithms explicitly in jwt.decode()", 0.98,
            "jwt.decode(token, key, algorithms=['HS256'])  # NEVER omit algorithms parameter"),
         wa("Use asymmetric algorithms (RS256/ES256) and separate signing/verification keys", 0.92,
            "RS256 with private key for signing, public key for verification. Even if alg is changed to HS256, the public key won't produce valid HMAC."),
         wa("Reject tokens with alg:none at the middleware level", 0.90,
            "header = jwt.get_unverified_header(token); if header['alg'] == 'none': raise SecurityError()")],
    ))

    canons.append(canon(
        "security", "bcrypt-silent-truncation-72-bytes", "bcrypt-auth-any",
        "Bcrypt accepts password but silently ignores characters beyond 72 bytes",
        r"(bcrypt.*truncat|bcrypt.*72.*byte|password.*longer.*72|bcrypt.*length.*limit)",
        "authentication", "bcrypt-auth", ">=any", "any", "true", 0.88, 0.90,
        "Bcrypt has a hard 72-byte input limit (not characters - bytes). UTF-8 passwords with multibyte characters hit this limit sooner. Two passwords that share the first 72 bytes but differ after are treated as identical.",
        [de("Use bcrypt for passwords of any length without pre-processing",
            "Passwords longer than 72 bytes are silently truncated. 'MySecurePassword123!+extra100characters' and 'MySecurePassword123!+extra100different' hash identically.", 0.90),
         de("Set a maximum password length of 72 characters",
            "72 bytes != 72 characters for UTF-8. A password with CJK characters or emojis uses 3-4 bytes per character, hitting the 72-byte limit at 18-24 characters.", 0.82)],
        [wa("Pre-hash password with SHA-256 before bcrypt to handle arbitrary lengths", 0.92,
            "import hashlib; prehashed = hashlib.sha256(password.encode()).hexdigest(); bcrypt.hashpw(prehashed.encode(), salt)"),
         wa("Use SHA-256 pre-hash and encode as base64 to stay within 72 bytes", 0.90,
            "prehash = base64.b64encode(hashlib.sha256(password.encode()).digest())  # always 44 bytes"),
         wa("Consider Argon2id which has no practical input length limit", 0.88,
            "from argon2 import PasswordHasher; ph = PasswordHasher(); hash = ph.hash(password)  # no truncation")],
    ))

    canons.append(canon(
        "security", "cors-preflight-cache-stale-auth", "cors-browser-any",
        "CORS preflight succeeds but subsequent request fails with 403, or auth changes aren't reflected",
        r"(CORS.*preflight.*cache|Access-Control-Max-Age.*stale|CORS.*403.*after.*auth|preflight.*cached.*old)",
        "cors", "cors-browser", ">=any", "any", "true", 0.85, 0.88,
        "Access-Control-Max-Age caches preflight responses. If you change CORS config or auth requirements, browsers use the cached preflight result. Chrome caches for up to 2 hours. Users see 'CORS error' for changes that are actually deployed correctly.",
        [de("Deploy CORS change and test immediately in the same browser",
            "Browser caches the old preflight response for Access-Control-Max-Age seconds (default varies by browser, up to 7200s in Chrome).", 0.88),
         de("Set Access-Control-Max-Age to a very high value for performance",
            "High max-age means CORS config changes take hours to propagate to users. Auth requirement changes are invisible until cache expires.", 0.82)],
        [wa("Set Access-Control-Max-Age to a short value (300-600s) during development", 0.90,
            "response.headers['Access-Control-Max-Age'] = '300'  # 5 minutes, balances caching and flexibility"),
         wa("Clear browser cache or use incognito mode to test CORS changes", 0.85,
            "Chrome DevTools -> Application -> Cache -> Clear storage. Or Ctrl+Shift+Delete -> Cached images and files."),
         wa("Include Vary: Origin header to prevent incorrect CORS response caching", 0.92,
            "response.headers['Vary'] = 'Origin'  # ensures different origins get correct CORS headers from CDN/proxy")],
    ))

    canons.append(canon(
        "security", "tls-certificate-chain-ordering", "tls-ssl-any",
        "SSL: CERTIFICATE_VERIFY_FAILED - unable to get local issuer certificate, even though cert is valid",
        r"(CERTIFICATE_VERIFY_FAILED|unable to get local issuer|SSL.*certificate.*chain|intermediate.*cert.*missing)",
        "tls", "tls-ssl", ">=any", "any", "true", 0.90, 0.92,
        "TLS requires the full certificate chain: leaf cert -> intermediate(s) -> root CA. Browsers often cache intermediates and work anyway, but programmatic clients (curl, Python requests, Node.js) fail. The server must send intermediates; the client only trusts root CAs.",
        [de("Install leaf certificate only, assuming clients have intermediate certs",
            "Browsers cache intermediate certs from previous visits. curl, Python, and Node.js don't cache intermediates. They fail on every connection.", 0.92),
         de("Add root CA cert to the server's chain file",
            "Root CA should NOT be in the chain. Clients already have root CAs in their trust store. Including it wastes bandwidth and can confuse some TLS implementations.", 0.72),
         de("Test TLS with a browser and assume all clients will work",
            "Browsers have intermediate certificate caching (AIA fetching). Programmatic clients don't. Browser testing misses missing intermediate cert issues.", 0.88)],
        [wa("Include full chain in order: leaf, intermediate(s), but NOT root", 0.95,
            "cat server.crt intermediate.crt > fullchain.pem  # leaf first, then intermediate(s)"),
         wa("Test with openssl s_client or SSL Labs, not just a browser", 0.92,
            "openssl s_client -connect example.com:443 -showcerts  # verify full chain is sent"),
         wa("Use ACME/certbot which automatically includes the correct chain", 0.88,
            "certbot uses fullchain.pem by default which includes leaf + intermediates in correct order")],
    ))

    canons.append(canon(
        "security", "session-fixation-no-regeneration", "session-auth-any",
        "Session hijacking possible because session ID is not regenerated after login",
        r"(session.*fixation|session.*regenerat|session.*id.*reuse.*login|session.*hijack.*login)",
        "session_management", "session-auth", ">=any", "any", "true", 0.90, 0.92,
        "If the session ID remains the same after login, an attacker who knows the pre-auth session ID (e.g., via URL, XSS, or shared computer) automatically gains authenticated access. Most web frameworks do NOT auto-regenerate session IDs on login.",
        [de("Assume the web framework regenerates session ID on login automatically",
            "Most frameworks (Express, Flask, Django, Spring) do NOT auto-regenerate session IDs on authentication state change. You must do it explicitly.", 0.88),
         de("Create a new session only when the user first visits",
            "The issue isn't session creation timing but that the same session ID survives the authentication boundary. Pre-auth and post-auth must have different IDs.", 0.82)],
        [wa("Explicitly regenerate session ID after successful authentication", 0.95,
            "Flask: session.regenerate(); Django: request.session.cycle_key(); Express: req.session.regenerate(cb)"),
         wa("Invalidate old session and create entirely new one on login", 0.90,
            "Destroy existing session completely, create new session with new ID, then populate with user data"),
         wa("Set session cookies with Secure, HttpOnly, SameSite=Lax attributes", 0.85,
            "response.set_cookie('session', value, httponly=True, secure=True, samesite='Lax')")],
    ))

    canons.append(canon(
        "security", "oauth2-state-parameter-csrf", "oauth2-auth-any",
        "OAuth2 authorization code can be injected by attacker due to missing state parameter validation",
        r"(OAuth.*state.*missing|CSRF.*OAuth|authorization.*code.*inject|OAuth.*state.*validation)",
        "authentication", "oauth2-auth", ">=any", "any", "true", 0.92, 0.95,
        "OAuth2 state parameter prevents CSRF in the authorization flow. Without it, an attacker can trick a user into logging in with the attacker's account (login CSRF) by sending them a crafted callback URL with the attacker's authorization code.",
        [de("Omit state parameter because PKCE is used for security",
            "PKCE prevents authorization code interception but does NOT prevent CSRF/login-CSRF attacks. State and PKCE serve different purposes.", 0.88),
         de("Use a static/predictable state value",
            "State must be unpredictable and tied to the user's session. A static value provides zero CSRF protection.", 0.95)],
        [wa("Generate cryptographic random state, store in session, validate on callback", 0.98,
            "state = secrets.token_urlsafe(32); session['oauth_state'] = state; # in callback: assert request.args['state'] == session.pop('oauth_state')"),
         wa("Use both state AND PKCE together for maximum security", 0.95,
            "State prevents CSRF. PKCE prevents code interception. They are complementary, not alternatives."),
         wa("Use established OAuth libraries (authlib, passport) that handle state automatically", 0.90,
            "Libraries like authlib automatically generate, store, and validate state parameter")],
    ))

    canons.append(canon(
        "security", "content-type-sniffing-xss", "browser-security-any",
        "XSS attack succeeds via uploaded file because browser sniffs content type instead of respecting Content-Type header",
        r"(content.*type.*sniff|X-Content-Type-Options|MIME.*sniff.*XSS|nosniff.*missing)",
        "xss", "browser-security", ">=any", "any", "true", 0.90, 0.92,
        "Browsers may ignore Content-Type header and 'sniff' the actual content. A file served as text/plain but containing <script> tags may be executed as HTML. The X-Content-Type-Options: nosniff header prevents this but is often missing.",
        [de("Serve user-uploaded files with correct Content-Type and assume safety",
            "Without nosniff header, browsers may override Content-Type based on content analysis. A .txt file with HTML content may be rendered as HTML.", 0.88),
         de("Validate file extension to prevent malicious uploads",
            "Extension validation is trivially bypassed. A file named 'image.png' can contain HTML/JS. Content-Type from extension doesn't prevent sniffing.", 0.82)],
        [wa("Add X-Content-Type-Options: nosniff header to all responses", 0.95,
            "response.headers['X-Content-Type-Options'] = 'nosniff'  # prevents MIME sniffing"),
         wa("Serve user uploads from a separate domain/subdomain", 0.92,
            "Serve from uploads.example.com, not example.com. Same-origin policy prevents uploaded content from accessing main site cookies/data."),
         wa("Set Content-Disposition: attachment for all user-uploaded files", 0.88,
            "response.headers['Content-Disposition'] = 'attachment'  # forces download instead of rendering")],
    ))

    canons.append(canon(
        "security", "timing-attack-string-comparison", "crypto-auth-any",
        "Secret comparison vulnerable to timing attack because regular == leaks information via response time",
        r"(timing.*attack|constant.*time.*compar|hmac\.compare_digest|timingSafeEqual|string.*comparison.*secret)",
        "cryptography", "crypto-auth", ">=any", "any", "true", 0.85, 0.88,
        "Regular string comparison (==) short-circuits on first different byte. By measuring response time, attackers can determine how many leading bytes match. For API keys, HMAC signatures, and tokens, this leaks the secret byte-by-byte.",
        [de("Use == to compare API keys or HMAC signatures",
            "== returns false at the first differing byte. Comparing 'abc' to 'axc' is faster than 'abc' to 'abd'. Over thousands of requests, attackers can extract the correct value byte by byte.", 0.85),
         de("Hash both values and compare hashes with ==",
            "Hashing reduces the leak but == comparison of hashes still has timing differences. Use constant-time comparison for the hash comparison too.", 0.72)],
        [wa("Use hmac.compare_digest() for constant-time comparison in Python", 0.95,
            "import hmac; hmac.compare_digest(received_signature, computed_signature)  # constant time"),
         wa("Use crypto.timingSafeEqual() in Node.js", 0.95,
            "const crypto = require('crypto'); crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b))"),
         wa("Ensure both strings are same length before constant-time comparison", 0.88,
            "timingSafeEqual requires equal-length buffers. Different lengths immediately reveal inequality. Pad or hash first.")],
    ))

    canons.append(canon(
        "security", "ssrf-metadata-endpoint-cloud", "cloud-security-any",
        "SSRF attack accesses cloud metadata endpoint (169.254.169.254) via user-supplied URL",
        r"(SSRF.*metadata|169\.254\.169\.254|metadata.*endpoint.*attack|IMDSv1.*ssrf|cloud.*metadata.*leak)",
        "ssrf", "cloud-security", ">=any", "any", "true", 0.92, 0.95,
        "Cloud instances (AWS/GCP/Azure) have a metadata endpoint at 169.254.169.254 that returns IAM credentials, API keys, and instance configuration. If your app fetches user-supplied URLs, attackers can read cloud credentials via SSRF.",
        [de("Block 169.254.169.254 in URL validation regex",
            "Attackers bypass with: decimal IP (2852039166), IPv6 (::ffff:169.254.169.254), DNS rebinding, redirects from allowed domains, or alternate representations.", 0.85),
         de("Use URL parsing to extract hostname and block known-bad IPs",
            "URL parsers are inconsistent. http://169.254.169.254@evil.com, http://[::ffff:a9fe:a9fe], and http://0xa9fea9fe all resolve to the metadata endpoint.", 0.82)],
        [wa("Require IMDSv2 (token-based) on all cloud instances", 0.92,
            "aws ec2 modify-instance-metadata-options --instance-id i-xxx --http-tokens required  # blocks simple SSRF"),
         wa("Resolve DNS and validate the IP address is not private/link-local before fetching", 0.90,
            "import ipaddress; ip = socket.getaddrinfo(hostname, port)[0][4][0]; if ipaddress.ip_address(ip).is_private: reject()"),
         wa("Use network-level controls: block metadata endpoint access from application subnets", 0.88,
            "iptables -A OUTPUT -d 169.254.169.254 -j DROP  # or use VPC network policies to block metadata access")],
    ))

    canons.append(canon(
        "security", "cors-wildcard-with-credentials", "cors-browser-any",
        "CORS request with credentials fails: 'Access-Control-Allow-Origin' cannot be wildcard when credentials flag is true",
        r"(Access-Control-Allow-Origin.*wildcard.*credentials|CORS.*wildcard.*cookie|credentials.*not.*supported.*wildcard)",
        "cors", "cors-browser", ">=any", "any", "true", 0.92, 0.95,
        "When a request includes credentials (cookies, auth headers), the CORS response MUST specify the exact origin, not '*'. Browsers reject wildcard Allow-Origin with credentials. This catches nearly every developer setting up CORS for the first time.",
        [de("Set Access-Control-Allow-Origin: * and Access-Control-Allow-Credentials: true",
            "Browsers explicitly reject this combination. The spec forbids wildcard origin with credentials to prevent credential leaking to arbitrary origins.", 0.95),
         de("Remove Allow-Credentials header to make wildcard work",
            "Without credentials, cookies and auth headers are not sent. Authenticated API calls fail silently with 401.", 0.85)],
        [wa("Echo the request Origin header back as Allow-Origin after validating it", 0.95,
            "origin = request.headers['Origin']; if origin in ALLOWED_ORIGINS: response.headers['Access-Control-Allow-Origin'] = origin"),
         wa("Always include Vary: Origin when reflecting origin to prevent CDN cache poisoning", 0.92,
            "response.headers['Vary'] = 'Origin'  # critical if response passes through CDN or cache"),
         wa("Use a CORS library that handles origin validation correctly", 0.88,
            "Flask-CORS, django-cors-headers, cors (Express) - all handle origin reflection and Vary header automatically")],
    ))

    # =====================================================================
    # === POLICY / SERVICE QUIRKS ===
    # =====================================================================
    canons.append(canon(
        "policy", "github-actions-minutes-private-repo", "github-actions-any",
        "GitHub Actions free minutes exhausted much faster than expected on private repositories",
        r"(Actions.*minutes.*exceeded|billing.*Actions.*private|minute.*multiplier.*Actions|Actions.*spending.*limit)",
        "billing", "github-actions", ">=2023-01", "any", "true", 0.88, 0.90,
        "GitHub Actions minutes have a multiplier for private repos: Linux=1x, macOS=10x, Windows=2x. A 10-minute macOS job costs 100 minutes from your 2000 free minutes. This multiplier is buried in the billing docs, not in the Actions documentation.",
        [de("Assume 2000 free minutes means 2000 minutes of any runner",
            "macOS runners cost 10x. 2000 free minutes = only 200 minutes of macOS CI. A single 10-min macOS build = 100 minutes billed.", 0.92),
         de("Switch from Linux to macOS runners for iOS builds without checking billing impact",
            "macOS runners cost 10x Linux. A pipeline running 20 min/day on macOS exhausts free tier in ~10 days.", 0.88)],
        [wa("Use Linux runners for everything except platform-specific tests", 0.92,
            "Run linting, unit tests, build on Linux. Only use macOS for iOS-specific integration tests."),
         wa("Set a spending limit of $0 to prevent unexpected charges", 0.90,
            "GitHub Settings -> Billing -> Actions -> Spending limit: $0.00  # hard stop when free minutes exhausted"),
         wa("Use self-hosted runners for macOS/Windows heavy workloads", 0.85,
            "Self-hosted runners have no minute limits. Use them for expensive platform-specific CI.")],
    ))

    canons.append(canon(
        "policy", "aws-free-tier-surprise-billing", "aws-billing-any",
        "AWS bill for hundreds of dollars after 'free tier' usage due to hidden limits or expiration",
        r"(AWS.*free tier.*bill|unexpected.*AWS.*charge|free tier.*expired|AWS.*surprise.*bill)",
        "billing", "aws-billing", ">=2023-01", "any", "true", 0.82, 0.85,
        "AWS free tier has three types: 12-month free (expires), always free (with limits), and trials. EC2 t2.micro is 12-month only. Leaving resources running after 12 months = full price. Some services have hidden data transfer costs. EBS volumes are not free.",
        [de("Assume all AWS free tier services are perpetually free",
            "12-month free tier services (EC2, RDS, S3) switch to full pricing after 12 months with no warning. You must actively track your free tier anniversary.", 0.90),
         de("Spin up resources and forget about them since they're free",
            "Free tier has strict limits (750 hrs/month for EC2). Running 2 t2.micro instances exceeds the limit and incurs charges immediately.", 0.85),
         de("Only check EC2 costs, ignore other services",
            "Data transfer, EBS volumes, Elastic IPs (when not attached), CloudWatch, and Route 53 queries all have separate costs that add up.", 0.82)],
        [wa("Set up AWS Budgets with alerts at $1, $5, $10 thresholds", 0.95,
            "AWS Console -> Budgets -> Create budget -> $5/month threshold -> Email alert"),
         wa("Use AWS Cost Explorer daily and tag all resources", 0.90,
            "Tag everything with project/owner. Use Cost Explorer to spot unexpected charges within 24 hours."),
         wa("Enable AWS Organizations SCPs to restrict resource creation in free tier accounts", 0.82,
            "Prevent creation of expensive resource types (GPU instances, large RDS) via Service Control Policies")],
    ))

    canons.append(canon(
        "policy", "docker-hub-pull-rate-limit", "docker-hub-any",
        "toomanyrequests: You have reached your pull rate limit. You may increase the limit by authenticating.",
        r"(toomanyrequests|pull rate limit|429.*docker|Docker Hub.*rate.*limit)",
        "rate_limiting", "docker-hub", ">=2020-11", "any", "true", 0.85, 0.88,
        "Docker Hub limits anonymous pulls to 100/6hr per IP, authenticated free to 200/6hr. CI/CD systems sharing an IP (NAT) quickly exhaust the limit. Kubernetes clusters pulling the same image from multiple nodes multiply the pull count.",
        [de("Authenticate with Docker Hub to get unlimited pulls",
            "Authenticated free accounts get 200/6hr, not unlimited. Only paid Docker Pro/Team/Business get higher limits.", 0.82),
         de("Pull images less frequently to stay under the limit",
            "In Kubernetes, each node independently pulls images. 10 nodes pulling on deploy = 10 pulls even if the image is the same.", 0.78)],
        [wa("Use a registry mirror/proxy (Harbor, JFrog, AWS ECR pull-through cache)", 0.95,
            "ECR pull-through cache: aws ecr create-pull-through-cache-rule --ecr-repository-prefix docker-hub --upstream-registry-url docker.io"),
         wa("Copy frequently-used images to your private registry", 0.92,
            "docker pull nginx:latest && docker tag nginx:latest myregistry.com/nginx:latest && docker push myregistry.com/nginx:latest"),
         wa("Use imagePullPolicy: IfNotPresent in Kubernetes to reduce pulls", 0.88,
            "Set imagePullPolicy: IfNotPresent and use specific tags (not :latest) to leverage node-level image cache")],
    ))

    canons.append(canon(
        "policy", "vercel-serverless-timeout-by-plan", "vercel-any",
        "Vercel serverless function times out at 10s even though code completes in time locally",
        r"(FUNCTION_INVOCATION_TIMEOUT|Vercel.*timeout.*10s|serverless.*function.*timeout|504.*Vercel.*gateway)",
        "platform_limits", "vercel", ">=2023-01", "any", "partial", 0.72, 0.82,
        "Vercel serverless function timeout varies by plan: Hobby=10s, Pro=60s, Enterprise=900s. The Hobby 10s limit is not prominently shown in docs. Database connections, external API calls, and cold starts easily exceed 10s.",
        [de("Optimize function code to run within 10 seconds",
            "10s includes cold start time (1-3s for Node.js, 5-10s for Python/Java). Actual code execution budget is 7-9s. With a database connection, you may have <5s for logic.", 0.82),
         de("Use Edge Functions for longer execution time",
            "Edge Functions have even lower limits (some regions enforce shorter timeouts) and don't support all Node.js APIs. They're for fast, lightweight transformations.", 0.75)],
        [wa("Upgrade to Pro plan for 60s timeout if 10s is insufficient", 0.90,
            "Vercel Pro: $20/month, 60s function timeout. Often the simplest fix for timeout issues."),
         wa("Use background functions (Vercel cron or queued) for long-running tasks", 0.88,
            "Use Vercel's maxDuration in vercel.json and Background Functions for tasks >10s"),
         wa("Move long-running tasks to external services (AWS Lambda, Cloud Functions)", 0.85,
            "Trigger external function via HTTP from Vercel edge. External function has its own timeout limits.")],
    ))

    canons.append(canon(
        "policy", "github-api-abuse-detection-cicd", "github-api-any",
        "GitHub API returns 403 Abuse Detection for legitimate CI/CD automation",
        r"(abuse detection|403.*Forbidden.*abuse|secondary rate limit.*CI|GitHub.*ban.*automation)",
        "rate_limiting", "github-api", ">=2023-01", "any", "partial", 0.68, 0.80,
        "GitHub's abuse detection triggers on patterns, not just rate: creating many PRs quickly, commenting on many issues, rapid content creation, or concurrent identical requests. Legitimate CI/CD tools are frequently flagged.",
        [de("Stay under the documented 5000 req/hr rate limit",
            "Abuse detection is behavior-based, not rate-based. You can be flagged at 50 req/hr if the pattern looks automated (rapid sequential mutations).", 0.85),
         de("Use a GitHub App instead of PAT to avoid abuse detection",
            "GitHub Apps have higher rate limits but are equally subject to abuse detection on mutation endpoints.", 0.78)],
        [wa("Add 1-2 second delays between mutating API calls (create/update/delete)", 0.90,
            "time.sleep(1)  # between each PR creation, comment, or issue update"),
         wa("Use GraphQL for read-heavy workloads (single request for multiple resources)", 0.85,
            "GraphQL queries count as single request. Fetching 100 PRs via REST = 100 requests, via GraphQL = 1."),
         wa("Implement exponential backoff with minimum 60s wait on 403", 0.88,
            "On 403 abuse detection: wait 60s, then 120s, then 240s. Check Retry-After header if present.")],
    ))

    canons.append(canon(
        "policy", "aws-ses-sandbox-silent-drop", "aws-ses-any",
        "AWS SES sends email successfully (200 OK) but recipient never receives it in sandbox mode",
        r"(SES.*sandbox.*not.*received|SES.*email.*missing|SES.*verified.*only|SES.*200.*not.*delivered)",
        "email_delivery", "aws-ses", ">=2023-01", "any", "true", 0.88, 0.92,
        "AWS SES sandbox mode only delivers to verified email addresses. The API returns 200 OK for all sends, but unverified recipients silently never receive the email. No error, no bounce notification. You must request production access.",
        [de("Send test emails and assume SES is working because API returns 200",
            "In sandbox mode, SES returns 200 for ALL sends but only delivers to verified addresses. Check your verified identities list.", 0.92),
         de("Verify just the sender email and start sending to any recipient",
            "Both sender AND recipient must be verified in sandbox mode. Verifying only the sender still silently drops emails to unverified recipients.", 0.88)],
        [wa("Request SES production access to send to any email address", 0.95,
            "AWS Console -> SES -> Account dashboard -> Request production access. Takes 24-48 hours for review."),
         wa("Verify all test recipient emails individually during development", 0.85,
            "aws ses verify-email-identity --email-address test@example.com  # for each test recipient"),
         wa("Use SES configuration sets with SNS notifications to track delivery/bounces", 0.90,
            "Configuration set with delivery/bounce/complaint event destinations reveals what actually happened to sent emails")],
    ))

    canons.append(canon(
        "policy", "cloudflare-workers-cpu-time-limit", "cloudflare-workers-any",
        "Cloudflare Worker exceeds CPU time limit even though wall clock time is well under 30s",
        r"(Worker.*CPU.*time.*exceeded|CPU time limit|Cloudflare.*10ms.*cpu|Worker.*exceeded.*limit)",
        "platform_limits", "cloudflare-workers", ">=2023-01", "any", "partial", 0.72, 0.82,
        "Cloudflare Workers free tier has 10ms CPU time limit (not wall clock time). A request waiting 5s for a fetch() uses ~0ms CPU. But JSON.parse() on a large payload or crypto operations quickly exceed 10ms CPU. Paid plan gets 30s wall clock.",
        [de("Assume 10ms means the Worker must complete in 10 milliseconds wall clock time",
            "CPU time ≠ wall clock time. I/O wait (fetch, KV reads) doesn't count. A Worker can run for 30s wall clock if most time is I/O, but 10ms of pure computation is the limit.", 0.85),
         de("Optimize fetch calls to reduce total execution time",
            "fetch() is I/O and doesn't count toward CPU time. The bottleneck is usually JSON parsing, string manipulation, or crypto operations.", 0.78)],
        [wa("Move CPU-intensive work to a backend service, use Worker only for routing/transformation", 0.90,
            "Worker fetches from origin/backend, does minimal transformation, returns result. Heavy computation stays in backend."),
         wa("Upgrade to Workers Paid ($5/month) for 30s wall clock / 30ms CPU per request", 0.88,
            "Paid Workers: 30s wall clock for HTTP, 15min for Cron Triggers. Much more generous CPU limits."),
         wa("Use streaming responses to avoid large JSON parse operations", 0.82,
            "Use HTMLRewriter or streaming JSON parser instead of loading entire response into memory")],
    ))

    canons.append(canon(
        "policy", "pypi-yanked-package-still-installable", "pypi-pip-any",
        "pip install succeeds for a yanked PyPI package version that was supposed to be removed",
        r"(yanked.*still.*install|pip.*yanked.*version|PyPI.*yank.*available|yanked.*warning.*install)",
        "package_management", "pypi-pip", ">=2023-01", "any", "true", 0.82, 0.85,
        "PyPI yank does NOT delete the package. It only hides it from resolution UNLESS the version is pinned exactly in requirements. 'pip install pkg==1.2.3' still installs yanked 1.2.3. Only 'pip install pkg' (unpinned) skips yanked versions.",
        [de("Yank a package version expecting it to be completely unavailable",
            "Yanking is a soft-delete. Exact version pins (==) still install yanked versions. Lock files with pinned versions continue to work.", 0.88),
         de("Rely on yanking to remove a security vulnerability from circulation",
            "All existing requirements.txt files with pinned versions will continue to install the yanked version. You need to publish a new patched version.", 0.85)],
        [wa("Publish a post-release or patch version with the fix, then yank the bad version", 0.92,
            "Upload pkg==1.2.4 with fix, then yank 1.2.3. Users upgrading get 1.2.4. Existing pins still get 1.2.3 (with pip warning)."),
         wa("Use pip --no-yanked flag or check pip warnings for yanked package notices", 0.85,
            "pip warns on yanked installs since pip 20.0. CI should treat pip warnings as errors: pip install --strict"),
         wa("For critical security issues, file a PyPI deletion request (not just yank)", 0.78,
            "Contact PyPI support for complete deletion of malicious packages. Yank is insufficient for malware.")],
    ))

    canons.append(canon(
        "policy", "npm-install-postinstall-script-risk", "npm-any",
        "npm install runs arbitrary postinstall scripts from untrusted packages, potential supply chain attack",
        r"(postinstall.*script.*malicious|npm.*lifecycle.*script|supply.*chain.*npm|install.*script.*attack)",
        "supply_chain", "npm", ">=any", "any", "partial", 0.70, 0.82,
        "npm runs lifecycle scripts (preinstall, install, postinstall) automatically on install. Malicious packages use postinstall to execute arbitrary code. This runs with the same permissions as the user running npm install.",
        [de("Assume npm packages from popular authors are safe to install",
            "Supply chain attacks target popular packages via typosquatting, account takeover, or dependency confusion. Popular ≠ safe.", 0.85),
         de("Review package code on npmjs.com before installing",
            "npmjs.com shows the published code, but postinstall scripts can download and execute additional code at install time. Static review misses this.", 0.78)],
        [wa("Use --ignore-scripts flag to prevent lifecycle script execution", 0.90,
            "npm install --ignore-scripts  # then manually run build scripts for trusted packages"),
         wa("Use npm audit and enable npm provenance for supply chain verification", 0.85,
            "npm audit --production; npm config set //registry.npmjs.org/:_authToken $TOKEN"),
         wa("Use a lockfile (package-lock.json) and review diffs on dependency updates", 0.88,
            "Always commit package-lock.json. Review lockfile diffs in PRs to catch unexpected dependency changes.")],
    ))

    canons.append(canon(
        "policy", "google-maps-api-billing-change", "google-maps-any",
        "Google Maps API requests returning 'REQUEST_DENIED' or billing error after previously working",
        r"(REQUEST_DENIED|Maps.*billing.*required|Google Maps.*API.*key.*invalid|Maps.*quota.*exceeded)",
        "billing", "google-maps-api", ">=2023-01", "any", "true", 0.85, 0.88,
        "Google Maps Platform requires billing account with credit card since 2018. Free tier gives $200/month credit (~28K map loads). Exceeding this or having payment issues causes silent request denial. API key restrictions can also silently block requests.",
        [de("Use Google Maps API without a billing account since it 'used to be free'",
            "Since June 2018, all Maps APIs require a billing account. Old API keys without billing return REQUEST_DENIED.", 0.92),
         de("Assume $200/month free credit covers all usage",
            "$200/month = ~28,000 Dynamic Maps loads or ~40,000 Geocoding requests. High-traffic sites exceed this quickly. Billing kicks in with no warning.", 0.82)],
        [wa("Set up billing budget alerts at $0, $50, $100 in Google Cloud Console", 0.92,
            "Google Cloud Console -> Billing -> Budgets & alerts -> Create budget with email notifications"),
         wa("Restrict API key by HTTP referrer/IP and API type to prevent abuse", 0.88,
            "Google Cloud Console -> Credentials -> API key -> Application restrictions -> HTTP referrers"),
         wa("Cache geocoding results and use static maps where possible to reduce API calls", 0.85,
            "Geocode addresses once and cache. Use Static Maps API (cheaper) for non-interactive displays.")],
    ))

    # =====================================================================
    # === COMMUNICATION / DOCUMENTATION QUIRKS ===
    # =====================================================================
    canons.append(canon(
        "communication", "github-pr-review-comment-position", "github-api-any",
        "GitHub PR review comment appears on wrong line or API returns 'position is not a valid hunk position'",
        r"(position.*not.*valid.*hunk|PR.*comment.*wrong.*line|pull.*request.*review.*position|422.*Unprocessable.*position)",
        "api_usage", "github-api", ">=2023-01", "any", "true", 0.85, 0.88,
        "GitHub PR review comment 'position' is NOT the file line number. It's the 1-based index within the diff hunk. Line 42 in the file might be position 5 in the diff. Using 'line' parameter (newer API) is simpler but only works for lines visible in the diff.",
        [de("Use file line number as 'position' in PR review comment API",
            "The 'position' parameter is the line index within the diff, not the file. Line 100 in the file might be position 3 in the diff if only 3 lines of context are shown.", 0.92),
         de("Use 'line' parameter on any line in the file",
            "The 'line' parameter only works for lines visible in the diff. Comments on unchanged lines outside the diff context fail with 422.", 0.82)],
        [wa("Use the newer 'line' and 'side' parameters instead of 'position'", 0.90,
            'body = {"body": "comment", "path": "file.py", "line": 42, "side": "RIGHT"}  # RIGHT for new code, LEFT for old'),
         wa("Use 'subject_type': 'file' for comments not tied to specific lines", 0.85,
            'body = {"body": "general comment about this file", "path": "file.py", "subject_type": "file"}'),
         wa("Parse the diff to calculate correct position if you must use the legacy parameter", 0.78,
            "Count lines in the diff hunk from @@ marker to the target line. That count is your position value.")],
    ))

    canons.append(canon(
        "communication", "notion-api-rich-text-block-limit", "notion-api-any",
        "Notion API returns 400 error or silently truncates content when block has too much text",
        r"(Notion.*block.*limit|Notion.*rich.*text.*truncat|Notion.*2000.*character|Notion.*API.*body.*too.*large)",
        "api_limits", "notion-api", ">=2023-01", "any", "true", 0.85, 0.88,
        "Notion API limits rich text per block to 2000 characters. A single paragraph block cannot exceed this. The API either returns 400 or silently truncates. Also, page content is limited to 100 blocks per API call (pagination required).",
        [de("Send a large text block assuming it will be stored as-is",
            "Notion truncates at 2000 characters per rich text array element and 100 blocks per append call. Large documents are silently cut off.", 0.88),
         de("Append all blocks in a single API call",
            "Maximum 100 blocks per append_block_children call. Documents with more blocks need paginated appends.", 0.82)],
        [wa("Split text into 2000-character chunks across multiple paragraph blocks", 0.92,
            "chunks = [text[i:i+2000] for i in range(0, len(text), 2000)]; blocks = [{'paragraph': {'rich_text': [{'text': {'content': c}}]}} for c in chunks]"),
         wa("Batch block appends in groups of 100", 0.88,
            "for i in range(0, len(blocks), 100): notion.blocks.children.append(page_id, children=blocks[i:i+100])"),
         wa("Use Notion's toggle blocks for very long content to keep pages manageable", 0.80,
            "Wrap long content sections in toggle blocks. Each toggle can contain sub-blocks with their own 2000-char limits.")],
    ))

    canons.append(canon(
        "communication", "email-spf-dkim-alignment-spam", "email-delivery-any",
        "Emails sent via API land in spam despite valid SPF and DKIM because of alignment failure",
        r"(SPF.*alignment|DKIM.*alignment|DMARC.*fail.*alignment|email.*spam.*SPF.*pass|Authentication-Results.*fail)",
        "email_delivery", "email-delivery", ">=any", "any", "true", 0.85, 0.90,
        "DMARC requires 'alignment': the domain in SPF/DKIM must match the From header domain. Sending from user@example.com via SendGrid (SPF passes for sendgrid.net, not example.com) fails DMARC alignment even though SPF itself passes.",
        [de("Set up SPF and DKIM and assume emails won't be marked as spam",
            "SPF and DKIM can both pass independently but DMARC still fails if neither aligns with the From domain. SPF must pass for the From domain, not just the envelope sender.", 0.88),
         de("Use email service provider's default sending domain",
            "Sending from user@example.com via service's domain means SPF passes for the service domain, not yours. DMARC alignment fails.", 0.85)],
        [wa("Configure custom DKIM signing with your domain on the email service provider", 0.95,
            "Add CNAME records for DKIM: selector._domainkey.example.com -> service-provided-value. This makes DKIM align with your From domain."),
         wa("Set up custom Return-Path domain for SPF alignment", 0.90,
            "Configure bounce subdomain: bounces.example.com CNAME to service's domain. Envelope sender aligns with From domain."),
         wa("Start with DMARC p=none to monitor before enforcing", 0.85,
            "v=DMARC1; p=none; rua=mailto:dmarc@example.com  # monitor alignment failures before setting p=reject")],
    ))

    canons.append(canon(
        "communication", "discord-bot-embed-field-limits", "discord-api-any",
        "Discord API rejects message embed with 400 Bad Request due to exceeding undocumented limits",
        r"(embed.*limit|Discord.*embed.*400|embed.*field.*exceed|Discord.*embed.*too.*large)",
        "api_limits", "discord-api", ">=v10", "any", "true", 0.88, 0.90,
        "Discord embeds have multiple undocumented or hard-to-find limits: 25 fields per embed, 256 chars per field name, 1024 chars per field value, 4096 chars for description, 6000 chars total per embed, 10 embeds per message. Exceeding any limit returns generic 400.",
        [de("Build large embeds without checking individual field limits",
            "Discord returns generic 400 Bad Request without specifying which limit was exceeded. You must validate all limits client-side.", 0.88),
         de("Put all information in embed description to avoid field limits",
            "Description is limited to 4096 characters AND counts toward the 6000-character total embed limit. Large descriptions leave no room for fields.", 0.82)],
        [wa("Validate all embed limits before sending", 0.95,
            "title<=256, description<=4096, fields<=25, field.name<=256, field.value<=1024, footer<=2048, total<=6000 chars"),
         wa("Split large content across multiple embeds (up to 10 per message)", 0.88,
            "If content exceeds single embed limits, distribute across multiple embeds in one message (max 10)."),
         wa("Use pagination with reaction-based navigation for very large datasets", 0.82,
            "Send one embed at a time with prev/next reaction buttons. Update embed content on reaction.")],
    ))

    canons.append(canon(
        "communication", "jira-api-pagination-breaking-change", "jira-api-any",
        "Jira REST API pagination returns incomplete results or different behavior between v2 and v3",
        r"(Jira.*pagination.*incomplete|Jira.*startAt.*maxResults|Jira.*API.*v2.*v3.*differ|Jira.*search.*missing)",
        "api_pagination", "jira-api", ">=v2", "any", "true", 0.82, 0.85,
        "Jira REST API v2 and v3 have different pagination behaviors. v2 returns 'total' which can change between pages (as issues are created/modified). v3 sometimes omits 'total'. maxResults is capped server-side (usually 50-100) regardless of requested value.",
        [de("Set maxResults=1000 to get all issues in one request",
            "Jira server silently caps maxResults to 50-100 (configurable by admin). You get at most 100 results regardless of what you request.", 0.88),
         de("Use 'total' field to determine when pagination is complete",
            "In Jira v3, 'total' may be absent. In v2, 'total' can change between page requests as issues are created/modified mid-pagination.", 0.82)],
        [wa("Paginate until returned results count < maxResults (not based on 'total')", 0.92,
            "while True: results = jira_search(startAt=offset, maxResults=50); if len(results) < 50: break; offset += 50"),
         wa("Use JQL with ORDER BY and createdDate filter for stable pagination", 0.85,
            "JQL: 'project = X ORDER BY created ASC' with startAt pagination. Ordering ensures consistent page contents."),
         wa("Use Jira's scroll API (experimental) for large result sets", 0.78,
            "For Jira Cloud: use the /search endpoint with 'expand' and pagination tokens instead of offset-based pagination")],
    ))

    canons.append(canon(
        "communication", "confluence-storage-vs-editor-format", "confluence-api-any",
        "Confluence API content renders incorrectly or loses formatting when using wrong format type",
        r"(Confluence.*storage.*format|Confluence.*editor.*format|XHTML.*storage.*body|Confluence.*rendering.*broken)",
        "api_usage", "confluence-api", ">=v2", "any", "true", 0.82, 0.85,
        "Confluence has two content formats: 'storage' (XHTML-based, what the API returns) and 'editor' (what users see). They are NOT interchangeable. Posting editor format to storage API corrupts content. Macros use storage format exclusively.",
        [de("Post HTML directly to Confluence API body.storage.value",
            "Confluence storage format is NOT regular HTML. It uses custom XHTML with ac: and ri: namespaces for macros. Regular HTML tags may work but macros, tables, and mentions require storage format.", 0.85),
         de("Read content from API and display directly as HTML in another app",
            "Storage format contains Confluence-specific XHTML (ac:structured-macro, ri:attachment). Rendering this as HTML in a non-Confluence context shows broken markup.", 0.82)],
        [wa("Use Confluence REST API's body.view for rendered HTML, body.storage for editing", 0.92,
            "GET /content/123?expand=body.view  # rendered HTML for display; body.storage for programmatic editing"),
         wa("Use the /contentbody/convert endpoint to transform between formats", 0.88,
            "POST /contentbody/convert/storage {value: '<p>text</p>', representation: 'editor'}  # converts editor -> storage"),
         wa("Use Atlassian Document Format (ADF) for Confluence Cloud v2 API", 0.82,
            "Confluence Cloud v2 API uses ADF (JSON) instead of XHTML storage format. Check API version before choosing format.")],
    ))

    canons.append(canon(
        "communication", "teams-webhook-connector-deprecation", "teams-api-any",
        "Microsoft Teams incoming webhook connector returns 404 or stops working after connector deprecation",
        r"(Teams.*webhook.*deprecated|Teams.*connector.*404|O365.*connector.*end.*of.*life|Teams.*webhook.*fail)",
        "api_deprecation", "teams-api", ">=2024-01", "any", "partial", 0.72, 0.80,
        "Microsoft deprecated Office 365 Connectors for Teams webhooks in 2024, moving to Workflows (Power Automate) instead. Existing webhooks may stop working. The new Workflows-based webhooks have a different URL format and payload structure.",
        [de("Continue using existing O365 Connector webhook URLs indefinitely",
            "Microsoft is deprecating O365 Connectors. Existing URLs will stop working after the retirement date. New connectors can no longer be created in many tenants.", 0.85),
         de("Use the same payload format with new Workflows webhook URL",
            "Workflows webhooks expect Adaptive Card JSON format, not the old MessageCard format used by O365 Connectors. Payload format is completely different.", 0.82)],
        [wa("Migrate to Workflows (Power Automate) based webhooks", 0.90,
            "Teams -> channel -> Workflows -> 'Post to a channel when a webhook request is received'. Use the new URL with Adaptive Card format."),
         wa("Use Adaptive Card JSON format for new webhook payloads", 0.88,
            '{"type": "message", "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive", "content": {"type": "AdaptiveCard", "$schema": "http://adaptivecards.io/schemas/adaptive-card.json", "version": "1.4", "body": [{"type": "TextBlock", "text": "Hello"}]}}]}'),
         wa("Use Microsoft Graph API for more reliable Teams integration", 0.82,
            "Graph API: POST /teams/{team-id}/channels/{channel-id}/messages for programmatic message posting")],
    ))

    canons.append(canon(
        "communication", "github-webhook-delivery-timeout-retry", "github-webhook-any",
        "GitHub webhook delivers same event multiple times because endpoint is slow or returns non-2xx",
        r"(GitHub.*webhook.*retry|webhook.*deliver.*duplicate|webhook.*timeout.*redeliver|X-GitHub-Delivery.*duplicate)",
        "webhook_reliability", "github-webhook", ">=2023-01", "any", "true", 0.85, 0.88,
        "GitHub webhooks timeout after 10 seconds and retry failed deliveries. There's no configurable retry policy. Slow endpoints receive duplicate deliveries. The X-GitHub-Delivery header is unique per delivery attempt, not per event.",
        [de("Process webhook synchronously and return 200 after completion",
            "If processing takes >10s, GitHub considers the delivery failed and retries. You get duplicate processing of the same event.", 0.88),
         de("Use X-GitHub-Delivery header as idempotency key",
            "X-GitHub-Delivery is unique per delivery ATTEMPT, not per event. Retries have different delivery IDs. Use the event payload's action+id for dedup.", 0.82)],
        [wa("Return 200 immediately and process webhook asynchronously", 0.95,
            "Enqueue the raw webhook payload for background processing. Return 200 within 1 second."),
         wa("Use event ID from payload (not delivery header) for idempotency", 0.90,
            "Dedup key: f'{event_type}:{payload[\"action\"]}:{payload[\"id\"]}'  # unique per logical event"),
         wa("Check webhook delivery logs in GitHub repo settings for debugging", 0.82,
            "Settings -> Webhooks -> Recent Deliveries shows each attempt with request/response details")],
    ))

    canons.append(canon(
        "communication", "sendgrid-batch-partial-failure-silent", "sendgrid-api-any",
        "SendGrid batch send returns 202 Accepted but some recipients don't receive email",
        r"(SendGrid.*partial.*fail|SendGrid.*202.*not.*delivered|SendGrid.*batch.*missing|SendGrid.*silent.*drop)",
        "email_delivery", "sendgrid-api", ">=v3", "any", "partial", 0.70, 0.82,
        "SendGrid's v3 mail/send API returns 202 Accepted (queued) not 200 (sent). A 202 means SendGrid accepted the request, not that delivery succeeded. Batch sends with invalid/bounced recipients silently skip those recipients. No per-recipient status in the API response.",
        [de("Assume 202 response means all recipients will receive the email",
            "202 = queued for sending, not delivered. Invalid addresses, bounced domains, and spam-flagged recipients are silently dropped after queuing.", 0.88),
         de("Send to large batches without checking bounce/suppression lists",
            "SendGrid maintains a suppression list. Addresses on it are silently skipped. Sending to previously-bounced addresses hurts your sender reputation.", 0.82)],
        [wa("Set up Event Webhooks to track per-recipient delivery status", 0.95,
            "SendGrid Settings -> Event Webhooks -> Enable delivered, bounced, dropped events. Track delivery per recipient."),
         wa("Check suppression list before sending batches", 0.88,
            "GET /v3/suppression/bounces, /v3/suppression/blocks, /v3/suppression/spam_reports  # check before sending"),
         wa("Use personalizations array for per-recipient tracking", 0.85,
            "Each personalization gets a unique message_id. Use this to track delivery status per recipient group.")],
    ))

    canons.append(canon(
        "communication", "slack-rate-limit-per-method-not-global", "slack-api-any",
        "Slack API returns 429 Too Many Requests on one method while other methods work fine",
        r"(Slack.*429|Slack.*rate.*limit|Slack.*too.*many.*requests|Slack.*Retry-After)",
        "rate_limiting", "slack-api", ">=2023-01", "any", "true", 0.85, 0.88,
        "Slack rate limits are per-method and per-workspace, not global. chat.postMessage has ~1 req/sec per channel. conversations.list has different limits. Hitting the limit on one method doesn't affect others. The Retry-After header tells you exactly how long to wait.",
        [de("Implement a single global rate limiter for all Slack API calls",
            "Rate limits are per-method. A global limiter is either too restrictive (slows unaffected methods) or too loose (still hits per-method limits).", 0.82),
         de("Retry immediately on 429 response",
            "Immediate retry will also be rate-limited. Always respect the Retry-After header value.", 0.88)],
        [wa("Implement per-method rate limiting using Slack's published tier limits", 0.92,
            "Tier 1: 1/min, Tier 2: 20/min, Tier 3: 50/min, Tier 4: 100/min. chat.postMessage is Tier 2-3 depending on context."),
         wa("Always respect the Retry-After header on 429 responses", 0.95,
            "retry_after = int(response.headers.get('Retry-After', 1)); time.sleep(retry_after)"),
         wa("Use Slack's Web API with built-in rate limit handling (slack_sdk)", 0.88,
            "from slack_sdk import WebClient; client = WebClient(token=token)  # automatically handles rate limits with retries")],
    ))

    # =====================================================================
    # === ROS2 EXPANSION ===
    # =====================================================================
    canons.append(canon(
        "ros2", "qos-incompatible-silent-drop", "humble-linux",
        "ROS2 subscriber receives no messages from publisher despite both running with no errors",
        r"(QoS.*incompatib|Requested incompatible QoS|no.*messages.*received|subscriber.*silent|QoS.*mismatch)",
        "communication", "ros2", "humble", "linux", "true", 0.90, 0.92,
        "ROS2 QoS (Quality of Service) settings must be compatible between publisher and subscriber. A RELIABLE publisher and BEST_EFFORT subscriber work, but BEST_EFFORT publisher + RELIABLE subscriber silently drops all messages with no error by default.",
        [de("Use default QoS for both publisher and subscriber",
            "Default QoS is RELIABLE+VOLATILE for most message types but BEST_EFFORT+VOLATILE for sensor data. Mixing sensor publishers with standard subscribers silently fails.", 0.88),
         de("Set both publisher and subscriber to RELIABLE",
            "Works but RELIABLE over lossy networks (WiFi, multi-robot) causes message queuing and latency spikes. Sensor data becomes stale.", 0.75)],
        [wa("Use compatible QoS: publisher reliability >= subscriber reliability", 0.95,
            "pub_qos = QoSProfile(reliability=RELIABLE); sub_qos = QoSProfile(reliability=BEST_EFFORT)  # RELIABLE pub -> BEST_EFFORT sub is OK"),
         wa("Use QoSProfile.sensor_data for all sensor topics consistently", 0.90,
            "from rclpy.qos import qos_profile_sensor_data; pub = node.create_publisher(Image, 'camera', qos_profile_sensor_data)"),
         wa("Use 'ros2 topic info -v /topic' to debug QoS mismatches", 0.88,
            "ros2 topic info -v /camera/image  # shows publisher and subscriber QoS profiles side by side")],
    ))

    canons.append(canon(
        "ros2", "lifecycle-node-transition-ordering", "humble-linux",
        "ROS2 lifecycle node fails during transition with 'transition is not valid from current state'",
        r"(transition.*not.*valid|lifecycle.*state.*error|invalid.*transition|configure.*before.*activate)",
        "lifecycle", "ros2", "humble", "linux", "true", 0.88, 0.90,
        "ROS2 lifecycle nodes must follow strict state transitions: unconfigured->configuring->inactive->activating->active. You cannot skip states (e.g., unconfigured->active). The 'configure' transition must complete before 'activate' can be called.",
        [de("Call activate immediately after creating the lifecycle node",
            "The node starts in 'unconfigured' state. You must call configure() first, wait for it to reach 'inactive', then call activate().", 0.92),
         de("Assume transition callbacks are synchronous and immediate",
            "Transition callbacks (on_configure, on_activate) can fail. If on_configure returns FAILURE, the node stays unconfigured. You must check return codes.", 0.85)],
        [wa("Follow the full transition sequence with state verification", 0.95,
            "node.trigger_configure(); assert node.get_state() == State.INACTIVE; node.trigger_activate(); assert node.get_state() == State.ACTIVE"),
         wa("Implement on_configure/on_activate callbacks with proper error handling", 0.90,
            "def on_configure(self, state): try: self.setup_hardware(); return TransitionCallbackReturn.SUCCESS except: return TransitionCallbackReturn.FAILURE"),
         wa("Use launch_ros lifecycle node launcher for automated transitions", 0.85,
            "Use lifecycle_node launch actions with 'configure' and 'activate' events in launch files")],
    ))

    canons.append(canon(
        "ros2", "tf2-extrapolation-into-future", "humble-linux",
        "tf2.ExtrapolationException: Lookup would require extrapolation into the future",
        r"(ExtrapolationException|extrapolation.*future|tf2.*lookup.*future|transform.*not.*yet.*available)",
        "transforms", "ros2", "humble", "linux", "true", 0.88, 0.92,
        "tf2 transform lookup fails when requesting a transform at a timestamp newer than the latest available transform. Common when sensor data timestamp is slightly ahead of tf broadcaster, or when using sim_time with clock skew between nodes.",
        [de("Use rospy.Time.now() / self.get_clock().now() as lookup time",
            "Current time may be ahead of the latest published transform. Transform publishers have latency. Requesting 'now' often extrapolates into the future.", 0.88),
         de("Increase tf buffer size to store more transforms",
            "Buffer size stores history, not future. The issue is timing, not storage. More history doesn't help when the requested time is in the future.", 0.82)],
        [wa("Use tf2_ros.Buffer.lookup_transform with timeout for blocking wait", 0.92,
            "transform = tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time(), timeout=Duration(seconds=1.0))"),
         wa("Use Time(0) to get the latest available transform instead of a specific timestamp", 0.90,
            "transform = tf_buffer.lookup_transform('map', 'base_link', rclpy.time.Time())  # latest available, no extrapolation"),
         wa("When using sim_time, ensure all nodes use use_sim_time:=true consistently", 0.85,
            "ros2 launch my_pkg my_launch.py use_sim_time:=true  # all nodes must agree on time source")],
    ))

    canons.append(canon(
        "ros2", "colcon-symlink-install-stale-launch", "humble-linux",
        "Changes to launch files or config not reflected after rebuild with colcon --symlink-install",
        r"(symlink.*install.*stale|launch.*file.*not.*updated|colcon.*symlink.*old.*config|install.*not.*refresh)",
        "build_system", "ros2", "humble", "linux", "true", 0.85, 0.88,
        "--symlink-install creates symlinks for Python files and launch files but NOT for compiled C++ artifacts or generated files. Also, newly added files require a full rebuild to create the symlink. Deleted files leave stale symlinks.",
        [de("Use --symlink-install and expect all file changes to be reflected automatically",
            "Only existing Python/launch files are symlinked. New files, CMakeLists.txt changes, and generated files require colcon build to update.", 0.85),
         de("Delete install/ directory and rebuild to fix stale symlinks",
            "Works but is slow. You also need to delete build/ for some cases. A targeted rebuild of the affected package is faster.", 0.72)],
        [wa("Run 'colcon build --packages-select <pkg>' after adding new files", 0.92,
            "colcon build --symlink-install --packages-select my_package  # rebuilds only the affected package"),
         wa("Source install/setup.bash after every rebuild", 0.90,
            "source install/setup.bash  # re-source after rebuild to pick up new packages and files"),
         wa("For C++ changes, always run colcon build (symlink-install doesn't help for compiled code)", 0.88,
            "colcon build --packages-select my_cpp_pkg --cmake-args -DCMAKE_BUILD_TYPE=Release")],
    ))

    canons.append(canon(
        "ros2", "action-server-preemption-race", "humble-linux",
        "ROS2 action goal preemption causes crash or undefined behavior when new goal arrives during execution",
        r"(action.*preempt.*race|goal.*cancel.*crash|action.*server.*concurrent|goal.*handle.*invalid)",
        "actions", "ros2", "humble", "linux", "true", 0.85, 0.88,
        "ROS2 action servers don't automatically handle goal preemption. When a new goal arrives while executing a previous one, both execute concurrently unless you explicitly implement preemption logic in handle_goal and execute callbacks.",
        [de("Assume new goals automatically cancel previous goals",
            "Unlike ROS1 actionlib, ROS2 action servers do NOT auto-preempt. Multiple goals execute simultaneously unless you explicitly manage goal lifecycle.", 0.90),
         de("Cancel the previous goal in handle_goal callback",
            "handle_goal is called before the new goal starts executing. Canceling the old goal here creates a race condition if the old execute callback hasn't checked for cancellation yet.", 0.82)],
        [wa("Use a single-goal policy: reject or queue new goals while one is executing", 0.90,
            "def handle_goal(self, goal_handle): if self._executing: return GoalResponse.REJECT; return GoalResponse.ACCEPT"),
         wa("Implement preemption with threading lock in execute callback", 0.88,
            "In execute: periodically check if goal_handle.is_cancel_requested or if a new goal has been accepted. Clean up and return CANCELED."),
         wa("Use goal_handle.status to track and manage concurrent goals explicitly", 0.85,
            "Maintain a list of active goal handles. In handle_goal, cancel previous goals and wait for their execute callbacks to finish.")],
    ))

    canons.append(canon(
        "ros2", "parameter-callback-composed-nodes", "humble-linux",
        "ROS2 parameter change callback not firing in composed (component) nodes",
        r"(parameter.*callback.*not.*fir|composed.*node.*parameter|component.*parameter.*event|on_set_parameters.*silent)",
        "parameters", "ros2", "humble", "linux", "true", 0.82, 0.88,
        "Parameter callbacks in composed nodes can silently fail when multiple component nodes register callbacks. The parameter event publisher topic is shared, and callback ordering depends on composition order. Also, add_on_set_parameters_callback only fires for set_parameter, not declare_parameter.",
        [de("Register parameter callback and expect it to fire on declare_parameter",
            "add_on_set_parameters_callback only triggers on set_parameter/set_parameters calls, NOT on declare_parameter with initial value.", 0.88),
         de("Use a single parameter callback for all parameters in a composed container",
            "Each component node has its own parameter namespace. Callbacks are per-node, not per-container. But parameter events from other nodes in the composition can interfere.", 0.82)],
        [wa("Use add_on_set_parameters_callback and set values explicitly after declaration", 0.90,
            "self.declare_parameter('speed', 1.0); self.add_on_set_parameters_callback(self.param_cb); # callback fires on future set_parameter calls"),
         wa("Use parameter event subscribers for cross-node parameter monitoring", 0.85,
            "from rcl_interfaces.msg import ParameterEvent; self.create_subscription(ParameterEvent, '/parameter_events', self.param_event_cb, 10)"),
         wa("Separate parameter namespaces explicitly in composed nodes", 0.88,
            "Use node name as namespace: Node('my_node', namespace='robot1', parameter_overrides=[...])")],
    ))

    canons.append(canon(
        "ros2", "bag-recording-sim-time-clock-skew", "humble-linux",
        "ROS2 bag recording timestamps don't match message timestamps when using sim_time",
        r"(rosbag.*timestamp.*mismatch|bag.*sim.*time.*skew|bag.*recording.*time.*wrong|rosbag.*clock.*drift)",
        "recording", "ros2", "humble", "linux", "true", 0.82, 0.85,
        "ros2 bag record uses wall clock for recording timestamps by default, even when nodes use sim_time. Messages are recorded with wall-clock receive time, not the sim_time publish time. This causes misalignment on playback.",
        [de("Record bag and assume timestamps match simulation time",
            "ros2 bag record uses wall clock for the bag metadata timestamps. Sim_time message headers have correct sim_time but the bag index uses wall clock.", 0.85),
         de("Use --use-sim-time flag on ros2 bag record",
            "This changes the bag recorder's clock to sim_time but can cause recording gaps if clock publishes are delayed or irregular.", 0.78)],
        [wa("Use --use-sim-time with a reliable clock source (e.g., Gazebo clock)", 0.88,
            "ros2 bag record --use-sim-time /topic1 /topic2 /clock  # always record /clock topic"),
         wa("Always record the /clock topic alongside other topics", 0.92,
            "ros2 bag record -a --include-hidden-topics  # or explicitly: ros2 bag record /clock /cmd_vel /scan"),
         wa("Use message header timestamps (not bag timestamps) for time-critical analysis", 0.85,
            "When processing bag data, use msg.header.stamp not the bag receive timestamp for accurate timing")],
    ))

    canons.append(canon(
        "ros2", "dds-discovery-vlan-multicast", "humble-linux",
        "ROS2 nodes on different VLANs or subnets cannot discover each other",
        r"(DDS.*discovery.*fail|multicast.*blocked|ROS2.*node.*not.*found|DDS.*VLAN|RTPS.*discovery.*timeout)",
        "networking", "ros2", "humble", "linux", "true", 0.85, 0.88,
        "ROS2 DDS discovery relies on UDP multicast (239.255.0.1:7400). Corporate networks, VLANs, and cloud VPCs often block multicast. Nodes on different subnets can't discover each other without explicit peer configuration.",
        [de("Assume ROS2 nodes on the same network will auto-discover each other",
            "DDS multicast discovery requires multicast routing between subnets. Most enterprise networks, VPNs, and cloud VPCs block multicast.", 0.88),
         de("Switch DDS implementations to fix discovery issues",
            "All DDS implementations (FastDDS, CycloneDDS, Connext) use the same multicast discovery by default. Switching DDS doesn't fix network-level multicast blocking.", 0.78)],
        [wa("Configure DDS peer discovery with explicit IP addresses (unicast)", 0.92,
            "CycloneDDS: <Peers><Peer address='192.168.1.100'/></Peers> in cyclonedds.xml; export CYCLONEDDS_URI=cyclonedds.xml"),
         wa("Use FastDDS Discovery Server for large networks without multicast", 0.90,
            "fastdds discovery -i 0 -l 192.168.1.1 -p 11811  # run discovery server; set ROS_DISCOVERY_SERVER env var on clients"),
         wa("Use ROS_DOMAIN_ID to isolate node groups and reduce discovery traffic", 0.82,
            "export ROS_DOMAIN_ID=42  # nodes with different domain IDs don't discover each other")],
    ))

    canons.append(canon(
        "ros2", "message-type-hash-mismatch-rebuild", "humble-linux",
        "ROS2 'type hash mismatch' or 'incompatible type' error after modifying custom message definition",
        r"(type hash mismatch|incompatible.*type|message.*definition.*changed|TypeHash.*differ|IDL.*mismatch)",
        "build_system", "ros2", "humble", "linux", "true", 0.88, 0.90,
        "After modifying a .msg/.srv/.action file, the type hash changes. Running nodes using the old compiled message type cannot communicate with nodes using the new type. Clean rebuild of ALL dependent packages is required, not just the message package.",
        [de("Rebuild only the message package after changing .msg definition",
            "All packages that depend on the message must also be rebuilt. Their compiled bindings reference the old type hash. Partial rebuild = type hash mismatch at runtime.", 0.90),
         de("Restart nodes without rebuilding after .msg change",
            "Compiled message types are baked into the binaries. Restarting without rebuilding uses the same old binaries with old type hashes.", 0.88)],
        [wa("Clean rebuild all dependent packages after message changes", 0.95,
            "colcon build --packages-above my_msgs  # rebuilds my_msgs AND all packages that depend on it"),
         wa("Delete build/ and install/ directories for a guaranteed clean state", 0.88,
            "rm -rf build/ install/ log/ && colcon build  # nuclear option but guarantees no stale artifacts"),
         wa("Source install/setup.bash in ALL terminals after rebuild", 0.85,
            "source install/setup.bash  # every terminal running ROS2 nodes must re-source after message type changes")],
    ))

    canons.append(canon(
        "ros2", "nav2-costmap-not-clearing-obstacle", "humble-linux",
        "Nav2 costmap shows obstacles that have been removed, robot avoids phantom obstacles",
        r"(costmap.*not.*clearing|phantom.*obstacle|costmap.*stale|obstacle.*layer.*not.*clear|nav2.*costmap.*stuck)",
        "navigation", "ros2", "humble", "linux", "true", 0.82, 0.88,
        "Nav2 costmap obstacle layer has separate 'marking' (adding obstacles) and 'clearing' (removing obstacles) behaviors. If the sensor's clearing parameters are misconfigured, obstacles are added but never removed. Raytrace clearing requires correct sensor origin and max range.",
        [de("Assume costmap automatically clears obstacles when sensor no longer sees them",
            "Clearing happens via raytrace from sensor origin. If sensor origin frame is wrong, clearing rays miss the old obstacles. If obstacle_max_range < actual sensor range, far obstacles are never cleared.", 0.85),
         de("Increase costmap resolution to fix stale obstacles",
            "Higher resolution makes the problem worse - more cells to clear. The issue is clearing behavior configuration, not resolution.", 0.72)],
        [wa("Configure obstacle layer with correct clearing parameters", 0.92,
            "obstacle_layer: clearing: true, obstacle_max_range: 5.0, raytrace_max_range: 6.0  # raytrace must be >= obstacle max range"),
         wa("Set correct sensor_frame and ensure TF from sensor to robot is published", 0.90,
            "observation_sources: scan: {sensor_frame: laser_frame, clearing: true, marking: true, data_type: LaserScan}"),
         wa("Add a voxel layer instead of obstacle layer for 3D clearing", 0.82,
            "Voxel layer handles 3D raytrace clearing better than 2D obstacle layer for sensors with variable height")],
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
