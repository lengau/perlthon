from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .typed import _introspect_module

_POD_MARKUP_RE = re.compile(r"[A-Z]<([^>]+)>")
_POD_NAME_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)")


def _class_name(module_name: str) -> str:
    return re.sub(r"\W+", "_", module_name.replace("::", "_"))


def _stub_path(root: Path, module_name: str) -> Path:
    return root.joinpath(*module_name.split("::")).with_suffix(".pyi")


def _ensure_packages(root: Path, path: Path) -> None:
    relative_parent = path.parent.relative_to(root)
    current = root
    for part in relative_parent.parts:
        current /= part
        current.mkdir(exist_ok=True)
        init_file = current / "__init__.pyi"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")


def _module_file(module_name: str) -> Path | None:
    script = (
        "use strict; use warnings; my $module = shift @ARGV;"
        "(my $file = $module) =~ s!::!/!g; $file .= '.pm';"
        'eval "require $module; 1" or exit 0;'
        "print $INC{$file} // q{};"
    )
    result = subprocess.run(
        ["perl", "-e", script, module_name],
        capture_output=True,
        text=True,
        check=False,
    )
    path = result.stdout.strip()
    if not path:
        return None
    module_path = Path(path)
    if not module_path.exists():
        return None
    return module_path


def _pod_target(line: str, known_names: set[str]) -> str | None:
    candidate = line.strip()
    if not candidate:
        return None
    candidate = candidate.removeprefix("*").strip()
    markup_match = _POD_MARKUP_RE.fullmatch(candidate)
    if markup_match:
        candidate = markup_match.group(1)
    name_match = _POD_NAME_RE.search(candidate)
    if not name_match:
        return None
    name = name_match.group(1)
    if name in known_names:
        return name
    return None


def _pod_docs(module_name: str, functions: list[str]) -> dict[str, str]:
    module_path = _module_file(module_name)
    if module_path is None:
        return {}

    known_names = set(functions)
    docs: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_name, current_lines
        if current_name and current_lines:
            text = "\n".join(line.rstrip() for line in current_lines).strip()
            if text:
                docs[current_name] = text
        current_name = None
        current_lines = []

    for raw_line in module_path.read_text(
        encoding="utf-8", errors="ignore"
    ).splitlines():
        if raw_line.startswith("=head"):
            flush()
            current_name = _pod_target(
                raw_line.split(maxsplit=1)[1] if " " in raw_line else "", known_names
            )
            continue
        if raw_line.startswith("=item"):
            flush()
            current_name = _pod_target(raw_line[5:], known_names)
            continue
        if raw_line.startswith("="):
            flush()
            continue
        if current_name is not None:
            current_lines.append(raw_line)

    flush()
    return docs


def _docstring_block(text: str) -> str:
    escaped = text.replace('"""', '"""')
    return f'        """{escaped}"""\n'


def _render_stub(module_name: str, functions: list[str]) -> str:
    class_name = _class_name(module_name)
    docs = _pod_docs(module_name, functions)
    lines = [
        "from typing import Any\n",
        "\n",
        "from perlthon.typed import TypedModule\n",
        "\n",
        f"class {class_name}(TypedModule):\n",
        f'    """Generated stub for Perl module {module_name}."""\n',
        "\n",
        "    def available_functions(self) -> list[str]: ...\n",
    ]
    for function_name in functions:
        if not function_name.isidentifier():
            continue
        lines.append("\n")
        lines.append(f"    def {function_name}(self, *args: Any) -> Any:\n")
        if doc := docs.get(function_name):
            lines.append(_docstring_block(doc))
        lines.append("        ...\n")
    return "".join(lines)


def generate_stubs(modules: list[str], output_dir: str) -> None:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    for module_name in modules:
        functions = _introspect_module(module_name)
        stub_path = _stub_path(root, module_name)
        stub_path.parent.mkdir(parents=True, exist_ok=True)
        _ensure_packages(root, stub_path)
        stub_path.write_text(_render_stub(module_name, functions), encoding="utf-8")
