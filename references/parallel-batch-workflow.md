# 批次协调与恢复

用于长项目的并行写入、多阶段交接和中断恢复。串行小修订复用已有记录即可；串行各批可顺序修改同一主文件，不必强拆章节或创建这套协调台账。实质审校顺序以 [主入口](../SKILL.md#每批译写与审校) 为准。

## 分批和写入责任

选择一次能完整源文核对与审校的范围，通常数页或一节；密集证明、图式和 OCR 页缩小，跨页单元记录接续。覆盖台账按源页及逻辑单元闭合，协调台账管理谁在写什么，两者不能互相代替。

并行写入时每个实际目标文件只由一人写，公共术语/覆盖/图形台账由协调者合并。单文件工程可并行只读审阅、私有修订建议，再由一人应用；不为了并行擅改工程组织。章节是合并单位，不是强制的工作量大小。

## 领取与完成

下述路径在 skill 根目录表示；在项目中执行时使用脚本实际路径。初始化一次，领取时指定批次身份、源页、phase 和目标文件：

```bash
python3 scripts/batch_checkpoint.py PROJECT/batch-checkpoints.tsv --init
python3 scripts/batch_checkpoint.py PROJECT/batch-checkpoints.tsv --claim \
  --project-dir PROJECT --batch-id ch06-s08-translation \
  --source-start 324 --source-end 327 --source-id chapter-06 \
  --phase translation --owner worker-1 --file chapters/ch06/section-08.tex
python3 scripts/batch_checkpoint.py PROJECT/batch-checkpoints.tsv --complete \
  --project-dir PROJECT --batch-id ch06-s08-translation --status drafted \
  --notes "audits/ch06-s08.md: 初译已核；图页尚待检查"
```

同 phase 重叠源范围不重复领取，跨 phase 也不能并发写同一文件。可用 phase 为 `translation`、`mathematics`、`terminology`、`language`、`layout`、`review`；默认完整每批流程可在一个 translation 任务内完成，不要求拆成六个代理任务。

- 全部适用检查已有证据，直接 `--complete --status verified`。
- 暂缺检查，记 `drafted`。后续检查**没有改动输出**时，用 `--promote --batch-id ID --notes "核验证据位置与结果"` 提升，脚本核原草稿哈希未变。
- 后续检查**修改了输出**时，领取不同 ID 的 review phase（例如 `ch06-s08-review`），完成后记录新哈希；不要用 promote 刷新旧草稿。需要继续复审已完成 review 时可用有原因的命名轮次 `--phase review:r2 --notes "新增修订及复审原因"`，保持每轮 ID 唯一。
- 真正阻塞时，`--complete --status blocked --notes "具体原因"`。继续先处理原因，再同 ID 用 `--claim --retry`；源 ID、phase、页范围和文件集合须不变，notes 写重试原因。每次保留历史，不凭固定重试次数判断是否解决，也不盲目重复相同失败。

后续 review 可审校并修改原目标，但只在旧写入已结束后开始。各阶段/轮次有独立批次 ID，同一 ID 不重新定义成不同 phase 或范围。

## 合入与验收

协调者先读私有报告及差异，核数学/术语，再完成中文句群审校与改动后的数学保护复核，最后对最终改动编译并看受影响图页及相邻分页。公共台账按源顺序合并；章节合并再查跨批术语、中文承接、引用和数学。不把中文改句放在最后一次编译之后并直接标 verified。

局部编译使用能够代表实际依赖的最小入口；若不能表示跨批引用或图，扩大到章节/全书。固定轮数不是稳定证明，最终正文、索引与目录按工程情况继续构建。用户明确只要 TeX 时，PDF 类检查按主入口记为不适用，不把未执行检查写成通过。

```bash
# 工作中：记录/文件/哈希及冲突检查，允许尚未结束的批次
python3 scripts/batch_checkpoint.py PROJECT/batch-checkpoints.tsv \
  --check --project-dir PROJECT
# 合并验收/发布：所有批次已结束，实际最终输出责任均 verified
python3 scripts/batch_checkpoint.py PROJECT/batch-checkpoints.tsv \
  --check --project-dir PROJECT --require-complete --require-verified
```

新版完成记录在原 `output_sha256` 列保存每文件 JSON 哈希；新版也能核旧聚合 SHA-256，旧工具不能读取新编码。每个文件的哈希责任只能由**更晚的完成记录**接管，active claim 不能遮蔽旧哈希。新编码被部分接管时仍检查未接管文件；旧聚合被部分接管且有变化时，须由后续完成记录覆盖全部旧目标，不能跳过整组检查。

严格 verified 检查允许旧 drafted 被后续最终 verified 输出完整接管，并列出接管批次；更晚的 drafted 仍会阻止发布。工具检查记录、文件与状态，不验证 notes 中的实质证据，也不证明全书页覆盖、中文审读或数学正确；对应报告和覆盖台账仍须实际完成。

## 失败与恢复

重试前区分来源缺失、环境能力、局部 TeX 错误、写入冲突和共享台账冲突。修当前原因；已经完成的译文不得因工具失败重新派给第二个写者。共享状态冲突先停止并发写入，交由一个协调者恢复。

恢复读取最新用户纠偏、源快照与检查点：已核页/单元、完成维度、目标文件与哈希、保护约定、未解问题和下一步。过时的“已编译”不继承为“已审计”。耗时估算依据真实批次测量；保留部分完成证据，继续未完成维度。
