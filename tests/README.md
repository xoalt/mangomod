# Development and testing

Run these commands from the repository root, with the runtime dependencies in the [README](../README.md#install) installed. The standard suite includes custom theme checks:

```sh
PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_*.py'
```

## Graphical checks

In a graphical session:

```sh
PYTHONPATH=. python3 tests/review_ui.py
PYTHONPATH=. python3 tests/smoke_ui.py
PYTHONPATH=. python3 tests/startup_ui.py
```

The graphical checks use temporary configs and preferences. The startup check exercises the default OpenGL startup path. Some integration tests require Mango on `PATH`.

## Compositor validation

To compare native validation with MangoMod using the installed compositor:

```sh
PYTHONPATH=. python3 tests/system_validation.py --config /path/to/config.conf
```

This validates staged copies and verifies that original config bytes are unchanged. It does not reload the running compositor. Its report can contain local file paths; review it before sharing.

## Build packages

With the `build` and `hatchling` development tools installed:

```sh
python3 -m build
```

Packages are written to `dist/`. The wheel contains the application and licenses; the source archive also includes the installer, documentation, assets, and tests. GTK-related dependencies remain system packages.

The application version is defined in `mangomod/__init__.py`; the package build reads the same value. Generated files and caches are ignored by Git.
