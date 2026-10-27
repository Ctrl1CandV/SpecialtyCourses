# 工具

从项目根目录运行。Python环境需要reportlab、pypdf、pypdfium2、PyMuPDF、Pillow、PyYAML、python-pptx；Node依赖见本目录package.json和lockfile。

| 用途 | 入口 |
|---|---|
| 题库查询/导出/导入 | `python tools/题库/tiku.py` |
| 六套模拟卷交付核验 | `python tools/verify_exam_delivery.py` |
| 当前C3与2027押题交付指纹核对 | `python -B tools/verify_current_delivery.py`；仅需Python标准库，不生成或覆盖课件/试卷 |
| 六套卷蓝图一致性核对 | `python tools/exam_blueprint.py` |
| 冲刺合集PDF生成与代码验证 | `python -B tools/build_sprint_collection.py`；`python -B tools/verify_sprint_collection.py`（需要g++，可用`--compiler`指定路径） |
| 旧设计种子验算（当前部分输入绑定已失效） | `verify_exam_seeds.py`；保留作历史核验来源，不自动重绑定 |
| 六套卷成品及MD生成 | `build_exam_papers.py`、`build_exam_answers.py`及配图脚本 |
| 登记新路径下的交付清单，不生成ZIP | `python tools/package_exam_delivery.py` |
| 2027三套押题试卷、答案及逐题讲解源稿生成 | `python tools/build_2027_prediction.py`（`--render`输出临时预览，`--papers 1`选套） |
| 去年三套押题答案生成 | `python tools/build_prediction_answers.py 一`（或二、三） |
| 押题答案算法功能验证 | `python tools/verify_prediction_algorithms.py` |
| 押题答案逐页渲染与边界检查 | `python tools/verify_prediction_layout.py 一`（或二、三） |
| 去年机构三套模拟答案生成 | `python tools/build_institution_mock_answers.py 一`（或二、三） |
| 模拟答案指纹、版面与六道C算法验算 | `python tools/verify_institution_mock_answers.py --render --algorithms`；算法验算需要GCC |
| 通用PPT生成 | `render-pptx.js`；内容规范见[CONTENT-SPEC.md](CONTENT-SPEC.md) |
| C3课件生成 | `../课程/课件/C3/维护/render_c3.mjs`，使用@oai/artifact-tool；C3不使用会覆盖课件的旧check.js |
| C2-B-pro旧构建来源和只读结构检查 | [c2b](c2b/)，先读[当前文件依据](../课程/课件/C2/C2-B-pro/当前文件依据.md) |
| 主讲视频转写 | `transcribe.py` |

`check.js`会调用渲染器覆盖PPT，不用于随意检查封存或手工修改课件。C2-B的旧构建检查结果不能替代当前手改成品和WPS实际放映。

## 在另一台电脑继续维护

PPT/PDF及可读讲稿已随仓库保存，可以直接打开审阅、录制。重建才需要相应工具：先在`tools/`运行`npm ci`安装lockfile中的Node依赖；2027押题PDF生成需要Python的reportlab、pypdf，预览另需pypdfium2，并使用Windows宋体/黑体。代码验算需要支持C++17的g++，优先读取`CXX`或PATH中的`g++`；C3另支持`C3_GXX`，均保留原本机路径作为最后兼容项。

C3新PPT使用Codex随附的`@oai/artifact-tool`及Presentations技能，本次生成环境分别为`2.8.99`和`26.1020.11618`；`npm ci`不会安装这套运行库。新电脑有Codex时先通过工作区依赖工具查找本机运行库；按需设置`RUNTIME_NODE_MODULES`、`PRESENTATIONS_SKILL`、`C3_PYTHON`后运行C3专用生成器。未配置时可直接修改源稿并审阅已提交成品；不要用旧渲染器替代。单课指令与图示维护见[C3入口](../课程/课件/C3/README.md)。

改题、改课后先执行对应数值/代码检查与逐页审阅，再更新成卷/成品核对记录；不要仅为消除差异而重写SHA-256。`.gitattributes`保留已审查源稿原字节，以避免跨电脑换行转换使指纹失配。

[project_paths.py](project_paths.py)集中定义业务目录并解析[目录迁移表](目录迁移.csv)中的历史出处。已审查JSON的内容哈希和原始路径不随搬家改写；新文档和新功能直接使用当前路径。临时编译、截图和中间产物写到`_tmp/`。
