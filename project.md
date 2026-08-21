# 英语词汇学习：间隔复习工具

英语词汇学习是一个无后端、可离线运行的英语词汇学习工具。它将单词资料和学习进度保存在浏览器 IndexedDB 中，按到期时间生成每日会话，并支持键盘操作、浏览器美式英语发音、CSV 词库导入以及完整进度备份。

## 主要文件

| 文件 | 用途 |
| --- | --- |
| `vocab_coach.html` | 完整的单文件学习应用 |
| `us_core_7000_authentic.csv` | 20,000 词正式数据文件；历史文件名为兼容旧版一键更新而保留 |
| `启动英语词汇学习.command` | macOS 双击启动入口 |
| `启动英语词汇学习.bat` | Windows 双击启动入口 |
| `更新英语词汇学习.command` | macOS 一键拉取最新版 |
| `更新英语词汇学习.bat` | Windows 一键拉取最新版 |
| `update_vocab.py` | 兼容 Git 克隆与 ZIP 下载版本的安全更新核心 |
| `start_vocab.py` | 自动启动本地服务器并打开浏览器 |
| `build_authentic_7000.py` | 从 ECDICT 重新构建可信核心词库 |
| `apply_cefr_levels.py` | 从 American Oxford 3000/5000 PDF 添加 CEFR 学习难度 |
| `enrich_wiktionary_etymology.py` | 流式筛选 Wiktextract 数据并补充中间英文词源 |
| `enrich_chinese_word_formation.py` | 用 engra 结构关系和 Wiktionary 来源生成中文构词短注 |
| `enrich_tatoeba_examples.py` | 从 Tatoeba 校对语料补充可溯源双语例句 |
| `audit_vocabulary.py` | 检查 CSV 结构、覆盖率、重复词和模板化伪数据 |

## 启动

macOS 直接双击 `启动英语词汇学习.command`，Windows 直接双击 `启动英语词汇学习.bat`。也可以在终端运行：

```bash
python3 start_vocab.py
```

启动器会自动选择可用端口并打开浏览器，按回车键或 `Ctrl+C` 停止。

通过 HTTP 打开时，应用会在首次使用时自动读取同目录的 `us_core_7000_authentic.csv`。旧版 7,000 词用户会自动迁移到 20,000 词：已有卡片只更新词典元数据，调度状态保持不变，再追加 13,000 张新卡。直接双击 HTML 也可以运行，但部分浏览器会阻止页面读取相邻文件，此时点击“导入词库”并手动选择 CSV。

## 学习流程

1. 应用先选取已经到期的复习卡，再补充当天允许数量的新卡。
2. 卡片正面显示单词、音标和 Oxford 难度参考。可以直接评级，也可以先翻面核对答案。
3. 四种评级同时影响本轮队列和跨天到期时间：

| 评级 | 本轮行为 | 下次间隔 |
| --- | --- | --- |
| 重来 | 插入当前队列靠前位置 | 进入学习状态，10 分钟后到期 |
| 困难 | 首次评级时在本轮较后位置再出现一次 | 当前间隔约 1.2 倍 |
| 记得 | 本轮完成 | 当前间隔乘以难度系数；新卡为 1 天 |
| 熟练 | 本轮完成 | 在“记得”基础上再延长；新卡为 4 天 |

这是一套透明的 SM-2 风格间隔调度器，不冒充完整 FSRS。每张卡保存 `state`、`due`、`interval`、`ease`、`reps`、`lapses` 与 `lastReviewed`。

## Placement Test 与分级学习

点击“词汇定级”可以完成 18 道自适应词义题。测试从 B1 难度开始，答对后提高下一题难度，答错或选择“不知道”后降低难度。能力值使用逐题更新的 logistic 概率模型，不用固定正确率直接套级别。

每道题作答后，能力值、答题数、正确数、“不知道”数和已用词都会立即写入 IndexedDB。测试中退出或关闭页面后，侧栏会显示已完成题数，下次可继续；第 18 题完成时结果会自动保存，不依赖额外确认按钮。设置和定级弹窗均有可见关闭按钮，测试页另有“退出测试（自动保存进度）”。

分级依据为 Oxford University Press 官方提供的 American Oxford 3000/5000 CEFR 列表：

- Oxford 3000：A1-B2；
- Oxford 5000 新增词：B2-C1；
- 不在两份表中的高频词标为 `Beyond C1`，而不是没有依据地标成 C2。

测试结果是词义识别能力估算，不是正式 CEFR 认证。正式 placement test 通常还会测试阅读、听力、语法和语言运用。

完成测试后，每天的新词约 75% 来自测得级别，25% 来自高一级。例如 B1 学习范围为 B1 和 B2。此前已经学过的词无论级别如何，仍会按到期时间复习。

## 快捷键

| 按键 | 操作 |
| --- | --- |
| `Space` | 翻面 |
| `1` | 重来 |
| `2` | 困难 |
| `3` | 记得 |
| `4` | 熟练 |
| `S` | 朗读单词 |
| `D` | 朗读例句 |

## 数据存储

- 词库和逐卡学习记录存放在 IndexedDB 数据库 `vocab_coach_db`。
- 每日统计以本地日期为键保存，用于当天计数和连续学习天数。
- 主题偏好单独保存在 LocalStorage。
- “备份进度”导出 schema v3 JSON，其中包含完整词库、逐卡调度状态、设置、每日统计、定级结果和未完成测试。
- 新版备份带 SHA-256 完整性值；导入前先完整校验所有卡片和调度字段，再用单个 IndexedDB 事务替换旧数据，失败不会留下半恢复状态。
- 仍兼容没有完整性字段的 schema v2 旧备份。导入 JSON 可以恢复到另一台设备或另一个浏览器。

使用 IndexedDB 是必要的。将 20,000 条完整词条连同调度状态写入 LocalStorage 会超过常见容量限制，也不适合频繁的逐卡更新。

## CSV 格式

文件使用 UTF-8 with BOM，标准表头如下：

```csv
word,base_word,phonetic,pos,meaning,level,collocation,etymology,etymology_source,etymology_license,example_en,example_zh,example_source,example_license
```

应用的解析器支持 RFC 4180 常用格式，包括：

- 双引号字段；
- 字段内逗号；
- 字段内换行；
- 以两个双引号表示一个字面双引号；
- Windows 与 Unix 换行符；
- UTF-8 BOM。

导入时按不区分大小写的 `word` 去重。资料缺失不会被模板文字自动填满，卡片会明确显示“待可信来源补充”。

`base_word` 用于让 `supposed`、`works` 等词形继承基础词的级别；`level` 可以是 `A1`、`A2`、`B1`、`B2`、`C1` 或 `Beyond C1`。

## 词库质量策略

默认词库的词频、音标、词性和中文释义来自开源 ECDICT。构建器按 `frq` 当代语料频率顺序选出 20,000 个合法英文词条。只有词典释义明确写出 `vt.` 或 `vi.` 时才保留及物性标记；没有依据时只标为 `v.`，不会猜测。

构词短注优先使用 MIT 许可的 engra 结构化词根关系，生成 `reform / re-form；re-：重新、再次；form：形式、组成；reform：改革、改正。` 这类中文记忆说明。没有可靠拆解时，只把 Wiktionary 中能明确识别的来源语言压缩成中文短句；无法确定就留空，不猜词根。

双语例句来自 Tatoeba 的英中句对，经 ManyThings 筛选为母语者或已校对内容。构建器只接受目标词的完整单词匹配，优先选择简体、长度适中的句子，并过滤不适合通用学习卡片的敏感内容。每个非空例句保存 Tatoeba 原句页面和 `CC BY 2.0 FR` 许可证。ECDICT 不稳定提供搭配，因此搭配仍保持为空。

重新构建：

```bash
python3 build_authentic_7000.py
python3 apply_cefr_levels.py
python3 enrich_wiktionary_etymology.py
python3 enrich_chinese_word_formation.py
python3 enrich_tatoeba_examples.py
```

若需要保留另一个 CSV 的词序，可显式传入：

```bash
python3 build_authentic_7000.py --input my_word_list.csv --output my_authentic_deck.csv
```

## 数据审计

运行：

```bash
python3 audit_vocabulary.py us_core_7000_authentic.csv
```

审计内容包括：

- 学习字段、`base_word`、`level`、构词与例句来源及许可证；
- 空单词与重复单词；
- 每个字段的有效覆盖率；
- 音标是否只是原词加斜杠；
- `use word`、通用词源、模板例句等伪数据模式。

当前默认词库的构建结果：

- 20,000 行，无重复词；
- 中文释义覆盖率 100%；
- 音标覆盖率约 95.0%；
- 词性覆盖率约 77.4%；
- 6,235 个词直接或通过基础词匹配 Oxford A1-C1；
- 中文构词或来源短注覆盖 13,677 个词，约 68.4%；
- 可溯源 Tatoeba 双语例句覆盖 4,831 个词，约 24.2%；
- 所有非空构词和例句均附来源页面与许可证；
- 未填充任何模板化搭配或程序生成例句。

## 浏览器兼容性

目标为最新版 Chrome、Edge 和 Safari。应用依赖：

- IndexedDB；
- Web Speech API；
- `<dialog>`；
- `structuredClone`；
- CSS `color-mix()`。

语音质量由操作系统安装的英文语音决定。页面优先选择 `en-US`，没有时回退到其他英语语音。

## 验证

开发完成后执行了以下检查：

```bash
node -e "/* 提取并编译 HTML 内联脚本 */"
python3 -m py_compile build_authentic_7000.py apply_cefr_levels.py enrich_wiktionary_etymology.py enrich_chinese_word_formation.py enrich_tatoeba_examples.py audit_vocabulary.py
python3 audit_vocabulary.py us_core_7000_authentic.csv
```

并使用真实 Chromium 浏览器验证了：测试逐题存盘、退出续测、结果自动保存、页面刷新、Python 服务停止后同端口重启、可视化关闭、桌面卡片与评级区布局、20,000 卡备份下载、SHA-256 校验、篡改拒绝及事务式恢复。

## 后续开发建议

1. 继续补充授权清晰的搭配语料，并按来源字段记录许可证和出处。
2. 若要采用 FSRS，应引入官方 `fsrs.js`，同时设计旧调度数据迁移，而不是复制不完整公式。
3. 增加词条编辑器，让用户人工补充搭配、词源与例句，并区分“词典数据”和“个人笔记”。
4. 增加可选的学习历史图表，但不应让统计信息压过当天复习任务。
