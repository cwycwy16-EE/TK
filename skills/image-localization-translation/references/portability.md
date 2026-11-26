# 新设备安装与核验

将 ZIP 解压，把完整的 image-localization-translation 文件夹放进当前设备的 Codex 用户技能目录。若设置了 CODEX_HOME，路径为其下的 skills；默认是用户主目录下的 .codex/skills。确认 SKILL.md 直接位于 image-localization-translation 下，避免解压出双层同名目录。若已有自定义版本，先另存旧版。打开新的 Codex 对话，输入“用 $image-localization-translation 处理我上传的图片”。

**迁移内容只有规则和工具。** 使用者提供本次商品原图。包内没有示例图、字体模板、以往客户图、历史聊天或绑定设备的素材目录。配置好技能后，先让 Codex 检查当前会话能否实际调用内置 image_gen 编辑输入图片。安装包不能授予账号权限或开通额度。

## 本地检查工具

以下命令从解压后的技能目录运行；Python 命令随环境选用 python、python3 或 py。可优先复用当前 Codex 运行时。像素检查依赖 Python 3 和 Pillow。若设备缺少依赖，可在独立 Python 环境里执行：

```sh
python -m pip install Pillow
python scripts/check_install.py
```

该自检检查技能文件、相对链接及透明像素保护。实际生产时先将图像模型输出与源图明确对齐；检查宽高、关键位置及蒙版，不能只拉伸到相同尺寸。蒙版按解码后的正向原图坐标准备：黑色保护，白色允许变化，须为纯二值灰度图。命令中的文件由本次任务提供，输出目录应先创建：

```sh
python scripts/protect_pixels.py source.png model-edit.png reviewed-mask.png localized.png
```

最终复核商品和整页背景。该命令只验证黑色区域；白色范围是否伤及商品或装饰仍需与本张原图逐处比对。生成中的拼写错误回到内置图像编辑返工。

## 可选本地 OCR

有可用本地 OCR 时优先复用。随包脚本使用 Node.js、tesseract.js、sharp 和本地训练数据。可在技能目录执行 npm install 安装 package.json 中列出的版本，选择符合 sharp 安装要求的 Node.js 版本。安装依赖需要网络，识别图片在本地执行。按本次图片语言传入 chi_sim、vie 或 eng；以越南语为例：

```sh
node scripts/ocr.cjs localized.png vie node_modules/@tesseract.js-data/vie/4.0.0_best_int
```

已下载语言包时可直接传入含对应 .traineddata.gz 的本地目录。缺少 OCR 时记录缺项，放大逐字复读；不把视觉检查记作 OCR 通过。没有可用的像素核验工具时不能声称背景零差异。

## 新设备首单

上传用户本次提供的一张实际原图，指定一个市场或采用默认双市场。按入口流程调用模型，把每个结果与其对应原图并排检查，保留模型实际输出记录、保护区差分与最终 PNG。自检成功只覆盖本地文件和工具；目标设备完成这一步才能记录该设备生图实测通过。

