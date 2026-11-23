# 提示词与验收规范

## 独立图片提示词

每个任务使用明确本地参考路径。输入标签区分原始编辑目标和辅助实物参考。

```text
任务：只替换原图文字，目标语言<Thai / Vietnamese / English only>。
商品不变量：<本图实际颜色、Logo、纹理、五金、肩带、挂件等>。
逐项原文→目标文本：<完整对应表>。
排版：<按区域分配独立文字块>；大字、清晰对比、留足边距。
两行文案逐行编号说明，但不得将编号或分隔符画进图里。
必须完整渲染所有文本块，不可省略第二行；不可自动改写翻译。
保留：<数字/单位/尺寸箭头/照片和SKU顺序>。
禁止：新增商品角度、隔层、容量、配件，改变Logo或色号。
```

参数页优先分行表格；SKU名称用换行处理，不缩成小字。字重和视觉层级在同国同商品中保持一致，避免每张任意切换字体/描边/装饰。文字不压住Logo、拉链、挂件或关键结构。PH用“English only, no Tagalog”；VN保留完整变音符号；TH核对上下标元音和声调。不要用斜杠暗示换行，模型可能把斜杠画出来。

## 验收表

- text_review：逐个文本块和锁定文案比对，漏行、混语、乱码、错误声调和数字均失败；适配性的标点变化可记录后接受。
- layout_review：手机可读、大字、对齐、留白、边缘安全，无遮挡，无文字截断。
- appearance_review：与原图逐张比对颜色、轮廓、纹路、刺绣/Logo、肩带连接、五金和挂件的形状/细节。不得只看主色相近就通过。
- fact_review：SKU顺序/数量/有无挂件正确，尺寸箭头语义正确，不新增证据外主张。
- 主智能体最终重点复核参数/颜色页和返工图；每张仍必须由负责国家的智能体完成上述全部审阅。无法确认记needs_review，不能写passed。

## 磁盘状态与来源

每条国家状态记录：scope_version、expected、passed、reused、retrying、blocked、active_image_id；每张保存image_id、attempt、state、source_hash、output_hash、review结果。实际调用失败也记录，不能虚构调用ID。

每个最终输出的provenance至少包括：

```json
{
  "output_file": "绝对路径",
  "method": "image_gen_edit",
  "source_images": ["原始商品参考路径"],
  "actual_tools": ["image_gen.imagegen", "Copy-Item: copy only"],
  "requested_model": "用户原始请求或未指定",
  "actual_model": null,
  "model_evidence": "接口未提供可核验版本",
  "generation_record": {
    "prompt": "实际完整提示词",
    "time": "实际记录的ISO时间含时区",
    "output_path": "工具实际返回路径",
    "call_id": null
  },
  "appearance_review": {"status": "passed", "notes": "本图实际比对结论"},
  "text_review": {"status": "passed", "notes": "逐文字块结论"},
  "layout_review": {"status": "passed", "notes": "本图排版结论"},
  "limitations": [],
  "scope_version": 1,
  "sha256": "实际文件哈希"
}
```

模板为字段示例，不可直接照抄passed。source_reuse记录实际复制步骤，generation_record为null，actual_model为null；不得把复用说成AI生成。当前生图本地化流程不接受模板合成替代；仅用户明确改变制作方法才新建范围并按实际方法记录。没有模型版本证据不得填2/2.5。除任务记录外不写用户长期记忆。

每张的日志及provenance在当次完成后立即写入磁盘，包含原图路径/哈希、完整实际提示词、工具返回路径、调用时间（未知须说明）、生成原件路径、最后成品哈希和四类审核。只存prompt.txt但不关联输出，或仅state计数，不构成完整来源。源稿包含先前模型编辑时保留其provenance引用。

恢复前核对实际文件与记录，检查最新scope_version及源图哈希；子智能体上下文丢失时以磁盘为准。缺日志不得编造，无法恢复的条目标needs_review并说明，不自动通过。首次失败后针对性重试仍使用原始中文参考，提示词保留完整锁定译文，不因重试简化而丢失色名、参数或限制。
