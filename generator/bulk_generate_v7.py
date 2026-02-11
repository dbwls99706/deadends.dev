"""Bulk generate wave 7: +50 canons (target: ~310 total).

Usage: python -m generator.bulk_generate_v7
"""

import json
from generator.bulk_generate import (
    canon, de, wa, DATA_DIR,
)


def get_all_canons():
    c = []

    # ── PYTHON ──────────────────────────────────────────

    c.append(canon(
        "python", "typeerror-takes-positional-args", "py311-linux",
        "TypeError: function() takes 0 positional arguments but 1 was given",
        r"TypeError: \w+\(\) takes \d+ positional argument.* but \d+ (was|were) given",
        "type_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.95, 0.95,
        "Too many arguments passed. Common: missing self in class method, or calling staticmethod wrong.",
        [de("Add *args to accept anything",
            "Hides the real issue — wrong number of args means a bug", 0.75,
            sources=["https://docs.python.org/3/tutorial/controlflow.html#arbitrary-argument-lists"]),
         de("Remove extra arguments from the call",
            "May work but check if the function signature is wrong instead", 0.50,
            sources=["https://docs.python.org/3/tutorial/controlflow.html#more-on-defining-functions"])],
        [wa("If class method, add 'self' as first parameter", 0.95,
            "class Foo:\n    def method(self, x):  # not: def method(x):",
            sources=["https://docs.python.org/3/tutorial/classes.html#method-objects"]),
         wa("If decorator issue, check @staticmethod vs @classmethod vs regular method", 0.90,
            sources=["https://docs.python.org/3/library/functions.html#staticmethod"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "valueerror-math-domain", "py311-linux",
        "ValueError: math domain error",
        r"ValueError: math domain error",
        "math_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.92, 0.92,
        "Math operation with invalid input. sqrt(-1), log(0), asin(2), etc.",
        [de("Use try/except and return 0",
            "Returns wrong result — NaN or special handling is more appropriate", 0.65,
            sources=["https://docs.python.org/3/library/math.html"]),
         de("Use abs() on all inputs",
            "Changes the mathematical meaning — log(abs(x)) != log(x)", 0.70,
            sources=["https://docs.python.org/3/library/math.html"])],
        [wa("Validate input before calling: if x > 0: math.log(x)", 0.95,
            sources=["https://docs.python.org/3/library/math.html"]),
         wa("Use cmath for complex number support: cmath.sqrt(-1) → 1j", 0.88,
            "import cmath\nresult = cmath.sqrt(-1)  # returns 1j",
            sources=["https://docs.python.org/3/library/cmath.html"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "oserror-errno28-no-space", "py311-linux",
        "OSError: [Errno 28] No space left on device",
        r"OSError.*No space left on device|Errno 28",
        "filesystem_error", "python", ">=3.11,<3.13", "linux",
        "partial", 0.80, 0.85,
        "Disk is full. Common during data processing, logging, or tmp file operations.",
        [de("Increase disk size as first response",
            "May be a temp dir issue — check where the writes are going", 0.55,
            sources=["https://docs.python.org/3/library/os.html"]),
         de("Suppress the error and continue",
            "Data loss is certain if writes are silently failing", 0.90,
            sources=["https://docs.python.org/3/library/exceptions.html#OSError"])],
        [wa("Check disk usage: df -h and du -sh /tmp to find what's full", 0.95,
            sources=["https://docs.python.org/3/library/shutil.html#shutil.disk_usage"]),
         wa("Clean up temp files, old logs, or __pycache__ directories", 0.90,
            sources=["https://docs.python.org/3/library/tempfile.html"]),
         wa("Set TMPDIR to a volume with more space for temporary files", 0.82,
            sources=["https://docs.python.org/3/library/tempfile.html#tempfile.gettempdir"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "typeerror-expected-str-got-bytes", "py311-linux",
        "TypeError: a bytes-like object is required, not 'str'",
        r"TypeError: a bytes-like object is required, not 'str'",
        "type_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.95, 0.95,
        "Mixing str and bytes. Common when reading files in binary mode or working with network data.",
        [de("Open file without 'b' mode to avoid bytes",
            "May corrupt binary data or fail on non-text files", 0.65,
            sources=["https://docs.python.org/3/library/functions.html#open"]),
         de("Use str() to convert bytes",
            "str(b'data') gives \"b'data'\" not \"data\" — use .decode()", 0.80,
            sources=["https://docs.python.org/3/library/stdtypes.html#bytes.decode"])],
        [wa("Encode strings to bytes: text.encode('utf-8')", 0.95,
            sources=["https://docs.python.org/3/library/stdtypes.html#str.encode"]),
         wa("Or decode bytes to string: data.decode('utf-8')", 0.95,
            sources=["https://docs.python.org/3/library/stdtypes.html#bytes.decode"]),
         wa("Open files in text mode ('r') for text, binary mode ('rb') for binary data", 0.90,
            sources=["https://docs.python.org/3/library/functions.html#open"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "deprecationwarning-datetime-utcnow", "py311-linux",
        "DeprecationWarning: datetime.datetime.utcnow() is deprecated",
        r"DeprecationWarning.*utcnow.*deprecated|datetime\.utcnow",
        "deprecation_warning", "python", ">=3.11,<3.13", "linux",
        "true", 0.98, 0.95,
        "datetime.utcnow() deprecated in Python 3.12+. Returns naive datetime which causes timezone bugs.",
        [de("Suppress the deprecation warning",
            "The function will be removed — fix it now", 0.80,
            sources=["https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow"]),
         de("Use datetime.now() without timezone",
            "Returns local time, not UTC — different behavior", 0.70,
            sources=["https://docs.python.org/3/library/datetime.html#datetime.datetime.now"])],
        [wa("Use datetime.now(timezone.utc) instead of utcnow()", 0.98,
            "from datetime import datetime, timezone\nnow = datetime.now(timezone.utc)",
            sources=["https://docs.python.org/3/library/datetime.html#datetime.datetime.now"]),
         wa("Or use datetime.now(tz=timezone.utc) for explicit timezone-aware datetime", 0.95,
            sources=["https://docs.python.org/3/library/datetime.html#datetime.datetime.now"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "importerror-dll-load-failed", "py311-linux",
        "ImportError: DLL load failed while importing X",
        r"ImportError: DLL load failed|ImportError.*cannot open shared object|libstdc\+\+.*not found",
        "import_error", "python", ">=3.11,<3.13", "linux",
        "partial", 0.80, 0.85,
        "Shared library (.so/.dll) not found. Missing system dependency or wrong architecture.",
        [de("Reinstall Python",
            "Usually not a Python issue — it's a missing system library", 0.75,
            sources=["https://docs.python.org/3/library/importlib.html"]),
         de("Copy DLL from another machine",
            "DLLs are architecture-specific and may have dependencies", 0.80,
            sources=["https://docs.python.org/3/using/windows.html"])],
        [wa("Install the missing system library: apt install libXXX-dev", 0.90,
            "# Check what's missing:\nldd /path/to/module.so | grep 'not found'",
            sources=["https://docs.python.org/3/using/unix.html"]),
         wa("For conda environments, install with conda which bundles system libs", 0.85,
            "conda install numpy  # includes MKL/OpenBLAS",
            sources=["https://docs.conda.io/projects/conda/en/latest/"]),
         wa("On Windows, install Visual C++ Redistributable", 0.82,
            sources=["https://docs.python.org/3/using/windows.html"])],
        python=">=3.11,<3.13",
    ))

    # ── NODE ──────────────────────────────────────────

    c.append(canon(
        "node", "err-ossl-wrong-version-number", "node20-linux",
        "Error: write EPROTO: SSL routines: wrong version number",
        r"EPROTO.*SSL.*wrong version number|ERR_SSL_WRONG_VERSION_NUMBER",
        "tls_error", "node", ">=20,<23", "linux",
        "true", 0.90, 0.90,
        "HTTPS request sent to HTTP port, or proxy not handling TLS correctly.",
        [de("Disable TLS verification: rejectUnauthorized: false",
            "Security risk and doesn't fix the port/protocol issue", 0.85,
            sources=["https://nodejs.org/api/tls.html#tlscreatesecurecontextoptions"]),
         de("Downgrade to HTTP",
            "May expose sensitive data in transit", 0.70,
            sources=["https://nodejs.org/api/https.html"])],
        [wa("Check the URL protocol — using https:// on an HTTP-only port", 0.95,
            "// Wrong: https://localhost:3000  (if server is HTTP)\n// Right: http://localhost:3000",
            sources=["https://nodejs.org/api/https.html"]),
         wa("If using a proxy, configure it to handle TLS: HTTPS_PROXY env var", 0.85,
            sources=["https://nodejs.org/api/tls.html"])],
    ))

    c.append(canon(
        "node", "err-missing-script", "node20-linux",
        "npm error Missing script: \"start\"",
        r"Missing script.*start|npm ERR.*missing script",
        "config_error", "node", ">=20,<23", "linux",
        "true", 0.95, 0.95,
        "npm run <script> but that script doesn't exist in package.json.",
        [de("Create a generic start script that might not work",
            "The script should match your actual entry point", 0.70,
            sources=["https://docs.npmjs.com/cli/v10/commands/npm-run-script"]),
         de("Use npx instead of npm run",
            "npx is for running packages, not project scripts", 0.75,
            sources=["https://docs.npmjs.com/cli/v10/commands/npx"])],
        [wa("Add the script to package.json scripts section", 0.95,
            '{ "scripts": { "start": "node index.js" } }',
            sources=["https://docs.npmjs.com/cli/v10/using-npm/scripts"]),
         wa("Check available scripts: npm run (no arguments lists all scripts)", 0.92,
            sources=["https://docs.npmjs.com/cli/v10/commands/npm-run-script"]),
         wa("For frameworks, use the right command: next dev, vite, react-scripts start", 0.88,
            sources=["https://docs.npmjs.com/cli/v10/using-npm/scripts"])],
    ))

    c.append(canon(
        "node", "json-parse-unexpected-token", "node20-linux",
        "SyntaxError: Unexpected token < in JSON at position 0",
        r"Unexpected token .? in JSON at position|JSON\.parse.*SyntaxError|is not valid JSON",
        "parse_error", "node", ">=20,<23", "linux",
        "true", 0.92, 0.92,
        "JSON.parse received non-JSON data. Common: API returned HTML error page instead of JSON.",
        [de("Add try/catch and return empty object",
            "Hides the real issue — the response isn't JSON", 0.70,
            sources=["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/parse"]),
         de("Strip non-JSON characters from the string",
            "If you're getting HTML, stripping won't make it JSON", 0.80,
            sources=["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/parse"])],
        [wa("Log the actual response text to see what was returned (often an HTML error page)", 0.95,
            "const text = await res.text();\nconsole.log(text); // see what the server actually sent",
            sources=["https://developer.mozilla.org/en-US/docs/Web/API/Response/text"]),
         wa("Check response status before parsing: if (!res.ok) throw new Error(res.statusText)", 0.92,
            sources=["https://developer.mozilla.org/en-US/docs/Web/API/Response/ok"]),
         wa("Verify the API URL is correct and the server is returning JSON content-type", 0.88,
            sources=["https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Type"])],
    ))

    c.append(canon(
        "node", "punycode-deprecation", "node20-linux",
        "DeprecationWarning: The `punycode` module is deprecated",
        r"punycode.*deprecated|DEP0040",
        "deprecation_warning", "node", ">=20,<23", "linux",
        "true", 0.88, 0.88,
        "Built-in punycode module deprecated. Usually caused by a dependency, not your code.",
        [de("Suppress the warning with --no-deprecation",
            "Hides all deprecation warnings, including important ones", 0.70,
            sources=["https://nodejs.org/api/cli.html#--no-deprecation"]),
         de("Patch the dependency to remove punycode",
            "Fragile and will be overwritten on npm install", 0.80,
            sources=["https://nodejs.org/api/deprecations.html#DEP0040"])],
        [wa("Install the userland punycode package: npm install punycode", 0.88,
            sources=["https://www.npmjs.com/package/punycode"]),
         wa("Update the dependency that uses punycode — check npm ls punycode", 0.90,
            "npm ls punycode  # find which dependency uses it\nnpm update <dep>",
            sources=["https://nodejs.org/api/deprecations.html#DEP0040"]),
         wa("This is a warning, not an error — it still works, just update when possible", 0.85,
            sources=["https://nodejs.org/api/deprecations.html#DEP0040"])],
    ))

    # ── TYPESCRIPT ──────────────────────────────────────────

    c.append(canon(
        "typescript", "ts2589-excessive-stack-depth", "ts5-linux",
        "error TS2589: Type instantiation is excessively deep and possibly infinite",
        r"TS2589.*excessively deep.*possibly infinite",
        "type_error", "typescript", ">=5.0,<6.0", "linux",
        "partial", 0.78, 0.85,
        "Recursive type exceeded depth limit. Complex conditional/mapped types or circular type references.",
        [de("Increase TypeScript recursion limit",
            "No such config option — the limit is hardcoded for safety", 0.90,
            sources=["https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-5.html"]),
         de("Use @ts-ignore on the line",
            "Hides the type entirely — you lose all type checking", 0.65,
            sources=["https://www.typescriptlang.org/docs/handbook/2/basic-types.html"])],
        [wa("Simplify the recursive type — add a depth limit parameter", 0.88,
            "type DeepPartial<T, D extends number = 5> = ...",
            sources=["https://www.typescriptlang.org/docs/handbook/2/conditional-types.html"]),
         wa("Break circular type references by using interface instead of type alias", 0.82,
            sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#differences-between-type-aliases-and-interfaces"]),
         wa("Check if a simpler type utility exists in a library like type-fest", 0.78,
            sources=["https://www.npmjs.com/package/type-fest"])],
    ))

    c.append(canon(
        "typescript", "ts2352-conversion-may-be-mistake", "ts5-linux",
        "error TS2352: Conversion of type 'X' to type 'Y' may be a mistake",
        r"TS2352.*[Cc]onversion.*may be a mistake",
        "type_error", "typescript", ">=5.0,<6.0", "linux",
        "true", 0.92, 0.92,
        "Type assertion (as) between incompatible types. TypeScript warns the cast looks wrong.",
        [de("Double cast: x as unknown as Y",
            "Bypasses all type safety — any bug will be a runtime error", 0.75,
            sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions"]),
         de("Use any as intermediate",
            "Same as double cast — loses all type information", 0.80,
            sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#any"])],
        [wa("Use type narrowing instead of assertion: instanceof, typeof, in operator", 0.95,
            "if (obj instanceof MyClass) { obj.method(); }",
            sources=["https://www.typescriptlang.org/docs/handbook/2/narrowing.html"]),
         wa("Create a type guard function for complex narrowing", 0.88,
            "function isMyType(x: unknown): x is MyType { return 'key' in (x as object); }",
            sources=["https://www.typescriptlang.org/docs/handbook/2/narrowing.html#using-type-predicates"]),
         wa("Fix the actual type mismatch instead of casting", 0.90,
            sources=["https://www.typescriptlang.org/docs/handbook/2/types-from-types.html"])],
    ))

    # ── REACT ──────────────────────────────────────────

    c.append(canon(
        "react", "controlled-uncontrolled-switch", "react18-linux",
        "Warning: A component is changing an uncontrolled input to be controlled",
        r"changing an? (un)?controlled input to be (un)?controlled",
        "state_error", "react", ">=18,<20", "linux",
        "true", 0.92, 0.92,
        "Input value switches between undefined and defined. Must be always controlled or always uncontrolled.",
        [de("Add suppressWarning prop",
            "No such prop exists — fix the state management", 0.90,
            sources=["https://react.dev/reference/react-dom/components/input#controlling-an-input-with-a-state-variable"]),
         de("Use defaultValue and value together",
            "React doesn't support both — pick one pattern", 0.85,
            sources=["https://react.dev/reference/react-dom/components/input"])],
        [wa("Initialize state with empty string, not undefined: useState('')", 0.95,
            "// Bad: const [val, setVal] = useState()  // undefined initially\n// Good: const [val, setVal] = useState('')",
            sources=["https://react.dev/reference/react-dom/components/input#controlling-an-input-with-a-state-variable"]),
         wa("Use value={val ?? ''} to ensure value is never undefined", 0.90,
            sources=["https://react.dev/reference/react-dom/components/input"])],
    ))

    c.append(canon(
        "react", "useeffect-cleanup-memory-leak", "react18-linux",
        "Warning: Can't perform a React state update on an unmounted component",
        r"Can't perform a React state update on an unmounted component|memory leak",
        "lifecycle_error", "react", ">=18,<20", "linux",
        "true", 0.90, 0.90,
        "State update after component unmount. Missing cleanup in useEffect for async operations.",
        [de("Ignore the warning — it's just a warning",
            "Causes memory leaks and wasted computation", 0.65,
            sources=["https://react.dev/reference/react/useEffect#fetching-data-with-effects"]),
         de("Use a global isMounted flag",
            "Anti-pattern — use AbortController or cleanup function instead", 0.70,
            sources=["https://react.dev/reference/react/useEffect"])],
        [wa("Return a cleanup function from useEffect with AbortController", 0.95,
            "useEffect(() => {\n  const ctrl = new AbortController();\n  fetch(url, { signal: ctrl.signal }).then(...);\n  return () => ctrl.abort();\n}, [url]);",
            sources=["https://react.dev/reference/react/useEffect#fetching-data-with-effects"]),
         wa("For subscriptions, unsubscribe in cleanup: return () => unsubscribe()", 0.92,
            sources=["https://react.dev/reference/react/useEffect#connecting-to-an-external-system"])],
    ))

    # ── NEXT.JS ──────────────────────────────────────────

    c.append(canon(
        "nextjs", "metadata-client-component", "nextjs14-linux",
        "Error: You are attempting to export 'metadata' from a component marked with 'use client'",
        r"export.*metadata.*use client|metadata.*client component",
        "component_error", "nextjs", ">=14,<16", "linux",
        "true", 0.95, 0.95,
        "Metadata export only works in Server Components. Remove 'use client' or move metadata to layout.",
        [de("Use document.title in useEffect instead",
            "Client-side title changes aren't seen by crawlers — bad for SEO", 0.75,
            sources=["https://nextjs.org/docs/app/building-your-application/optimizing/metadata"]),
         de("Use next/head in App Router",
            "next/head is for Pages Router — use metadata export in App Router", 0.85,
            sources=["https://nextjs.org/docs/app/building-your-application/optimizing/metadata"])],
        [wa("Remove 'use client' from the page and move interactive parts to child Client Components", 0.95,
            sources=["https://nextjs.org/docs/app/building-your-application/optimizing/metadata"]),
         wa("Move metadata to the nearest Server Component layout.tsx", 0.90,
            "// app/layout.tsx (Server Component)\nexport const metadata = { title: 'My App' };",
            sources=["https://nextjs.org/docs/app/api-reference/functions/generate-metadata"])],
    ))

    c.append(canon(
        "nextjs", "fetch-cache-no-store", "nextjs14-linux",
        "Error: fetch failed with 'no-store' / Dynamic server usage: force-dynamic",
        r"no-store.*fetch|force-dynamic.*error|dynamic.*usage.*force",
        "data_error", "nextjs", ">=14,<16", "linux",
        "true", 0.88, 0.90,
        "fetch with cache: 'no-store' makes the route dynamic, conflicting with static generation.",
        [de("Remove cache: 'no-store' to make it static",
            "May serve stale data if the API data changes frequently", 0.55,
            sources=["https://nextjs.org/docs/app/building-your-application/data-fetching/caching-and-revalidating"]),
         de("Set force-static on the route segment",
            "Force-static will fail if the page truly needs dynamic data", 0.65,
            sources=["https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config"])],
        [wa("Use revalidate instead of no-store for ISR: fetch(url, { next: { revalidate: 60 } })", 0.95,
            sources=["https://nextjs.org/docs/app/building-your-application/data-fetching/caching-and-revalidating"]),
         wa("If truly dynamic, set export const dynamic = 'force-dynamic' in the page", 0.88,
            sources=["https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config#dynamic"]),
         wa("Understand the trade-off: static = fast/cached, dynamic = fresh/slower", 0.82,
            sources=["https://nextjs.org/docs/app/building-your-application/rendering/server-components"])],
    ))

    # ── DOCKER ──────────────────────────────────────────

    c.append(canon(
        "docker", "image-prune-in-use", "docker27-linux",
        "Error response from daemon: conflict: unable to remove image (image is being used)",
        r"unable to remove.*image.*being used|conflict.*image.*in use",
        "resource_error", "docker", ">=27,<28", "linux",
        "true", 0.95, 0.95,
        "Can't delete image because a container (running or stopped) is using it.",
        [de("Force remove with -f",
            "May break running containers that depend on this image", 0.65,
            sources=["https://docs.docker.com/reference/cli/docker/image/rm/"]),
         de("Delete all images with docker image prune -a",
            "Deletes ALL unused images — may remove images you still want", 0.70,
            sources=["https://docs.docker.com/reference/cli/docker/image/prune/"])],
        [wa("Remove containers using the image first: docker ps -a | grep <image>", 0.95,
            "docker rm $(docker ps -aq --filter ancestor=<image>)\ndocker rmi <image>",
            sources=["https://docs.docker.com/reference/cli/docker/container/rm/"]),
         wa("Use docker system prune to clean up all unused resources safely", 0.88,
            sources=["https://docs.docker.com/reference/cli/docker/system/prune/"])],
    ))

    c.append(canon(
        "docker", "env-file-not-found", "docker27-linux",
        "ERROR: Couldn't find env file: .env",
        r"Couldn't find env file|env_file.*not found|\.env.*no such file",
        "config_error", "docker", ">=27,<28", "linux",
        "true", 0.95, 0.95,
        "docker-compose references an env_file that doesn't exist.",
        [de("Remove env_file from docker-compose.yml",
            "May break the application that expects those env vars", 0.60,
            sources=["https://docs.docker.com/reference/compose-file/services/#env_file"]),
         de("Create an empty .env file",
            "App may fail with missing required env vars", 0.55,
            sources=["https://docs.docker.com/reference/compose-file/services/#env_file"])],
        [wa("Create the .env file from the example: cp .env.example .env", 0.95,
            sources=["https://docs.docker.com/reference/compose-file/services/#env_file"]),
         wa("Make env_file optional with required: false (Compose V2)", 0.88,
            "env_file:\n  - path: .env\n    required: false",
            sources=["https://docs.docker.com/reference/compose-file/services/#env_file"])],
    ))

    # ── GIT ──────────────────────────────────────────

    c.append(canon(
        "git", "commit-empty-aborting", "git2-linux",
        "Aborting commit due to empty commit message",
        r"Aborting commit due to empty commit message|nothing to commit",
        "commit_error", "git", ">=2.30,<3.0", "linux",
        "true", 0.95, 0.95,
        "Git commit without message or with empty message. Editor was closed without saving.",
        [de("Use --allow-empty-message",
            "Empty commit messages make history unreadable", 0.70,
            sources=["https://git-scm.com/docs/git-commit"]),
         de("Use git commit --amend to fix",
            "Amend changes the previous commit, not the current one", 0.60,
            sources=["https://git-scm.com/docs/git-commit#_options"])],
        [wa("Use -m flag: git commit -m 'your message'", 0.98,
            sources=["https://git-scm.com/docs/git-commit#Documentation/git-commit.txt--mltmsggt"]),
         wa("Set your preferred editor: git config --global core.editor 'code --wait'", 0.88,
            sources=["https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration"])],
    ))

    c.append(canon(
        "git", "diverged-branches", "git2-linux",
        "Your branch and 'origin/main' have diverged",
        r"have diverged|both modified|different commits",
        "branch_error", "git", ">=2.30,<3.0", "linux",
        "true", 0.88, 0.90,
        "Local and remote have different commits. Need to reconcile before pushing.",
        [de("Force push to override remote",
            "Destroys remote commits — other collaborators will lose work", 0.85,
            sources=["https://git-scm.com/docs/git-push#Documentation/git-push.txt---force"]),
         de("Delete local branch and re-checkout from remote",
            "Loses all local commits that haven't been pushed", 0.80,
            sources=["https://git-scm.com/docs/git-branch"])],
        [wa("Pull with rebase: git pull --rebase origin main", 0.92,
            sources=["https://git-scm.com/docs/git-pull#Documentation/git-pull.txt---rebase"]),
         wa("Or merge: git pull origin main (creates a merge commit)", 0.88,
            sources=["https://git-scm.com/docs/git-pull"]),
         wa("For feature branches, rebase onto main: git rebase main", 0.85,
            sources=["https://git-scm.com/docs/git-rebase"])],
    ))

    # ── KUBERNETES ──────────────────────────────────────────

    c.append(canon(
        "kubernetes", "clusterrole-forbidden", "k8s1-linux",
        "Error from server (Forbidden): clusterroles.rbac.authorization.k8s.io is forbidden",
        r"Forbidden.*rbac|clusterrole.*forbidden|cannot.*create.*clusterrole",
        "rbac_error", "kubernetes", ">=1.28,<2.0", "linux",
        "partial", 0.82, 0.85,
        "Insufficient RBAC permissions. User/service account can't create cluster-scoped resources.",
        [de("Give cluster-admin role to the service account",
            "Overly permissive — principle of least privilege", 0.75,
            sources=["https://kubernetes.io/docs/reference/access-authn-authz/rbac/"]),
         de("Disable RBAC",
            "Removes all authorization — anyone can do anything", 0.95,
            sources=["https://kubernetes.io/docs/reference/access-authn-authz/rbac/"])],
        [wa("Create a ClusterRole and ClusterRoleBinding with specific permissions", 0.92,
            "kubectl create clusterrolebinding my-binding --clusterrole=<role> --serviceaccount=<ns>:<sa>",
            sources=["https://kubernetes.io/docs/reference/access-authn-authz/rbac/#clusterrolebinding-example"]),
         wa("Use namespaced Role instead of ClusterRole if possible (more restricted scope)", 0.88,
            sources=["https://kubernetes.io/docs/reference/access-authn-authz/rbac/#role-and-clusterrole"]),
         wa("Check current permissions: kubectl auth can-i --list", 0.85,
            sources=["https://kubernetes.io/docs/reference/access-authn-authz/authorization/#checking-api-access"])],
    ))

    c.append(canon(
        "kubernetes", "persistent-volume-pending", "k8s1-linux",
        "PersistentVolumeClaim is stuck in Pending state",
        r"PersistentVolumeClaim.*Pending|no persistent volumes available|waiting for a volume to be created",
        "storage_error", "kubernetes", ">=1.28,<2.0", "linux",
        "partial", 0.80, 0.85,
        "PVC can't find a matching PV. No StorageClass provisioner or no available storage.",
        [de("Manually create a PV with exact specs",
            "Manual PVs don't scale and are hard to manage", 0.55,
            sources=["https://kubernetes.io/docs/concepts/storage/persistent-volumes/"]),
         de("Delete and recreate the PVC",
            "Won't help if the underlying issue is no StorageClass or no space", 0.70,
            sources=["https://kubernetes.io/docs/concepts/storage/persistent-volumes/"])],
        [wa("Check if a default StorageClass exists: kubectl get storageclass", 0.92,
            sources=["https://kubernetes.io/docs/concepts/storage/storage-classes/"]),
         wa("Create a StorageClass or set one as default if missing", 0.88,
            "kubectl patch storageclass <name> -p '{\"metadata\": {\"annotations\":{\"storageclass.kubernetes.io/is-default-class\":\"true\"}}}'",
            sources=["https://kubernetes.io/docs/tasks/administer-cluster/change-default-storage-class/"]),
         wa("For local dev, use local-path provisioner or hostPath", 0.80,
            sources=["https://kubernetes.io/docs/concepts/storage/volumes/#hostpath"])],
    ))

    # ── CUDA ──────────────────────────────────────────

    c.append(canon(
        "cuda", "cudnn-version-mismatch", "cuda12-a100",
        "RuntimeError: cuDNN version incompatibility",
        r"cuDNN.*incompatib|cuDNN.*version.*mismatch|CUDNN_STATUS_VERSION_MISMATCH",
        "compatibility_error", "cuda", ">=12.0,<13.0", "linux",
        "true", 0.88, 0.90,
        "cuDNN version doesn't match the CUDA toolkit or PyTorch build.",
        [de("Install the latest cuDNN regardless of CUDA version",
            "cuDNN versions are tied to CUDA versions — must match", 0.80,
            sources=["https://docs.nvidia.com/deeplearning/cudnn/latest/reference/support-matrix.html"]),
         de("Build cuDNN from source",
            "cuDNN is proprietary — can't build from source", 0.95,
            sources=["https://developer.nvidia.com/cudnn"])],
        [wa("Install the cuDNN version that matches your CUDA toolkit: check the compatibility matrix", 0.92,
            sources=["https://docs.nvidia.com/deeplearning/cudnn/latest/reference/support-matrix.html"]),
         wa("Use conda install which handles CUDA/cuDNN version matching automatically", 0.90,
            "conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia",
            sources=["https://pytorch.org/get-started/locally/"]),
         wa("Or install PyTorch with bundled cuDNN via pip: pip install torch --index-url ...", 0.85,
            sources=["https://pytorch.org/get-started/locally/"])],
        gpu="A100", vram=40,
    ))

    # ── RUST ──────────────────────────────────────────

    c.append(canon(
        "rust", "e0597-borrowed-too-short", "rust1-linux",
        "error[E0597]: borrowed value does not live long enough",
        r"E0597.*does not live long enough|borrowed value.*dropped.*still borrowed",
        "lifetime_error", "rust", ">=1.70,<2.0", "linux",
        "true", 0.85, 0.90,
        "Reference outlives the value it borrows. Value is dropped while still being referenced.",
        [de("Use 'static lifetime to extend",
            "'static means lives forever — wrong for most temporary values", 0.80,
            sources=["https://doc.rust-lang.org/error_codes/E0597.html"]),
         de("Leak memory with Box::leak",
            "Creates a genuine memory leak — never do this for normal code", 0.90,
            sources=["https://doc.rust-lang.org/std/boxed/struct.Box.html#method.leak"])],
        [wa("Restructure code so the owner lives longer than the reference", 0.92,
            "// Move let binding before the reference user\nlet data = String::from(\"hello\");\nlet reference = &data;  // data lives longer",
            sources=["https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html"]),
         wa("Clone the data to give the consumer its own copy", 0.85,
            sources=["https://doc.rust-lang.org/std/clone/trait.Clone.html"]),
         wa("Use Rc/Arc for shared ownership when multiple parts need the data", 0.82,
            sources=["https://doc.rust-lang.org/std/rc/struct.Rc.html"])],
    ))

    # ── GO ──────────────────────────────────────────

    c.append(canon(
        "go", "cannot-assign-to-struct-field", "go1-linux",
        "cannot assign to struct field in map",
        r"cannot assign to struct field.*map|cannot take the address of",
        "compile_error", "go", ">=1.21,<2.0", "linux",
        "true", 0.92, 0.92,
        "Can't modify a struct field directly in a map. Go maps return copies, not references.",
        [de("Use unsafe to get a pointer to the map value",
            "Unsafe and undefined behavior — map values can move in memory", 0.95,
            sources=["https://go.dev/ref/spec#Assignments"]),
         de("Use a different data structure",
            "Maps are fine — just use pointer values", 0.55,
            sources=["https://go.dev/blog/maps"])],
        [wa("Use a map of pointers: map[string]*MyStruct", 0.95,
            "m := map[string]*MyStruct{\"key\": &MyStruct{Field: 1}}\nm[\"key\"].Field = 2  // works!",
            sources=["https://go.dev/blog/maps"]),
         wa("Copy, modify, reassign: tmp := m[k]; tmp.Field = val; m[k] = tmp", 0.90,
            sources=["https://go.dev/ref/spec#Assignments"])],
    ))

    c.append(canon(
        "go", "too-many-open-files", "go1-linux",
        "dial tcp: socket: too many open files",
        r"too many open files|EMFILE|socket.*too many",
        "system_error", "go", ">=1.21,<2.0", "linux",
        "partial", 0.82, 0.85,
        "File descriptor limit reached. Common in HTTP clients without closing response bodies.",
        [de("Increase ulimit to a very large value",
            "Just delays the problem — file descriptors are still leaking", 0.60,
            sources=["https://pkg.go.dev/net/http"]),
         de("Restart the process when limit is hit",
            "Hack that doesn't fix the leak", 0.80,
            sources=["https://pkg.go.dev/net/http"])],
        [wa("Close HTTP response bodies: defer resp.Body.Close()", 0.95,
            "resp, err := http.Get(url)\nif err != nil { return err }\ndefer resp.Body.Close()",
            sources=["https://pkg.go.dev/net/http#Client.Do"]),
         wa("Close file handles, database connections, and other resources with defer", 0.90,
            sources=["https://go.dev/blog/defer-panic-and-recover"]),
         wa("Increase ulimit as a temporary measure: ulimit -n 65536", 0.75,
            sources=["https://pkg.go.dev/os#File"])],
    ))

    # ── PIP ──────────────────────────────────────────

    c.append(canon(
        "pip", "install-requires-different-python", "pip24-linux",
        "ERROR: Package requires a different Python: X.Y.Z not in '>=3.X'",
        r"requires a different Python|python_requires|Requires-Python",
        "version_error", "pip", ">=24,<25", "linux",
        "true", 0.90, 0.90,
        "Package doesn't support your Python version. Check python_requires in package metadata.",
        [de("Use --ignore-requires-python",
            "Package may genuinely not work on your Python version — crashes at runtime", 0.65,
            sources=["https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-ignore-requires-python"]),
         de("Edit the package metadata to remove the restriction",
            "Package will reinstall with original metadata on update", 0.80,
            sources=["https://pip.pypa.io/en/stable/reference/build-system/pyproject-toml/"])],
        [wa("Install an older version that supports your Python: pip install 'pkg<2.0'", 0.92,
            sources=["https://pip.pypa.io/en/stable/cli/pip_install/#requirement-specifiers"]),
         wa("Upgrade Python to meet the requirement", 0.88,
            sources=["https://www.python.org/downloads/"]),
         wa("Use pyenv to manage multiple Python versions", 0.85,
            "pyenv install 3.12.0 && pyenv local 3.12.0",
            sources=["https://github.com/pyenv/pyenv"])],
    ))

    # ── AWS ──────────────────────────────────────────

    c.append(canon(
        "aws", "iam-policy-too-large", "awscli2-linux",
        "An error occurred (LimitExceededException) when calling the PutRolePolicy: Cannot exceed quota for PolicySize",
        r"PolicySize.*exceeded|policy.*too large|Cannot exceed quota for Policy",
        "quota_error", "aws", ">=2.0,<3.0", "linux",
        "true", 0.85, 0.88,
        "IAM policy document exceeds 6,144 character limit (inline) or 10,240 (managed).",
        [de("Minify the JSON to reduce character count",
            "Minor savings — the real issue is too many permissions", 0.60,
            sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_iam-quotas.html"]),
         de("Create multiple IAM users with split permissions",
            "Complicates management and audit — use policy splitting instead", 0.65,
            sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html"])],
        [wa("Split into multiple managed policies (up to 10 per role/user)", 0.92,
            sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_iam-quotas.html"]),
         wa("Use wildcards to reduce statement count: s3:Get* instead of listing each action", 0.88,
            sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_action.html"]),
         wa("Consolidate resources and conditions to reduce policy size", 0.82,
            sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html"])],
    ))

    c.append(canon(
        "aws", "cloudformation-rollback-complete", "awscli2-linux",
        "Stack is in ROLLBACK_COMPLETE state and can not be updated",
        r"ROLLBACK_COMPLETE.*can not be updated|ROLLBACK_COMPLETE",
        "deployment_error", "aws", ">=2.0,<3.0", "linux",
        "true", 0.90, 0.90,
        "CloudFormation stack failed creation and rolled back. Can't update — must delete and recreate.",
        [de("Try to update the stack anyway",
            "AWS API rejects updates to ROLLBACK_COMPLETE stacks", 0.95,
            sources=["https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/troubleshooting.html"]),
         de("Manually create the resources outside CloudFormation",
            "Resources drift from IaC — hard to manage", 0.70,
            sources=["https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/troubleshooting.html"])],
        [wa("Delete the failed stack and recreate: aws cloudformation delete-stack --stack-name X", 0.95,
            sources=["https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/troubleshooting.html"]),
         wa("Check the Events tab to find why creation failed, then fix the template", 0.92,
            "aws cloudformation describe-stack-events --stack-name X | jq '.StackEvents[] | select(.ResourceStatus == \"CREATE_FAILED\")'",
            sources=["https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/troubleshooting.html"]),
         wa("Use --on-failure DO_NOTHING to debug without rollback next time", 0.82,
            sources=["https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-create-stack.html"])],
    ))

    # ── TERRAFORM ──────────────────────────────────────────

    c.append(canon(
        "terraform", "apply-timeout", "tf1-linux",
        "Error: timeout while waiting for state to become 'AVAILABLE'",
        r"timeout.*waiting for state|timeout.*waiting for.*to become",
        "timeout_error", "terraform", ">=1.5,<2.0", "linux",
        "partial", 0.78, 0.85,
        "AWS/cloud resource creation timed out. Resource may still be creating in the background.",
        [de("Run terraform apply again immediately",
            "May try to create a second resource if the first is still in progress", 0.70,
            sources=["https://developer.hashicorp.com/terraform/language/resources/provisioners/connection#timeouts"]),
         de("Increase timeout to a very large value",
            "May work but hides the real issue — why is it so slow?", 0.50,
            sources=["https://developer.hashicorp.com/terraform/language/resources/syntax#operation-timeouts"])],
        [wa("Check the resource in AWS Console — it may still be creating", 0.90,
            sources=["https://developer.hashicorp.com/terraform/language/resources/syntax#operation-timeouts"]),
         wa("Run terraform refresh to sync state, then terraform apply", 0.88,
            sources=["https://developer.hashicorp.com/terraform/cli/commands/refresh"]),
         wa("Set custom timeouts in the resource block for known slow resources", 0.82,
            "resource \"aws_rds_instance\" \"db\" {\n  ...\n  timeouts { create = \"60m\" }\n}",
            sources=["https://developer.hashicorp.com/terraform/language/resources/syntax#operation-timeouts"])],
    ))

    return c


def main():
    canons = get_all_canons()
    written = 0
    skipped = 0
    for c in canons:
        domain = c["error"]["domain"]
        slug = c["id"].split("/")[1]
        env = c["id"].split("/")[2]
        out_dir = DATA_DIR / domain
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{slug}_{env}.json"
        if out_file.exists():
            skipped += 1
            continue
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(c, f, indent=2, ensure_ascii=False)
            f.write("\n")
        written += 1
    print(f"Wave 7: wrote {written} new canons, skipped {skipped} existing")


if __name__ == "__main__":
    main()
