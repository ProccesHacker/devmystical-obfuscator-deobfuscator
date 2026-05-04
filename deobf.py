from __future__ import annotations

import ast
import builtins
import pickle
from pathlib import Path
from typing import Any


ENC = "ISO-8859-1"


class Error(ValueError):
    pass


def banner() -> None:
    print(f"""\033[31m
             %                                                    %
              %%                                                %%
               %%%                                            %%%
                 %%%%                                      %%%%
                   %%%%%                                %%%%%
                     %%%%%%%                        %%%%%%%
                       %%%%%%%%:                :%%%%%%%%
                         %%%%%%%%%%          %%%%%%%%%%
                           :%%%%%%%%        %%%%%%%%:
                              %%%%%%        %%%%%%
                               %%%%.         %%%%
                               %%%%          %%%%
                              :%%%%%        %%%%%:
                              %%%%%%%%%  %%%%%%%%%
                                %%%%%%%%%%%%%%%%
                                  %%%%%%%%%%%%
                                    #%%%%%%
                                       %%

                        Деобфускатор создавал ProcHacker.""")


def looks(src: str) -> bool:
    marks = ["ISO-8859", "pickle.loads", "co_argcount", "__code__", "globals"]
    n = 0
    for x in marks:
        if x in src:
            n += 1
    return n >= 3


def run(src: str) -> dict[str, Any]:
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        raise Error(f"не удалось распарсить файл {e}") from e

    box: dict[str, Any] = {"__builtins__": builtins, "__file__": "<devmystical>"}
    for node in tree.body:
        if isinstance(node, ast.Assign) or isinstance(node, ast.AnnAssign) or isinstance(node, ast.AugAssign):
            try:
                code = compile(ast.Module([node], []), "<devmystical>", "exec")
                exec(code, box, box)
            except Exception as e:
                text = ast.unparse(node)
                raise Error(f"не смог вытащить данные {text[:180]}") from e
    return box


def pair(obj: Any) -> bool:
    if not isinstance(obj, list):
        return False
    if not obj:
        return False
    ok = True
    for x in obj:
        ok = ok and isinstance(x, tuple)
        ok = ok and len(x) == 2
        ok = ok and isinstance(x[0], list)
        ok = ok and isinstance(x[1], str)
    return ok


def find(box: dict[str, Any]) -> list[tuple[list[Any], str]]:
    arr = []
    for x in box.values():
        if pair(x):
            arr.append(x)
    if not arr:
        raise Error("не найден список pickle-объектов.")
    return max(arr, key=len)


def path(arr: list[Any]) -> list[str | int]:
    out = []
    for x in arr:
        if type(x) is str or type(x) is int:
            out.append(x)
    return out


def get(obj: Any, key: str | int) -> Any:
    if isinstance(key, int):
        return obj[key]
    return getattr(obj, key)


def put(obj: Any, key: str | int, val: Any) -> None:
    if isinstance(key, int):
        obj[key] = val
    else:
        setattr(obj, key, val)


def restore(arr: list[tuple[list[Any], str]]) -> ast.AST:
    root = None
    for raw, data in reversed(arr):
        try:
            obj = pickle.loads(data.encode(ENC))
        except Exception as e:
            raise Error("не распаковался pickle.") from e

        p = path(raw)
        if not p:
            if not isinstance(obj, ast.AST):
                raise Error("корень не AST.")
            root = obj
        else:
            if root is None:
                raise Error("нет корня AST.")
            cur = root
            for x in p[:-1]:
                cur = get(cur, x)
            put(cur, p[-1], obj)
    if root is None:
        raise Error("не удалось восстановить AST.")
    return ast.fix_missing_locations(root)


def deobfuscate_source(source: str) -> str:
    if not looks(source):
        raise Error("файл не похож на обфу от DevMystical.")
    box = run(source)
    arr = find(box)
    tree = restore(arr)
    return ast.unparse(tree) + "\n"


def deobfuscate_file(input_path: str | Path, output_path: str | Path | None = None) -> Path:
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.with_name(input_path.stem + "_deobf.py")
    output_path = Path(output_path)
    src = input_path.read_text(encoding="utf-8")
    out = deobfuscate_source(src)
    output_path.write_text(out, encoding="utf-8")
    return output_path


def main() -> None:
    banner()
    file = ""
    while not file:
        file = input("Введите путь к файлу: ").strip().strip('"')
    out = deobfuscate_file(file)
    print(f"Deobfuscated file written to: {out}")


if __name__ == "__main__":
    main()
