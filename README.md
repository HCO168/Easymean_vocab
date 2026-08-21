# Easymean_vocab｜英语词汇学习

一个无需后端的英语词汇间隔复习工具，内置 7000 词英汉词库、CEFR 难度参考、自适应词汇定级、每日复习队列、发音、进度备份和深色模式。

## 启动

- Windows：双击 `启动英语词汇学习.bat`
- macOS：双击 `启动英语词汇学习.command`
- 其他平台：运行 `python3 start_vocab.py`

启动器会在本机开启 HTTP 服务并自动打开浏览器。按回车键或 `Ctrl+C` 停止服务。Python 建议使用 3.9 或更高版本，无需安装第三方依赖。

## 更新

使用 `git clone` 获取项目后：

- Windows：双击 `更新英语词汇学习.bat`
- macOS：双击 `更新英语词汇学习.command`

更新脚本只执行安全的 Git 快进更新，不会清除浏览器中的学习进度。通过 GitHub 下载 ZIP 的副本不包含 Git 信息，不能使用一键更新脚本。

## 数据与隐私

词库与学习记录保存在浏览器 IndexedDB 中，不会上传到服务器。“备份进度”可导出包含完整学习状态的 JSON 文件。

默认词库基于 [ECDICT](https://github.com/skywind3000/ECDICT) 的频率、音标、词性和英汉释义构建，难度参考来自 [Oxford 3000/5000 CEFR wordlists](https://www.oxfordlearnersdictionaries.com/us/wordlists/oxford3000-5000)。定级结果只用于安排学习范围，不是正式 CEFR 认证。

完整设计、数据管道和验证说明见 [`project.md`](project.md)。
