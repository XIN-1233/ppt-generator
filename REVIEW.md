# Code Review — PPT Generator

**Reviewed**: 2026-06-01 | **Score**: 7.5/10 — 项目结构不错，有几个值得修的地方

---

## 一、值得夸的（别动）

- **Prompt 工程是亮点**。McKinsey 角色扮演 + 深度节奏 + 标题即论点，这套 prompt 设计质量很高
- **JSON 解析 4 层兜底**。直接解析 → 代码块提取 → 尾逗号修复 → 括号匹配。AI 最常犯的 JSON 错误全防了
- **主题系统清晰**。8 套配色 + 中英文字体映射，数据驱动，加新主题一行代码
- **前端 UX 用心**。状态轮播、loading 态、错误提示、下载触发器，体验完整
- **全内存 pipeline**。不写临时文件，直接流式返回，架构干净

---

## 二、现在就该修的

### 1. `requirements.txt` 版本过老 🔴

```diff
- anthropic==0.39.0
+ anthropic>=0.39.0
```

你 pip 实际装了 `0.105.2`，钉死旧版本会误导别人（或未来的你）。把所有 `==` 改成 `>=`。

### 2. 没检验 API key 是否存在 🔴

`ai_service.py` 直接创建 client，如果 `.env` 没配 key，等到调 API 才报错——前端看到一个 500 超时。加上：

```python
# ai_service.py, after client = ...
if not settings.anthropic_api_key:
    raise RuntimeError(
        "ANTHROPIC_AUTH_TOKEN not set. Create a .env file (see .env.example)"
    )
```

### 3. `_font()` 静默丢弃非白名单字体 🟡

`ppt_generator.py:678` — 只有 `Calibri`、`Arial`、`Microsoft YaHei` 三个字体名会被设置。其他字体名（比如用户自定义的）被静默跳过，不报错但字体不对。

```python
# 现在：白名单以外不设置
if font_name in ("Calibri", "Arial", "Microsoft YaHei"):
    ...

# 改：先尝试设置，失败再用系统默认
try:
    r.font.name = font_name
except Exception:
    pass
```

### 4. `validate_slide_structure` 太宽容 🟡

AI 返回空 slides、缺少字段、数量不对——全都静默修补，不告诉你出问题了。这让你看不出 prompt 质量下降。

加一行 logging：
```python
if len(slides) > expected_count + 2:
    print(f"WARNING: AI returned {len(slides)} slides, trimming to {expected_count}")
```

### 5. `brightness` 已弃用 🟢

`ppt_generator.py:529` — `card.fill.fore_color.brightness = 0.3` 在新版 python-pptx 里已弃用。改成用 alpha / transparency 或者直接用一个更浅的硬编码颜色。

---

## 三、可以更好（不急，有空再搞）

### 6. 异步用得对，但可以更简单

`app.py:124-133` — 用 `asyncio.get_running_loop().run_in_executor()` 包装同步调用，正确。但 FastAPI 的 `def`（非 `async def`）路由自动进线程池，效果一样。两种写法都可以，当前写法没问题。

### 7. 项目缺少 logging

全是 `print()` 和 `traceback.format_exc()`。换成 `logging` 模块，加 `INFO`/`ERROR` 级别区分。以后 debug 容易很多。

### 8. 图表数据标签在中文下可能乱码

`_style_chart()` 的 data labels 没有显式设置中文字体。如果图表里有中文，标签可能显示为方块。加一行 `plot.data_labels.font.name = 'Microsoft YaHei'` 当 language 是 chinese/bilingual。

### 9. 前端 `var` 声明

`main.js` 全用 `var`。改成 `const`/`let`，ES6+ 惯例。

### 10. 没有 health check 超时保护

`/health` 端点不调用 AI，很安全。但 `/api/generate` 没有请求大小限制，没有速率限制。单用户没事，多用户时需要。

---

## 总结

| 优先级 | 数量 | 影响 |
|--------|------|------|
| 🔴 马上修 | 2 个 | 版本锁死 + 缺 API key 报错不友好 |
| 🟡 建议修 | 3 个 | 字体静默失败 + 验证太宽容 + API 已弃用 |
| 🟢 有空修 | 4 个 | logging、中文图表、ES6、速率限制 |

**结论**：项目骨架很好，prompt 设计是亮点。先把 🔴 两个修了，其他有空再搞。
