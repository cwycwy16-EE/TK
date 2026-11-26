# 逐图验收

对照原图、批准译稿和模型实际成品。先核实照片身份、Logo、材质和结构；逐个检查尺寸、数字、箭头和编号所指的位置，再看大小层级、颜色、平衡、行距、裁切和手机可读性。逐字复读非英语声调及组合字符。用 scripts/ocr.cjs 和本地语言包辅助检查；OCR 错认时保留记录并放大实图判断。严禁以提示词或 OCR 单方面断言成品正确。

返工继续用内置 image_gen，改正具体错误，验收其他区域有无新变化。OCR、尺寸和哈希检查、无损导出、来源记录可用代码。只有实际逐图核对通过的输出进入交付目录。翻译与质检报告分别记录源文与语义回核、最终可见文字与图像检查、返工和待核项。

image-provenance.json 为每图写 output_file、method、source_images、actual_tools、requested_model、actual_model、model_evidence、generation_record、appearance_review、limitations。直接编辑成品用 image_gen_edit；额外复合原产品素材则用 template_composite 并追溯模型输出、实际步骤。生成记录使用真实输出标识或提示、时间、路径。版本无可靠证据时 actual_model 为 null。
