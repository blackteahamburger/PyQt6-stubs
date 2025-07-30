# Copyright (c) 2025 Blackteahamburger <blackteahamburger@outlook.com>
#
# Adapted from https://github.com/python-qt-tools/PyQt6-stubs/blob/main/generate_upstream.py
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/>.
#
"""Utility functions to fix PyQt6 stub files."""

import re
import subprocess
from pathlib import Path
from typing import Final

SRC_DIR: Path = Path(__file__).parent.joinpath("PyQt6-stubs")

# Deprecated typing aliases mapping, refer to the official documentation
DEPRECATED_TYPING_ALIASES: Final = {
    "typing.List": "list",
    "typing.Dict": "dict",
    "typing.Set": "set",
    "typing.FrozenSet": "frozenset",
    "typing.Tuple": "tuple",
    "typing.Type": "type",
    "typing.DefaultDict": "collections.defaultdict",
    "typing.OrderedDict": "collections.OrderedDict",
    "typing.Counter": "collections.Counter",
    "typing.ChainMap": "collections.ChainMap",
    "typing.Deque": "collections.deque",
    "typing.ByteString": "bytes",
    "typing.Awaitable": "collections.abc.Awaitable",
    "typing.Coroutine": "collections.abc.Coroutine",
    "typing.AsyncIterable": "collections.abc.AsyncIterable",
    "typing.AsyncIterator": "collections.abc.AsyncIterator",
    "typing.Iterable": "collections.abc.Iterable",
    "typing.Iterator": "collections.abc.Iterator",
    "typing.Generator": "collections.abc.Generator",
    "typing.Reversible": "collections.abc.Reversible",
    "typing.Container": "collections.abc.Container",
    "typing.Collection": "collections.abc.Collection",
    "typing.Callable": "collections.abc.Callable",
    "typing.AbstractSet": "collections.abc.Set",
    "typing.MutableSet": "collections.abc.MutableSet",
    "typing.Mapping": "collections.abc.Mapping",
    "typing.MutableMapping": "collections.abc.MutableMapping",
    "typing.Sequence": "collections.abc.Sequence",
    "typing.MutableSequence": "collections.abc.MutableSequence",
    "typing.MappingView": "collections.abc.MappingView",
    "typing.KeysView": "collections.abc.KeysView",
    "typing.ItemsView": "collections.abc.ItemsView",
    "typing.ValuesView": "collections.abc.ValuesView",
    "typing.ContextManager": "collections.abc.ContextManager",
    "typing.AsyncContextManager": "collections.abc.AsyncContextManager",
}


def find_enum_lines(lines: list[str]) -> set[int]:
    """
    Find lines that are inside enum class bodies.

    Args:
        lines (list[str]): List of lines from a .pyi file.

    Returns:
        set[int]: Indices of lines that are inside enum class bodies.

    """
    enum_lines: set[int] = set()
    in_enum = False
    class_indent = ""
    for i, line in enumerate(lines):
        m = re.match(r"^(\s*)class\s+\w+\s*\(.*?enum\.\w+.*?\)\s*:", line)
        if m:
            in_enum = True
            class_indent = m.group(1)
            continue
        if in_enum:
            # If line is blank, continue
            if not line.strip():
                enum_lines.add(i)
                continue
            # If dedented to class or less, enum ends
            if not line.startswith(class_indent + " ") and line.strip():
                in_enum = False
                continue
            # Otherwise, it's inside enum
            enum_lines.add(i)
    return enum_lines


def insert_imports(lines: list[str], filename: str) -> list[str]:
    """
    Insert necessary imports.

    Args:
        lines (list[str]): List of lines from a .pyi file.
        filename (str): The name of the file being processed.

    Returns:
        list[str]: Modified list of lines with the import inserted if needed.

    """
    insert_idx = 0
    while insert_idx < len(lines) and (
        lines[insert_idx].strip().startswith("#")
        or not lines[insert_idx].strip()
    ):
        insert_idx += 1

    imports = ["import collections.abc\n", "from typing import Any\n"]
    if filename == "QtStateMachine.pyi":
        imports.append("from PyQt6.QtCore import pyqtBoundSignal\n")
    if filename == "QtGui.pyi":
        imports.append("from PyQt6.QtWidgets import QMenu\n")
    if filename == "sip.pyi":
        imports.append("import typing\n")
    if filename in {"QtDataVisualization.pyi", "QtGraphs.pyi"}:
        imports.append("import sip\n")

    for imp in imports:
        lines.insert(insert_idx, imp)
        insert_idx += 1
    return lines


def replace_deprecated_aliases(content: str) -> str:
    """
    Replace deprecated typing aliases with their modern equivalents.

    Args:
        content (str): The content of a .pyi file as a string.

    Returns:
        str: The content with deprecated typing aliases replaced.

    """
    for old, new in DEPRECATED_TYPING_ALIASES.items():
        content = re.sub(rf"\b{re.escape(old)}\b", new, content)
    return content


def process_type_comments(content: str, enum_lines: set[int]) -> str:
    """
    Convert type comments to type annotations, except for enum variables.

    Args:
        content (str): The content of a .pyi file as a string.
        enum_lines (set[int]): Indices of lines that are
        inside enum class bodies.

    Returns:
        str: The content with type comments converted to
        type annotations where appropriate.

    """
    new_lines: list[str] = []
    for idx, line in enumerate(content.splitlines()):
        m = re.match(
            r"^(\s*\w+)\s*=\s*(\.\.\.|[^\n#]+)\s*#\s*type:\s*([^\n]+)$", line
        )
        if m:
            var, val, typ = m.group(1), m.group(2), m.group(3)
            if idx in enum_lines:
                new_lines.append(f"{var} = {val}")
            else:
                new_lines.append(f"{var}: {typ} = {val}")
            continue
        m2 = re.match(r"^(\s*\w+)\s*=\s*\.\.\.\s*#\s*type:\s*([^\n]+)$", line)
        if m2:
            if idx in enum_lines:
                new_lines.append(f"{m2.group(1)} = ...")
            else:
                new_lines.append(f"{m2.group(1)}: {m2.group(2)} = ...")
            continue
        new_lines.append(line)
    return "\n".join(new_lines)


def remove_try_except_blocks(text: str) -> str:
    """
    Remove try-except blocks, keeping only the code inside the try block.

    Args:
        text (str): The content of a .pyi file as a string.

    Returns:
        str: The content with try-except blocks removed.

    """
    pattern = re.compile(
        r"try:\n((?:[ \t]+[^\n]*\n)+)except[^\n]*:\n((?:[ \t]+[^\n]*\n)+)",
        re.MULTILINE,
    )
    while True:
        m = pattern.search(text)
        if not m:
            break
        try_block: str = m.group(1)
        try_block = re.sub(r"^[ \t]{4}", "", try_block, flags=re.MULTILINE)
        text = text[: m.start()] + try_block + text[m.end() :]
    return text


def replace_union_optional(expr: str) -> str:
    """
    Replace typing.Optional and typing.Union with X | None and X | Y.

    Args:
        expr (str): The expression to process.

    Returns:
        str: The expression with typing.Optional and typing.Union replaced.

    """

    # Replace typing.Optional[X] with X | None
    def optional_repl(m: re.Match[str]) -> str:
        inner = replace_union_optional(m.group(1))
        return f"{inner} | None"

    expr = re.sub(
        r"\btyping\.Optional\[\s*([^\[\]]+?)\s*\]", optional_repl, expr
    )

    # Replace typing.Union[X, Y, ...] with X | Y | ...
    def union_repl(m: re.Match[str]) -> str:
        inner = m.group(1)
        # Split by comma, but handle nested brackets
        parts: list[str] = []
        depth = 0
        buf = ""
        for c in inner:
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
            if c == "," and depth == 0:
                parts.append(buf.strip())
                buf = ""
            else:
                buf += c
        if buf:
            parts.append(buf.strip())
        parts = [replace_union_optional(p) for p in parts]
        return " | ".join(parts)

    # Handle nested Unions
    while True:
        new_expr = re.sub(
            r"\btyping\.Union\[\s*([^\[\]]+?)\s*\]", union_repl, expr
        )
        if new_expr == expr:
            break
        expr = new_expr
    return expr


def add_eq_ne_return_type(content: str) -> str:
    """
    Add return type annotation -> bool for __eq__ and __ne__ methods.

    Args:
        content (str): Content of the .pyi file

    Returns:
        str: Processed content

    """
    # Match def __eq__(self, other: object): ...
    # or def __ne__(self, other: object): ...
    pattern = re.compile(
        r"(def\s+(__eq__|__ne__)\s*\(\s*self\s*,\s*other\s*:\s*object\s*\))\s*:\s*\.\.\.",
        re.MULTILINE,
    )
    return pattern.sub(r"\1 -> bool: ...", content)


def fix_callable_and_sip_array(content: str) -> str:
    """
    Add type parameters to collections.abc.Callable and sip.array if missing.

    Args:
        content (str): The content of a .pyi file as a string.

    Returns:
        str: The content with type parameters added to Callable and sip.array.

    """
    # Replace collections.abc.Callable without type parameters
    content = re.sub(
        r"\bcollections\.abc\.Callable\b(?!\[)",
        "collections.abc.Callable[..., typing.Any]",
        content,
    )
    # Replace sip.array without type parameters
    return re.sub(r"\bsip\.array\b(?!\[)", "sip.array[typing.Any]", content)


def split_params(params: str) -> list[str]:
    """
    Split parameters string into a list.

    Args:
        params (str): The parameters string to split.

    Returns:
        list[str]: List of parameters

    """
    result: list[str] = []
    buf = ""
    paren = 0
    bracket = 0
    for c in params:
        if c == "(":
            paren += 1
        elif c == ")":
            paren -= 1
        elif c == "[":
            bracket += 1
        elif c == "]":
            bracket -= 1
        if c == "," and paren == 0 and bracket == 0:
            result.append(buf.strip())
            buf = ""
        else:
            buf += c
    if buf.strip():
        result.append(buf.strip())
    return result


def add_missing_type_hints(content: str) -> str:
    """
    Add missing type hints for arguments in function definitions.

    Args:
        content (str): The content of a .pyi file as a string.

    Returns:
        str: content with missing type hints added.

    """

    def repl(match: re.Match[str]) -> str:
        params = match.group(1)

        def param_repl(p: str) -> str:
            p = p.strip()
            # Skip parameters with existing type annotations
            if p in {"self", "cls"} or ":" in p or not p:
                return p
            return f"{p}: typing.Any"

        param_list = [param_repl(x) for x in split_params(params)]
        return f"({', '.join(param_list)})"

    pattern = re.compile(r"\(([^)]*)\)")
    def_line_pattern = re.compile(
        r"^(\s*def\s+\w+\s*)\(([^)]*)\)(.*)", re.MULTILINE
    )

    def def_repl(m: re.Match[str]) -> str:
        prefix, params, suffix = m.group(1), m.group(2), m.group(3)
        new_params = pattern.sub(repl, f"({params})")
        return f"{prefix}{new_params}{suffix}"

    return def_line_pattern.sub(def_repl, content)


def fix_sip_pyi(content: str) -> str:
    """
    Apply special fixes for sip.pyi stub file.

    Args:
        content (str): The content of sip.pyi file.

    Returns:
        str: The fixed content.

    """
    # Fix Buffer type definition
    content = re.sub(
        r"Buffer\s*=\s*Union\[\s*bytes\s*,\s*bytearray\s*,\s*memoryview\s*,\s*'array'\s*,\s*'voidptr'\s*\]",
        "Buffer = Union[bytes, bytearray, memoryview, "
        "'array[typing.Any]', 'voidptr']",
        content,
    )
    # Replace _T with T
    return content.replace("_T", "T")


def fix_file(path: Path) -> None:
    """
    Fix a PyQt6 stub file.

    The following fixes are applied:
    - add missing imports
    - replace deprecated typing aliases
    - convert type comments to type annotations
    - remove try-except blocks
    - replace typing.Union/Optional
    - add __eq__/__ne__ return type
    - add missing type parameters for collections.abc.Callable and sip.array
    - and add missing type hints for *args and **kwargs.
    - special fixes for sip.pyi
    Args:
        path (Path): Path to the .pyi file to fix.

    """
    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    lines = insert_imports(lines, path.name)
    enum_lines = find_enum_lines(lines)
    content = "".join(lines)
    content = replace_deprecated_aliases(content)
    content = process_type_comments(content, enum_lines)
    content = remove_try_except_blocks(content)
    content = replace_union_optional(content)
    content = add_eq_ne_return_type(content)
    content = fix_callable_and_sip_array(content)
    content = add_missing_type_hints(content)
    if path.name == "sip.pyi":
        content = fix_sip_pyi(content)

    with path.open("w", encoding="utf-8") as f:
        f.write(content)


def fix_all() -> None:
    """Fix all PyQt6 stub files in the SRC_DIR directory."""
    for pyi in SRC_DIR.glob("*.pyi"):
        fix_file(pyi)
        subprocess.check_call([
            "/usr/bin/ruff",
            "check",
            "--fix-only",
            str(pyi),
        ])
        subprocess.check_call(["/usr/bin/ruff", "format", str(pyi)])


if __name__ == "__main__":
    fix_all()
