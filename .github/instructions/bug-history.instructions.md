---
description: This instruction file provides guidelines for documenting and managing bug fixing history.
---

<critical>MANDATORY POLICY: Any bug discovered during development MUST be fixed and documented here, even if it falls outside the scope of the current task or issue being worked on. Do not defer, ignore, or leave bugs for later — fix them immediately and add an entry below.</critical>

# Bug History — hhh-maps-service

Document every bug found and fixed during development. Include root cause, fix applied, and lesson learned so they don't recur.

---

## BUG-001: Mutation of module-level seed data globals

**PR:** #2 (SETUP-2: Seed test locations) | **Severity:** Medium

**Symptom:** `seed_locations()` passed the module-level `SYSTEMS` list directly to service calls, mutating global state. Running the seed script twice would corrupt data.

**Root cause:** `SYSTEMS` and child locations were module-level dataclass instances. Passing them directly to `create()` allowed the service to mutate the original objects (e.g., setting `id` on them).

**Fix:** Used `dataclasses.replace(system)` to create copies before passing to `create()`. Applied the same fix in tests where `fake_create` was mutating the location argument.

**Lesson:** Always copy dataclass instances before passing them to functions that may mutate them. Use `dataclasses.replace()` for shallow copies.

---

## BUG-002: Missing `__main__` entrypoint for seed script

**PR:** #2 | **Severity:** Low

**Symptom:** `python -m src.infrastructure.seed.seed_locations` didn't work — no `if __name__ == "__main__"` block.

**Fix:** Added `if __name__ == "__main__"` block that instantiates `Settings`, creates the DI injector, and calls `seed_locations(service)`.

---

## BUG-003: Missing CORS middleware blocks all frontend location features

**Issue:** #13 | **Severity:** Critical

**Symptom:** Both frontends (localhost:3000 and localhost:3001) get CORS errors on every `/locations/*` request. Backoffice location management, hauling order location autocomplete, and all frontend location features are completely broken.

**Root cause:** `src/main.py` in `create_app()` never configures `CORSMiddleware`. Every other service (contracts, commodities, ships, etc.) already has CORS configured — maps-service was the only one missing it.

**Fix:** Added `CORSMiddleware` to `create_app()` with `allow_origins=["http://localhost:3000", "http://localhost:3001"]`, `allow_methods=["*"]`, `allow_headers=["*"]`.

**Status:** ✅ Fixed.

**Lesson:** When scaffolding a new service, use an existing service as a template and verify all middleware is present. CORS is easy to miss because the backend works fine — the error only appears in browser requests.
