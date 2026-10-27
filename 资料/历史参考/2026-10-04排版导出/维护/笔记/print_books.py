# -*- coding: utf-8 -*-
"""Chrome headless 渲染两册 PDF（书签由 --generate-pdf-document-outline 生成）。"""
import os
import pathlib
import subprocess

BUILD = pathlib.Path(r"D:/Program Project/SpecialtyCourses/_tmp/pdf_v3/build_notes")
OUT = pathlib.Path(r"D:/Program Project/SpecialtyCourses/_tmp/pdf_v3/产出")
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"

os.makedirs(OUT, exist_ok=True)
for idx, name in enumerate(["代码总结", "重邮数据结构"], start=1):
    out = OUT / f"{name}.pdf"
    cmd = [
        CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
        "--generate-pdf-document-outline", "--virtual-time-budget=60000",
        f"--user-data-dir={BUILD / f'chrome_{idx}'}",
        f"--print-to-pdf={out}", (BUILD / f"{name}.html").as_uri(),
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=300)
    size = out.stat().st_size if out.exists() else -1
    print(name, "rc=", r.returncode, "size=", size, r.stderr.decode("utf-8", "ignore")[-300:])
