"""Bulk generate wave 6: +50 canons (target: ~275 total).

Usage: python -m generator.bulk_generate_v6
"""

import json
from generator.bulk_generate import (
    canon, de, wa, DATA_DIR,
)


def get_all_canons():
    c = []

    # ── PYTHON ──────────────────────────────────────────

    c.append(canon(
        "python", "typeerror-unsupported-operand", "py311-linux",
        "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
        r"TypeError: unsupported operand type\(s\) for .+: '(\w+)' and '(\w+)'",
        "type_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.95, 0.95,
        "Binary operation between incompatible types. Common: concatenating str + int without conversion.",
        [de("Convert everything to str",
            "May hide a logic error — you might want numeric addition, not concatenation", 0.60,
            sources=["https://docs.python.org/3/library/functions.html#str"]),
         de("Use eval() to auto-detect types",
            "eval is a security risk and doesn't fix type issues", 0.90,
            sources=["https://docs.python.org/3/library/functions.html#eval"])],
        [wa("Explicitly convert types: str(num) for concat, int(s) for math", 0.95,
            "result = 'Count: ' + str(count)  # or f'Count: {count}'",
            sources=["https://docs.python.org/3/library/stdtypes.html#str"]),
         wa("Use f-strings for mixed type formatting: f'{name}: {value}'", 0.95,
            sources=["https://docs.python.org/3/reference/lexical_analysis.html#f-strings"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "runtimeerror-generator-already-executing", "py311-linux",
        "RuntimeError: generator already executing",
        r"RuntimeError: generator already executing",
        "runtime_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.85, 0.88,
        "Generator's next() called while it's still running. Common in async code or recursive generators.",
        [de("Use threading lock on the generator",
            "Generators are not thread-safe by design — restructure instead", 0.75,
            sources=["https://docs.python.org/3/reference/expressions.html#generator-expressions"]),
         de("Convert to list to avoid generator issues",
            "Loses lazy evaluation and may cause memory issues", 0.55,
            sources=["https://docs.python.org/3/glossary.html#term-generator"])],
        [wa("Don't call next() on a generator from within that generator's code path", 0.92,
            sources=["https://docs.python.org/3/reference/expressions.html#generator-expressions"]),
         wa("Use separate generator instances for recursive patterns", 0.88,
            sources=["https://docs.python.org/3/reference/expressions.html#yield-expressions"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "lookuperror-unknown-encoding", "py311-linux",
        "LookupError: unknown encoding: utf8",
        r"LookupError: unknown encoding",
        "encoding_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.95, 0.95,
        "Misspelled encoding name. utf8 → utf-8, ascii → ascii, latin1 → latin-1.",
        [de("Install a codec package",
            "Standard encodings are built into Python — no package needed", 0.80,
            sources=["https://docs.python.org/3/library/codecs.html#standard-encodings"]),
         de("Set PYTHONIOENCODING environment variable",
            "Doesn't fix the encoding name in your code", 0.70,
            sources=["https://docs.python.org/3/using/cmdline.html#envvar-PYTHONIOENCODING"])],
        [wa("Use the correct encoding name: 'utf-8' (with hyphen), not 'utf8'", 0.98,
            "open('file.txt', encoding='utf-8')  # not 'utf8' or 'UTF_8'",
            sources=["https://docs.python.org/3/library/codecs.html#standard-encodings"]),
         wa("Check Python's list of standard encodings for the correct name", 0.90,
            sources=["https://docs.python.org/3/library/codecs.html#standard-encodings"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "django-improperlyconfigured", "py311-linux",
        "django.core.exceptions.ImproperlyConfigured: Requested setting DEFAULT_INDEX_TABLESPACE, but settings are not configured",
        r"ImproperlyConfigured.*settings are not configured|DJANGO_SETTINGS_MODULE",
        "config_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.95, 0.95,
        "DJANGO_SETTINGS_MODULE not set. Django can't find settings.py.",
        [de("Hardcode settings in the script",
            "Duplicates configuration and diverges from the main settings", 0.70,
            sources=["https://docs.djangoproject.com/en/5.0/topics/settings/"]),
         de("Import settings directly from the file",
            "Bypasses Django's settings machinery — may miss configured apps", 0.65,
            sources=["https://docs.djangoproject.com/en/5.0/topics/settings/"])],
        [wa("Set environment variable: export DJANGO_SETTINGS_MODULE=myproject.settings", 0.95,
            "import os\nos.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')",
            sources=["https://docs.djangoproject.com/en/5.0/topics/settings/#designating-the-settings"]),
         wa("Or call django.setup() after setting the env var in scripts", 0.92,
            "import django\nos.environ['DJANGO_SETTINGS_MODULE'] = 'myproject.settings'\ndjango.setup()",
            sources=["https://docs.djangoproject.com/en/5.0/topics/settings/"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "flask-working-outside-context", "py311-linux",
        "RuntimeError: Working outside of application context",
        r"Working outside of (application|request) context",
        "context_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.92, 0.92,
        "Flask operation requires app context. Accessing current_app, g, or db outside of a request/CLI.",
        [de("Import the app instance directly",
            "Creates circular imports and bypasses Flask's context-local design", 0.65,
            sources=["https://flask.palletsprojects.com/en/3.0.x/appcontext/"]),
         de("Set global variables instead of using g/current_app",
            "Breaks in multi-threaded/multi-worker deployments", 0.80,
            sources=["https://flask.palletsprojects.com/en/3.0.x/appcontext/"])],
        [wa("Use with app.app_context(): to push an application context", 0.95,
            "with app.app_context():\n    db.create_all()",
            sources=["https://flask.palletsprojects.com/en/3.0.x/appcontext/"]),
         wa("In tests, use app.test_client() or app.test_request_context()", 0.90,
            sources=["https://flask.palletsprojects.com/en/3.0.x/testing/"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "asyncio-no-running-event-loop", "py311-linux",
        "RuntimeError: no running event loop",
        r"RuntimeError: no running event loop|There is no current event loop",
        "async_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.90, 0.90,
        "Calling async code without an event loop. asyncio.get_event_loop() fails in threads.",
        [de("Use asyncio.get_event_loop() to create one",
            "Deprecated in 3.12+ — raises error in non-main threads", 0.75,
            sources=["https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.get_event_loop"]),
         de("Run asyncio.run() inside an already running loop",
            "asyncio.run() can't be called from within an existing event loop", 0.85,
            sources=["https://docs.python.org/3/library/asyncio-runner.html#asyncio.run"])],
        [wa("Use asyncio.run() in the main entry point — it creates and manages the loop", 0.95,
            "asyncio.run(main())",
            sources=["https://docs.python.org/3/library/asyncio-runner.html#asyncio.run"]),
         wa("In Jupyter/IPython, use await directly (loop already running) or nest_asyncio", 0.88,
            "import nest_asyncio; nest_asyncio.apply()",
            sources=["https://docs.python.org/3/library/asyncio-runner.html"]),
         wa("For threads, use asyncio.run_coroutine_threadsafe(coro, loop)", 0.85,
            sources=["https://docs.python.org/3/library/asyncio-task.html#asyncio.run_coroutine_threadsafe"])],
        python=">=3.11,<3.13",
    ))

    # ── NODE ──────────────────────────────────────────

    c.append(canon(
        "node", "err-dlopen-failed", "node20-linux",
        "Error: dlopen failed: cannot load native module",
        r"dlopen failed|Cannot load native module|was compiled against a different Node",
        "native_error", "node", ">=20,<23", "linux",
        "true", 0.88, 0.90,
        "Native addon compiled for different Node/architecture. Need to rebuild.",
        [de("Copy node_modules from another machine",
            "Native addons are platform-specific — compiled binaries aren't portable", 0.85,
            sources=["https://nodejs.org/api/addons.html"]),
         de("Downgrade Node to match the addon",
            "Better to rebuild the addon for your current Node version", 0.60,
            sources=["https://nodejs.org/api/addons.html"])],
        [wa("Rebuild native modules: npm rebuild or rm -rf node_modules && npm install", 0.95,
            "npm rebuild\n# or: npx node-gyp rebuild",
            sources=["https://nodejs.org/api/addons.html"]),
         wa("For Electron apps, use electron-rebuild: npx electron-rebuild", 0.88,
            sources=["https://www.electronjs.org/docs/latest/tutorial/using-native-node-modules"])],
    ))

    c.append(canon(
        "node", "err-package-json-invalid", "node20-linux",
        "Error [ERR_PACKAGE_PATH_NOT_EXPORTED]: Package subpath './X' is not defined by exports",
        r"ERR_PACKAGE_PATH_NOT_EXPORTED|Package subpath.*not defined by.*exports",
        "module_error", "node", ">=20,<23", "linux",
        "true", 0.88, 0.90,
        "Package exports field doesn't expose this subpath. Library changed its exports in a new version.",
        [de("Patch package.json exports field in node_modules",
            "Changes will be lost on next npm install", 0.85,
            sources=["https://nodejs.org/api/packages.html#exports"]),
         de("Use require() to bypass exports restriction",
            "Only works for CJS packages and may break in future", 0.60,
            sources=["https://nodejs.org/api/packages.html#exports"])],
        [wa("Check library changelog for the new import path after the update", 0.92,
            sources=["https://nodejs.org/api/packages.html#exports"]),
         wa("Pin to the previous version that exposed this subpath", 0.85,
            sources=["https://docs.npmjs.com/cli/v10/commands/npm-install"]),
         wa("Use the library's public API instead of deep imports", 0.90,
            "// Old: import X from 'lib/internal/x'\n// New: import { X } from 'lib'",
            sources=["https://nodejs.org/api/packages.html#exports"])],
    ))

    c.append(canon(
        "node", "digital-envelope-unsupported", "node20-linux",
        "Error: error:0308010C:digital envelope routines::unsupported",
        r"digital envelope routines.*unsupported|ERR_OSSL_EVP_UNSUPPORTED",
        "openssl_error", "node", ">=18,<23", "linux",
        "true", 0.90, 0.90,
        "OpenSSL 3.0 dropped support for legacy algorithms. Common with old webpack/CRA versions.",
        [de("Set NODE_OPTIONS=--openssl-legacy-provider permanently",
            "Workaround, not a fix — legacy algorithms are deprecated for security reasons", 0.55,
            sources=["https://nodejs.org/api/cli.html#--openssl-configfile"]),
         de("Downgrade to Node 16",
            "Node 16 is end-of-life — no security updates", 0.80,
            sources=["https://nodejs.org/en/about/previous-releases"])],
        [wa("Update webpack/CRA/build tool to a version that supports OpenSSL 3.0", 0.95,
            "npm update react-scripts  # or: npm update webpack",
            sources=["https://nodejs.org/api/crypto.html"]),
         wa("Temporary fix: NODE_OPTIONS=--openssl-legacy-provider npm start", 0.80,
            sources=["https://nodejs.org/api/cli.html#node_optionsoptions"])],
    ))

    c.append(canon(
        "node", "experimental-vm-modules", "node20-linux",
        "TypeError: A dynamic import callback was not specified (Jest ESM)",
        r"dynamic import callback.*not specified|--experimental-vm-modules|ERR_VM_DYNAMIC_IMPORT_CALLBACK_MISSING",
        "test_error", "node", ">=20,<23", "linux",
        "true", 0.88, 0.90,
        "Jest can't handle ES modules without --experimental-vm-modules flag.",
        [de("Rewrite all tests to CommonJS",
            "If your project is ESM, tests should be ESM too", 0.70,
            sources=["https://jestjs.io/docs/ecmascript-modules"]),
         de("Use dynamic import() inside require-based tests",
            "Awkward pattern that makes tests harder to read", 0.60,
            sources=["https://jestjs.io/docs/ecmascript-modules"])],
        [wa("Run Jest with experimental VM modules: NODE_OPTIONS=--experimental-vm-modules npx jest", 0.92,
            sources=["https://jestjs.io/docs/ecmascript-modules"]),
         wa("Consider switching to Vitest which has native ESM support", 0.90,
            "npm install -D vitest\n# vitest supports ESM natively",
            sources=["https://vitest.dev/guide/"]),
         wa("Add transform config to jest.config.js for ESM files", 0.82,
            sources=["https://jestjs.io/docs/configuration#transform-objectstring-pathtotransformer--pathtotransformer-object"])],
    ))

    # ── TYPESCRIPT ──────────────────────────────────────────

    c.append(canon(
        "typescript", "ts2769-no-overload-matches", "ts5-linux",
        "error TS2769: No overload matches this call",
        r"TS2769.*No overload matches this call",
        "type_error", "typescript", ">=5.0,<6.0", "linux",
        "true", 0.88, 0.90,
        "None of the function's overload signatures match the provided arguments. Check each overload's requirements.",
        [de("Cast arguments to any",
            "Bypasses type checking entirely — the overloads exist for correctness", 0.80,
            sources=["https://www.typescriptlang.org/docs/handbook/2/functions.html#function-overloads"]),
         de("Remove the overload signatures",
            "If it's a library function, you can't modify it", 0.85,
            sources=["https://www.typescriptlang.org/docs/handbook/2/functions.html#function-overloads"])],
        [wa("Read each overload signature in the error — match your args to one of them", 0.92,
            sources=["https://www.typescriptlang.org/docs/handbook/2/functions.html#function-overloads"]),
         wa("Check for subtle type differences: string vs String, number vs bigint", 0.88,
            sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html"]),
         wa("Common with event handlers: use the specific event type, not generic Event", 0.85,
            "onClick: (e: React.MouseEvent<HTMLButtonElement>) => void",
            sources=["https://www.typescriptlang.org/docs/handbook/2/functions.html"])],
    ))

    c.append(canon(
        "typescript", "ts2305-module-no-exported-member", "ts5-linux",
        "error TS2305: Module 'X' has no exported member 'Y'",
        r"TS2305.*Module.*has no exported member",
        "import_error", "typescript", ">=5.0,<6.0", "linux",
        "true", 0.92, 0.92,
        "Named import doesn't exist in the module. Different from TS2694 (namespace).",
        [de("Use @ts-ignore to suppress",
            "Hides the error but runtime import will fail or be undefined", 0.80,
            sources=["https://www.typescriptlang.org/docs/handbook/modules/reference.html"]),
         de("Use require() to bypass type checking",
            "Loses all type safety for this import", 0.75,
            sources=["https://www.typescriptlang.org/docs/handbook/modules/reference.html"])],
        [wa("Check if the export was renamed or moved in a package update", 0.92,
            sources=["https://www.typescriptlang.org/docs/handbook/modules/reference.html"]),
         wa("Use default import if the module uses export default: import X from 'mod' not { X }", 0.88,
            sources=["https://www.typescriptlang.org/docs/handbook/modules/reference.html"]),
         wa("Check @types package version matches the library version", 0.85,
            "npm ls @types/react react  # versions should be compatible",
            sources=["https://www.typescriptlang.org/docs/handbook/2/type-declarations.html"])],
    ))

    # ── REACT ──────────────────────────────────────────

    c.append(canon(
        "react", "cannot-read-undefined-map", "react18-linux",
        "TypeError: Cannot read properties of undefined (reading 'map')",
        r"Cannot read properties of (undefined|null).*reading 'map'",
        "data_error", "react", ">=18,<20", "linux",
        "true", 0.95, 0.95,
        "Calling .map() on undefined data. Common with async data not loaded yet or wrong API response shape.",
        [de("Add || [] everywhere data is mapped",
            "Masks underlying data issues — undefined data might indicate a real bug", 0.55,
            sources=["https://react.dev/learn/rendering-lists"]),
         de("Use try/catch around the render",
            "Components shouldn't need try/catch for normal rendering", 0.70,
            sources=["https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary"])],
        [wa("Initialize state with empty array: const [items, setItems] = useState([])", 0.95,
            sources=["https://react.dev/reference/react/useState"]),
         wa("Add loading state check: if (!data) return <Loading />", 0.92,
            sources=["https://react.dev/learn/synchronizing-with-effects"]),
         wa("Use optional chaining: data?.items?.map(...)", 0.88,
            sources=["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining"])],
    ))

    c.append(canon(
        "react", "hooks-in-class-component", "react18-linux",
        "Error: Invalid hook call. Hooks can only be called inside of the body of a function component. (class component)",
        r"Invalid hook call.*function component|Hooks can only be called inside",
        "hook_error", "react", ">=18,<20", "linux",
        "true", 0.90, 0.92,
        "Using hooks (useState, useEffect) in a class component. Hooks are function-component only.",
        [de("Wrap class component in a function component",
            "Over-engineering — convert the class component instead", 0.65,
            sources=["https://react.dev/reference/rules/rules-of-hooks"]),
         de("Use a higher-order component to inject hooks",
            "Works but adds complexity — better to convert to function component", 0.50,
            sources=["https://react.dev/reference/rules/rules-of-hooks"])],
        [wa("Convert class component to function component to use hooks", 0.95,
            "// Class: this.state, this.setState\n// Function: const [state, setState] = useState()",
            sources=["https://react.dev/reference/react/Component#alternatives"]),
         wa("If keeping class, use lifecycle methods instead: componentDidMount, componentDidUpdate", 0.85,
            sources=["https://react.dev/reference/react/Component#componentdidmount"])],
    ))

    c.append(canon(
        "react", "act-warning", "react18-linux",
        "Warning: An update to X inside a test was not wrapped in act(...)",
        r"An update to .+ inside a test was not wrapped in act",
        "test_error", "react", ">=18,<20", "linux",
        "true", 0.88, 0.90,
        "React state update in test not wrapped in act(). Test may not reflect final UI state.",
        [de("Suppress console.error in tests",
            "Silences the warning but test assertions may be wrong", 0.80,
            sources=["https://react.dev/reference/react/act"]),
         de("Add act() around every single assertion",
            "Over-wrapping — only wrap state-changing operations", 0.55,
            sources=["https://react.dev/reference/react/act"])],
        [wa("Wrap state-triggering actions in act(): await act(async () => { fireEvent.click(btn) })", 0.92,
            sources=["https://react.dev/reference/react/act"]),
         wa("Use React Testing Library's built-in methods (click, type) which auto-wrap in act", 0.95,
            "import { render, screen, fireEvent } from '@testing-library/react';",
            sources=["https://testing-library.com/docs/react-testing-library/intro/"]),
         wa("For async updates, use waitFor: await waitFor(() => expect(element).toBeVisible())", 0.90,
            sources=["https://testing-library.com/docs/dom-testing-library/api-async#waitfor"])],
    ))

    # ── NEXT.JS ──────────────────────────────────────────

    c.append(canon(
        "nextjs", "use-client-directive", "nextjs14-linux",
        "Error: useState/useEffect can only be used in Client Components. Add 'use client' directive",
        r"useState.*Client Component|useEffect.*Client Component|use client.*directive",
        "component_error", "nextjs", ">=14,<16", "linux",
        "true", 0.98, 0.95,
        "Using React hooks in a Server Component. App Router defaults all components to Server Components.",
        [de("Mark every component as 'use client'",
            "Defeats the purpose of Server Components — only mark interactive ones", 0.70,
            sources=["https://nextjs.org/docs/app/building-your-application/rendering/client-components"]),
         de("Move state management to a global store",
            "Over-engineering for simple interactive components", 0.65,
            sources=["https://nextjs.org/docs/app/building-your-application/rendering/composition-patterns"])],
        [wa("Add 'use client' directive at the top of the file that uses hooks", 0.98,
            "'use client';\nimport { useState } from 'react';",
            sources=["https://nextjs.org/docs/app/building-your-application/rendering/client-components"]),
         wa("Split into Server (data fetching) + Client (interactive) components", 0.92,
            sources=["https://nextjs.org/docs/app/building-your-application/rendering/composition-patterns"])],
    ))

    c.append(canon(
        "nextjs", "server-actions-error", "nextjs14-linux",
        "Error: Functions cannot be passed directly to Client Components unless you explicitly expose it with 'use server'",
        r"Functions cannot be passed.*Client Components|use server|Server Actions",
        "component_error", "nextjs", ">=14,<16", "linux",
        "true", 0.90, 0.90,
        "Passing a server function as prop to a Client Component. Need 'use server' directive.",
        [de("Convert the function to a client-side function",
            "Loses server-side benefits (DB access, secrets, etc.)", 0.65,
            sources=["https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions-and-mutations"]),
         de("Use an API route instead",
            "Server Actions are the recommended replacement for simple API routes", 0.55,
            sources=["https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions-and-mutations"])],
        [wa("Mark the function with 'use server' directive to make it a Server Action", 0.95,
            "'use server';\nasync function submitForm(data: FormData) { ... }",
            sources=["https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions-and-mutations"]),
         wa("Create a separate actions.ts file with 'use server' at the top", 0.92,
            "// app/actions.ts\n'use server';\nexport async function createItem(data: FormData) { ... }",
            sources=["https://nextjs.org/docs/app/building-your-application/data-fetching/server-actions-and-mutations"])],
    ))

    # ── DOCKER ──────────────────────────────────────────

    c.append(canon(
        "docker", "multi-stage-copy-from", "docker27-linux",
        "COPY --from=builder failed: stat /app/build: file not found in build stage",
        r"COPY --from.*failed|file not found.*build stage|COPY.*--from.*stat",
        "build_error", "docker", ">=27,<28", "linux",
        "true", 0.90, 0.90,
        "Multi-stage build COPY source path doesn't exist in the builder stage.",
        [de("Add the file to the build context",
            "Build context is for COPY without --from; --from copies from another stage", 0.80,
            sources=["https://docs.docker.com/build/building/multi-stage/"]),
         de("Use a single-stage build",
            "Loses multi-stage benefits (smaller final image, no build tools in prod)", 0.65,
            sources=["https://docs.docker.com/build/building/multi-stage/"])],
        [wa("Check the builder stage: the build output path may differ from what you're copying", 0.95,
            "# Verify: RUN ls -la /app/build  # add this to builder stage to debug",
            sources=["https://docs.docker.com/build/building/multi-stage/"]),
         wa("Ensure the build step in the builder stage actually runs and outputs to the expected path", 0.90,
            sources=["https://docs.docker.com/build/building/multi-stage/"])],
    ))

    c.append(canon(
        "docker", "compose-version-obsolete", "docker27-linux",
        "WARNING: the attribute 'version' is obsolete in docker compose",
        r"attribute.*version.*obsolete|version.*top-level element is obsolete",
        "config_warning", "docker", ">=27,<28", "linux",
        "true", 0.98, 0.95,
        "Docker Compose V2 no longer needs the 'version' field. Harmless warning.",
        [de("Downgrade Docker Compose",
            "Older versions are unmaintained — accept the new format", 0.80,
            sources=["https://docs.docker.com/compose/releases/"]),
         de("Pin version to '3.8' or another specific version",
            "Still triggers the warning — the field itself is obsolete", 0.75,
            sources=["https://docs.docker.com/reference/compose-file/version-and-name/"])],
        [wa("Simply remove the 'version' line from docker-compose.yml", 0.98,
            "# Remove this line:\n# version: '3.8'",
            sources=["https://docs.docker.com/reference/compose-file/version-and-name/"]),
         wa("It's just a warning — it still works. But removing it is cleaner", 0.90,
            sources=["https://docs.docker.com/reference/compose-file/version-and-name/"])],
    ))

    c.append(canon(
        "docker", "exit-code-137", "docker27-linux",
        "Container exited with code 137 (OOMKilled)",
        r"exit.*code 137|OOMKill|Killed|signal: killed",
        "oom_error", "docker", ">=27,<28", "linux",
        "partial", 0.80, 0.85,
        "Container killed by OOM killer (exit code 137 = SIGKILL). Exceeded memory limit.",
        [de("Set --oom-kill-disable",
            "System may freeze if container consumes all host memory", 0.85,
            sources=["https://docs.docker.com/engine/containers/resource_constraints/#limit-a-containers-access-to-memory"]),
         de("Remove memory limit entirely",
            "Container may consume all host memory and kill other processes", 0.70,
            sources=["https://docs.docker.com/engine/containers/resource_constraints/"])],
        [wa("Increase memory limit: docker run --memory=2g or in compose: mem_limit: 2g", 0.90,
            sources=["https://docs.docker.com/engine/containers/resource_constraints/#limit-a-containers-access-to-memory"]),
         wa("Profile application memory to find leaks or reduce footprint", 0.85,
            sources=["https://docs.docker.com/engine/containers/resource_constraints/"]),
         wa("For build-time OOM, increase Docker Desktop memory in Settings > Resources", 0.88,
            sources=["https://docs.docker.com/desktop/settings-and-maintenance/settings/"])],
    ))

    # ── GIT ──────────────────────────────────────────

    c.append(canon(
        "git", "bad-object", "git2-linux",
        "fatal: bad object HEAD",
        r"fatal: bad object|fatal: not a valid object",
        "corruption_error", "git", ">=2.30,<3.0", "linux",
        "partial", 0.75, 0.80,
        "Git repository is corrupted. HEAD or objects are broken.",
        [de("Delete .git and re-clone",
            "Loses all local branches, stashes, and unpushed commits", 0.70,
            sources=["https://git-scm.com/book/en/v2/Git-Internals-Maintenance-and-Data-Recovery"]),
         de("Run git gc --aggressive",
            "gc can't fix corrupted objects — may make things worse", 0.75,
            sources=["https://git-scm.com/docs/git-gc"])],
        [wa("Try git fsck to identify corrupted objects", 0.90,
            "git fsck --full",
            sources=["https://git-scm.com/docs/git-fsck"]),
         wa("Recover HEAD: git reflog to find last good commit, then git reset", 0.85,
            "git reflog\ngit reset --hard <good-commit>",
            sources=["https://git-scm.com/docs/git-reflog"]),
         wa("If remote is intact, backup local branches then re-clone", 0.80,
            sources=["https://git-scm.com/book/en/v2/Git-Internals-Maintenance-and-Data-Recovery"])],
    ))

    c.append(canon(
        "git", "large-file-push-rejected", "git2-linux",
        "remote: error: File X is 100.00 MB; this exceeds GitHub's file size limit of 100.00 MB",
        r"exceeds GitHub.*file size limit|this exceeds.*100.*MB|large files detected",
        "push_error", "git", ">=2.30,<3.0", "linux",
        "true", 0.85, 0.88,
        "File exceeds GitHub's 100MB limit. Can't push even after removing — it's in git history.",
        [de("Just delete the large file and push again",
            "File is still in git history — push will still fail", 0.90,
            sources=["https://docs.github.com/en/repositories/working-with-files/managing-large-files"]),
         de("Increase the file size limit",
            "GitHub's limit is fixed at 100MB — can't be changed", 0.95,
            sources=["https://docs.github.com/en/repositories/working-with-files/managing-large-files"])],
        [wa("Use git filter-branch or BFG Repo Cleaner to remove from history", 0.90,
            "git filter-branch --tree-filter 'rm -f large-file.bin' HEAD\n# or: bfg --strip-blobs-bigger-than 100M",
            sources=["https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository"]),
         wa("Use Git LFS for large files going forward: git lfs track '*.bin'", 0.88,
            "git lfs install\ngit lfs track '*.bin'\ngit add .gitattributes",
            sources=["https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage"]),
         wa("Add large files to .gitignore before committing", 0.85,
            sources=["https://git-scm.com/docs/gitignore"])],
    ))

    # ── KUBERNETES ──────────────────────────────────────────

    c.append(canon(
        "kubernetes", "dns-resolution-failed-pod", "k8s1-linux",
        "Error: Could not resolve host / nslookup failed in pod",
        r"Could not resolve|nslookup.*can't resolve|dial tcp.*no such host",
        "dns_error", "kubernetes", ">=1.28,<2.0", "linux",
        "partial", 0.82, 0.85,
        "Pod can't resolve DNS. CoreDNS issue, network policy blocking, or service doesn't exist.",
        [de("Hardcode IP addresses in the application",
            "IPs change — services are designed to be accessed by name", 0.80,
            sources=["https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/"]),
         de("Restart the pod",
            "If CoreDNS is broken, restarting the pod won't help", 0.65,
            sources=["https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/"])],
        [wa("Check if CoreDNS pods are running: kubectl get pods -n kube-system -l k8s-app=kube-dns", 0.92,
            sources=["https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/"]),
         wa("Test DNS from inside the pod: kubectl exec <pod> -- nslookup <service-name>", 0.90,
            sources=["https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/"]),
         wa("Use FQDN: service-name.namespace.svc.cluster.local for cross-namespace access", 0.88,
            sources=["https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/"])],
    ))

    c.append(canon(
        "kubernetes", "configmap-too-large", "k8s1-linux",
        "Error from server: etcd: request is too large",
        r"request is too large|etcd.*too large|ConfigMap.*exceeds maximum size",
        "storage_error", "kubernetes", ">=1.28,<2.0", "linux",
        "true", 0.88, 0.88,
        "ConfigMap/Secret exceeds 1MB etcd limit. Too much data in a single resource.",
        [de("Increase etcd max request size",
            "Requires cluster admin access and can affect etcd performance", 0.70,
            sources=["https://kubernetes.io/docs/concepts/configuration/configmap/"]),
         de("Split into many small ConfigMaps manually",
            "Hard to manage — consider using external configuration", 0.55,
            sources=["https://kubernetes.io/docs/concepts/configuration/configmap/"])],
        [wa("Use a volume mount with a PersistentVolumeClaim for large config files", 0.90,
            sources=["https://kubernetes.io/docs/concepts/storage/persistent-volumes/"]),
         wa("Use external configuration services (Vault, Parameter Store, etc.)", 0.88,
            sources=["https://kubernetes.io/docs/concepts/configuration/configmap/"]),
         wa("Compress or minify the config data, or split logically into multiple ConfigMaps", 0.82,
            sources=["https://kubernetes.io/docs/concepts/configuration/configmap/"])],
    ))

    # ── CUDA ──────────────────────────────────────────

    c.append(canon(
        "cuda", "cusolver-internal-error", "cuda12-a100",
        "RuntimeError: cusolver error: CUSOLVER_STATUS_INTERNAL_ERROR",
        r"cusolver.*INTERNAL_ERROR|cusolverDn.*error|CUSOLVER_STATUS",
        "library_error", "cuda", ">=12.0,<13.0", "linux",
        "partial", 0.78, 0.85,
        "cuSOLVER failure in linear algebra operations. Matrix may be singular or GPU memory corrupted.",
        [de("Retry the same operation",
            "If matrix is singular, retrying gives the same error", 0.70,
            sources=["https://docs.nvidia.com/cuda/cusolver/index.html"]),
         de("Switch to CPU computation as fallback",
            "Works but defeats the purpose of GPU acceleration", 0.50,
            sources=["https://pytorch.org/docs/stable/generated/torch.linalg.solve.html"])],
        [wa("Check if input matrix is singular or has NaN/Inf values", 0.90,
            "torch.isnan(matrix).any()  # check for NaN\ntorch.isinf(matrix).any()  # check for Inf",
            sources=["https://pytorch.org/docs/stable/generated/torch.isnan.html"]),
         wa("Add regularization to prevent singular matrices: A + eps * I", 0.85,
            "A = A + 1e-6 * torch.eye(A.size(0), device=A.device)",
            sources=["https://pytorch.org/docs/stable/generated/torch.linalg.solve.html"]),
         wa("Update CUDA and cuSOLVER to latest version for bug fixes", 0.78,
            sources=["https://docs.nvidia.com/cuda/cusolver/index.html"])],
        gpu="A100", vram=40,
    ))

    # ── RUST ──────────────────────────────────────────

    c.append(canon(
        "rust", "e0277-send-not-satisfied", "rust1-linux",
        "error[E0277]: `X` cannot be sent between threads safely",
        r"E0277.*cannot be sent between threads|Send.*is not satisfied",
        "concurrency_error", "rust", ">=1.70,<2.0", "linux",
        "true", 0.85, 0.90,
        "Type doesn't implement Send trait. Can't use across threads. Common with Rc, RefCell.",
        [de("Implement Send with unsafe impl",
            "Implementing Send unsafely on types that aren't thread-safe causes UB", 0.95,
            sources=["https://doc.rust-lang.org/std/marker/trait.Send.html"]),
         de("Use single-threaded runtime",
            "Limits application scalability unnecessarily", 0.55,
            sources=["https://doc.rust-lang.org/book/ch16-04-extensible-concurrency-sync-and-send.html"])],
        [wa("Use Arc instead of Rc for shared ownership across threads", 0.95,
            "use std::sync::Arc;\nlet shared = Arc::new(data);",
            sources=["https://doc.rust-lang.org/std/sync/struct.Arc.html"]),
         wa("Use Mutex/RwLock instead of RefCell for interior mutability across threads", 0.92,
            "use std::sync::Mutex;\nlet data = Arc::new(Mutex::new(value));",
            sources=["https://doc.rust-lang.org/std/sync/struct.Mutex.html"]),
         wa("If using async, ensure futures are Send by avoiding non-Send types across .await", 0.85,
            sources=["https://doc.rust-lang.org/book/ch16-04-extensible-concurrency-sync-and-send.html"])],
    ))

    c.append(canon(
        "rust", "e0433-unresolved-import", "rust1-linux",
        "error[E0433]: failed to resolve: use of undeclared crate or module",
        r"E0433.*failed to resolve|undeclared crate or module",
        "import_error", "rust", ">=1.70,<2.0", "linux",
        "true", 0.95, 0.95,
        "Crate or module not found. Missing dependency in Cargo.toml or wrong use path.",
        [de("Add the path to src/lib.rs manually",
            "If the crate isn't in Cargo.toml, it's not available", 0.75,
            sources=["https://doc.rust-lang.org/error_codes/E0433.html"]),
         de("Use extern crate (pre-2018 edition syntax)",
            "Unnecessary since Rust 2018 — just add to Cargo.toml", 0.70,
            sources=["https://doc.rust-lang.org/edition-guide/rust-2018/module-system/path-clarity.html"])],
        [wa("Add the dependency to Cargo.toml: [dependencies] section", 0.95,
            "cargo add <crate-name>",
            sources=["https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html"]),
         wa("Check use path: crate:: for local, module_name:: for deps", 0.90,
            "use crate::module::MyType;  // local\nuse serde::Serialize;  // external",
            sources=["https://doc.rust-lang.org/reference/items/use-declarations.html"]),
         wa("For feature-gated items, enable the feature in Cargo.toml", 0.82,
            'serde = { version = "1", features = ["derive"] }',
            sources=["https://doc.rust-lang.org/cargo/reference/features.html"])],
    ))

    # ── GO ──────────────────────────────────────────

    c.append(canon(
        "go", "context-deadline-exceeded", "go1-linux",
        "context deadline exceeded",
        r"context deadline exceeded|context canceled",
        "timeout_error", "go", ">=1.21,<2.0", "linux",
        "partial", 0.82, 0.85,
        "Operation timed out via context.WithTimeout/WithDeadline. Server call or DB query took too long.",
        [de("Remove the context timeout",
            "Operations may hang forever without timeouts", 0.75,
            sources=["https://pkg.go.dev/context#WithTimeout"]),
         de("Set a very large timeout",
            "Just delays the inevitable — find why the operation is slow", 0.60,
            sources=["https://pkg.go.dev/context#WithTimeout"])],
        [wa("Increase timeout to a reasonable value based on expected operation time", 0.90,
            "ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)",
            sources=["https://pkg.go.dev/context#WithTimeout"]),
         wa("Investigate why the operation is slow: check DB queries, network latency, etc.", 0.88,
            sources=["https://pkg.go.dev/context"]),
         wa("Add retry logic for transient timeouts", 0.80,
            sources=["https://pkg.go.dev/context"])],
    ))

    c.append(canon(
        "go", "assignment-to-entry-in-nil-map", "go1-linux",
        "panic: assignment to entry in nil map",
        r"assignment to entry in nil map",
        "runtime_error", "go", ">=1.21,<2.0", "linux",
        "true", 0.95, 0.95,
        "Writing to an uninitialized map. Maps must be created with make() before use.",
        [de("Check for nil before every map write",
            "Verbose and error-prone — just initialize the map", 0.70,
            sources=["https://go.dev/blog/maps"]),
         de("Use sync.Map for all maps",
            "sync.Map is for concurrent access — overkill for single-goroutine use", 0.65,
            sources=["https://pkg.go.dev/sync#Map"])],
        [wa("Initialize with make(): m := make(map[string]int)", 0.98,
            sources=["https://go.dev/blog/maps"]),
         wa("Or use map literal: m := map[string]int{}", 0.95,
            sources=["https://go.dev/blog/maps"]),
         wa("For struct fields, initialize in constructor or init function", 0.90,
            "func NewFoo() *Foo {\n    return &Foo{data: make(map[string]int)}\n}",
            sources=["https://go.dev/blog/maps"])],
    ))

    # ── PIP ──────────────────────────────────────────

    c.append(canon(
        "pip", "editable-install-requires-pyproject", "pip24-linux",
        "ERROR: Project file has a 'pyproject.toml' and its build backend is missing the 'build_editable' hook",
        r"build_editable.*hook|editable.*install.*failed|pip install -e.*error",
        "install_error", "pip", ">=24,<25", "linux",
        "true", 0.90, 0.90,
        "pip install -e . fails because build backend doesn't support editable installs.",
        [de("Use pip install . instead (non-editable)",
            "Loses live editing — need to reinstall after every change", 0.55,
            sources=["https://pip.pypa.io/en/stable/topics/local-project-installs/"]),
         de("Downgrade pip to bypass the check",
            "Old pip has other issues — better to fix the build config", 0.65,
            sources=["https://pip.pypa.io/en/stable/installation/"])],
        [wa("Add setuptools to build-system in pyproject.toml — it supports build_editable", 0.95,
            "[build-system]\nrequires = ['setuptools>=64']\nbuild-backend = 'setuptools.build_meta'",
            sources=["https://setuptools.pypa.io/en/latest/userguide/development_mode.html"]),
         wa("Or use pip install -e . --no-build-isolation if using a custom backend", 0.82,
            sources=["https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-no-build-isolation"])],
    ))

    c.append(canon(
        "pip", "subprocess-error-setuptools", "pip24-linux",
        "error: subprocess-exited-with-error: python setup.py egg_info did not run successfully",
        r"subprocess-exited-with-error|setup.py egg_info.*error|egg_info",
        "build_error", "pip", ">=24,<25", "linux",
        "true", 0.85, 0.88,
        "Legacy setup.py based install failed. Package may need C compiler, headers, or pyproject.toml migration.",
        [de("Use --no-build-isolation",
            "May fix some cases but can cause dependency conflicts in build env", 0.55,
            sources=["https://pip.pypa.io/en/stable/cli/pip_install/"]),
         de("Install from a wheel instead",
            "If a wheel exists, pip would already use it — it's building because there's no wheel", 0.70,
            sources=["https://pip.pypa.io/en/stable/topics/wheels/"])],
        [wa("Install build dependencies: apt install python3-dev build-essential (for C extensions)", 0.90,
            "sudo apt install python3-dev build-essential  # Debian/Ubuntu\nbrew install python  # macOS",
            sources=["https://pip.pypa.io/en/stable/topics/wheels/"]),
         wa("Check if a newer version has a pre-built wheel: pip install --prefer-binary <pkg>", 0.85,
            sources=["https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-prefer-binary"]),
         wa("Install package-specific system deps (e.g., libpq-dev for psycopg2, libxml2-dev for lxml)", 0.88,
            sources=["https://pip.pypa.io/en/stable/topics/wheels/"])],
    ))

    # ── AWS ──────────────────────────────────────────

    c.append(canon(
        "aws", "region-not-set", "awscli2-linux",
        "botocore.exceptions.NoRegionError: You must specify a region",
        r"NoRegionError|You must specify a region|could not be found.*region",
        "config_error", "aws", ">=2.0,<3.0", "linux",
        "true", 0.95, 0.95,
        "AWS region not configured. Set via env var, config file, or SDK parameter.",
        [de("Hardcode us-east-1 everywhere",
            "Breaks for resources in other regions and couples code to region", 0.65,
            sources=["https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html"]),
         de("Set region in every boto3 call",
            "Verbose and easy to miss — set it once globally", 0.55,
            sources=["https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html"])],
        [wa("Set AWS_DEFAULT_REGION env var: export AWS_DEFAULT_REGION=us-east-1", 0.95,
            sources=["https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html"]),
         wa("Configure in ~/.aws/config: aws configure set region us-east-1", 0.92,
            sources=["https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html"]),
         wa("Set in boto3 client: boto3.client('s3', region_name='us-east-1')", 0.88,
            sources=["https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html"])],
    ))

    # ── TERRAFORM ──────────────────────────────────────────

    c.append(canon(
        "terraform", "for-each-sensitive", "tf1-linux",
        "Error: Invalid for_each argument: Sensitive values not allowed in for_each",
        r"Invalid for_each.*[Ss]ensitive|for_each.*sensitive value",
        "config_error", "terraform", ">=1.5,<2.0", "linux",
        "true", 0.90, 0.90,
        "for_each can't iterate over sensitive values. Terraform can't plan resources with hidden keys.",
        [de("Mark everything as non-sensitive",
            "Exposes secrets in plan output and state", 0.80,
            sources=["https://developer.hashicorp.com/terraform/language/expressions/function-calls#sensitive"]),
         de("Use count instead of for_each",
            "Loses the benefit of stable resource keys — risky for updates", 0.60,
            sources=["https://developer.hashicorp.com/terraform/language/meta-arguments/count"])],
        [wa("Use nonsensitive() to unwrap the value for for_each keys only", 0.92,
            "for_each = nonsensitive(var.my_sensitive_map)",
            sources=["https://developer.hashicorp.com/terraform/language/functions/nonsensitive"]),
         wa("Restructure to use non-sensitive keys with sensitive values as attributes", 0.85,
            sources=["https://developer.hashicorp.com/terraform/language/expressions/function-calls"])],
    ))

    c.append(canon(
        "terraform", "moved-block-error", "tf1-linux",
        "Error: Moved object no longer exists",
        r"Moved object no longer exists|moved block.*error",
        "refactor_error", "terraform", ">=1.5,<2.0", "linux",
        "true", 0.88, 0.90,
        "Terraform moved block references a resource that doesn't exist in state.",
        [de("Delete the moved block and force apply",
            "Terraform may destroy and recreate the resource", 0.75,
            sources=["https://developer.hashicorp.com/terraform/language/moved"]),
         de("Manually edit the state file",
            "Error-prone and can corrupt state", 0.80,
            sources=["https://developer.hashicorp.com/terraform/language/state"])],
        [wa("Use terraform state mv to move the resource in state first, then add moved block", 0.90,
            "terraform state mv aws_instance.old aws_instance.new",
            sources=["https://developer.hashicorp.com/terraform/cli/commands/state/mv"]),
         wa("Verify the 'from' address matches exactly what's in the state", 0.88,
            "terraform state list | grep <resource>",
            sources=["https://developer.hashicorp.com/terraform/language/moved"])],
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
    print(f"Wave 6: wrote {written} new canons, skipped {skipped} existing")


if __name__ == "__main__":
    main()
