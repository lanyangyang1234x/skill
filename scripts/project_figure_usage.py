#!/usr/bin/env python3
"""Detect common figure/diagram calls in the main TeX input graph.

Exit 0 when candidates exist, 1 when none are found, and 2 on input errors.
This static detector ignores comments and ordinary macro/environment
definitions. It is not a complete source-to-output figure inventory and does
not expand arbitrary TeX macros or resolve conditional execution.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from audit_bibliography import outside_definitions, strip_comments, tex_graph


FIGURE_USAGE_RE = re.compile(
    r"\\(?:includegraphics|SourceFigure|xymatrix|xy|tikz)(?![A-Za-z@])"
    r"|\\begin\s*\{(?:tikzpicture|tikzcd|xy|pspicture)\*?\}"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("main_tex")
    args = parser.parse_args()
    project = args.project_dir.expanduser().resolve()
    try:
        files = tex_graph(project, args.main_tex, ignore_definitions=True)
        count = sum(
            len(FIGURE_USAGE_RE.findall(outside_definitions(strip_comments(path.read_text(encoding="utf-8")))))
            for path in files
        )
    except (OSError, UnicodeError, SystemExit) as exc:
        print(f"Figure usage check failed: {exc}", file=sys.stderr)
        return 2
    print(f"Figure usage candidates: {count} in {len(files)} TeX input files (static check).")
    return 0 if count else 1


if __name__ == "__main__":
    raise SystemExit(main())
