# 工具

从项目根目录运行。Python环境需要reportlab、pypdf、pypdfium2、PyMuPDF、Pillow、PyYAML、python-pptx；Node依赖见本目录package.json和lockfile。

| 用途 | 入口 |
|---|---|
| 题库查询/导出/导入 | `python tools/题库/tiku.py` |
| 六套模拟卷交付核验 | `python tools/verify_exam_delivery.py` |
| 六套卷蓝图一致性核对 | `python tools/exam_blueprint.py` |
| 旧设计种子验算（当前部分输入绑定已失效） | `verify_exam_seeds.py`；保留作历史核验来源，不自动重绑定 |
| 六套卷成品及MD生成 | `build_exam_papers.py`、`build_exam_answers.py`及配图脚本 |
| 登记新路径下的交付清单，不生成ZIP | `python tools/package_exam_delivery.py` |
| 去年三套押题答案生成 | `python tools/build_prediction_answers.py 一`（或二、三） |
| 押题答案算法功能验证 | `python tools/verify_prediction_algorithms.py` |
| 押题答案逐页渲染与边界检查 | `python tools/verify_prediction_layout.py 一`（或二、三） |
| 去年机构三套模拟答案生成 | `python tools/build_institution_mock_answers.py 一`（或二、三） |
| 模拟答案指纹、版面与六道C算法验算 | `python tools/verify_institution_mock_answers.py --render --algorithms`；算法验算需要GCC |
| 通用PPT生成 | `render-pptx.js`；内容规范见[CONTENT-SPEC.md](CONTENT-SPEC.md) |
| C2-B-pro旧构建来源和只读结构检查 | [c2b](c2b/)，先读[当前文件依据](../课程/课件/C2/C2-B-pro/当前文件依据.md) |
| 主讲视频转写 | `transcribe.py` |

`check.js`会调用渲染器覆盖PPT，不用于随意检查封存或手工修改课件。C2-B的旧构建检查结果不能替代当前手改成品和WPS实际放映。

[project_paths.py](project_paths.py)集中定义业务目录并解析[目录迁移表](目录迁移.csv)中的历史出处。已审查JSON的内容哈希和原始路径不随搬家改写；新文档和新功能直接使用当前路径。临时编译、截图和中间产物写到`_tmp/`。
