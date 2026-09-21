# fdy

日常开发工具库 —— 核心 10 个模块、78 个公开符号，`import fdy` 开箱即用。
FastAPI 与 PySide6 集成做成可选 extras，按需安装、互不干扰。

## 安装

需要 Python 3.14 及以上。

```bash
pip install fdy            # 核心：仅依赖 pydantic
pip install "fdy[http]"    # httpx 请求封装
pip install "fdy[web]"     # FastAPI 集成
pip install "fdy[gui]"     # PySide6 集成
pip install "fdy[all]"     # 以上全部
```

可选依赖缺失不影响 `import fdy`：只有导入对应子包（或调用 `http_client`）时才失败，
错误信息里直接给出该执行的安装命令，例如
`fdy 的该功能需要 PySide6，请先安装：pip install "fdy[gui]"`。

## 快速开始

```python
import fdy

fdy.snake_case("HTTPServerConfig")  # 'http_server_config'
fdy.mask("13812345678", 3, 4)  # '138****5678'
fdy.human_size(1536)  # '1.5 KB'
fdy.humanize_delta(-7200)  # '2 小时后'
fdy.deep_get({"a": {"b": [1, 2, 3]}}, "a.b.2")  # 3
list(fdy.chunk([1, 2, 3, 4, 5], 2))  # [[1, 2], [3, 4], [5]]
fdy.group_by(["a", "bb", "cc"], len)  # {1: ['a'], 2: ['bb', 'cc']}
```

统一响应模型与业务异常：

```python
from fdy import APIException, APIResponse

APIResponse.success(
    data={"id": 1}
)  # APIResponse(code=0, message='success', data={'id': 1})
APIResponse.fail(
    message="参数错误"
)  # APIResponse(code=1, message='参数错误', data=None)

raise APIException(code=1001, message="余额不足", status_code=400)
```

### PySide6（需 `fdy[gui]`）

链式配置控件 —— 不往 Qt 类型上打补丁，用包装器包住，`done()` 取回原对象：

```python
from fdy.gui import Chain

button = (
    Chain(QPushButton("确定"))
    .set(text="保存", object_name="btn_save")  # Qt 属性名，支持 snake_case
    .tooltip("Ctrl+S")
    .resize(120, 32)
    .connect("clicked", on_save)
    .done()
)
```

声明式信号槽 —— `@on` 只给方法挂标记、不产生副作用，`bind()` 才真正接线：

```python
from fdy.gui import bind, on


class Dialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.btn_ok = QPushButton("确定")
        bind(self)

    @on("clicked", sender="btn_ok")  # 省略 sender 时发送者是 self
    def _confirm(self) -> None: ...
```

表格模型 —— 用列描述消掉 `QAbstractTableModel` 的样板代码：

```python
from fdy.gui import Column, TableModel

columns = [
    Column("name", "姓名"),
    Column("balance", "余额", editable=True, formatter=lambda v: f"¥{v:,.2f}"),
]
# rows 可以是 dataclass、pydantic 模型、dict 或普通对象；key 支持 "user.name" 路径
view.setModel(TableModel(rows, columns))
```

常用对话框 —— 一行拿到结果，`destructive=True` 时默认按钮落在「取消」上：

```python
from fdy.gui import dialogs

dialogs.info("已保存")
if dialogs.confirm("删除后不可恢复，确定吗？", destructive=True):
    delete()

name = dialogs.ask_text("请输入名称", default=old_name)
if name is not None:              # None 是「放弃输入」，与「确定输入空串」含义不同
    rename(name)
```

> `title` 参数在 macOS 上不生效 —— Qt 按 Apple HIG 忽略消息框标题
> （`QMessageBox::setWindowTitle` 的 `Q_OS_MAC` 分支是空操作），Windows / Linux 正常。

配置持久化 —— 读取时用默认值兜底并决定返回类型，顺带管窗口几何：

```python
from PySide6.QtCore import QSettings
from fdy.gui import Settings

settings = Settings(QSettings("MyOrg", "MyApp"))
settings.restore_geometry("main/window", window)   # 无记录时返回 False，不动窗口
window.resize(settings.value("main/width", 1024), settings.value("main/height", 768))

settings.save_geometry("main/window", window)      # 关闭时
settings.sync()                                    # QSettings 默认延迟写入，退出前落盘
```

> 回读时会按 `default` 的类型规范化：某些后端把 bool 读成字符串，
> 直接 `bool("false")` 会得到 `True`，开关就被读反了。
>
> `restore_geometry` 返回 `True` 也不代表尺寸和保存时一致 —— Qt 会把超出屏幕
> 可用区域的几何收进去（换显示器 / 分辨率变小后防止窗口落到看不见的地方）。

## 模块一览

通用能力全部收在 `fdy.core` 下：

| 模块 | 用途 | 主要函数 |
| --- | --- | --- |
| `core.utils.strings` | 命名风格转换、清洗、脱敏 | `camel_case` `pascal_case` `snake_case` `kebab_case` `slugify` `truncate` `mask` `normalize_space` `random_string` |
| `core.utils.containers` | 嵌套结构操作与集合处理 | `deep_merge` `deep_get` `deep_set` `flatten` `chunk` `group_by` `unique` `unique_by` `pick` `omit` `invert` `first` `last` |
| `core.utils.checks` | 容错类型转换与判断 | `to_bool` `to_int` `to_float` `safe_cast` `is_empty` `is_blank` `is_iterable` `ensure_list` |
| `core.utils.ids` | ID 与随机串生成 | `uuid_str` `short_id` `token_hex` `token_urlsafe` `is_valid_uuid` |
| `core.utils.dates` | 时间解析、格式化与区间计算 | `parse_datetime` `format_datetime` `humanize_delta` `date_range` `days_between` `start_of_day` `end_of_day` `start_of_month` `now` `to_timestamp` `from_timestamp` |
| `core.utils.files` | 文件读写与路径处理 | `read_text` `write_text` `read_json` `write_json` `iter_files` `ensure_dir` `human_size` `safe_filename` `unique_path` `file_hash` |
| `core.utils.decorators` | 常用函数式装饰器 | `timer` `retry` `memoize` `silent` `singleton` |
| `core.utils.http_client` | 基于 httpx 的请求封装（需 `fdy[http]`） | `HttpClient` `get_json` `post_json` |
| `core.models.api_response` | 统一响应结构 `{code, message, data}` | `APIResponse`（`APIResponse.success` / `APIResponse.fail`） |
| `core.exceptions.api_exception` | 业务异常，携带响应码与 HTTP 状态码 | `APIException`（`code` `message` `status_code`） |

上表 10 个模块的符号全部在顶层重导出，`import fdy` 后直接 `fdy.函数名(...)` 调用；
也可以按模块导入，如 `from fdy import strings`、`from fdy import APIResponse`，
或直接走通用包的完整路径：`from fdy.core.utils.dates import date_range`。

### 分层

```
fdy
├── core    通用部分 —— 仅依赖 pydantic，零框架依赖
├── web     FastAPI 集成（需 fdy[web]）
└── gui     PySide6 集成（需 fdy[gui]）
```

`web` 与 `gui` 只**单向**依赖 `core`，core 不反向依赖它们 —— 这条边界由 `tests/test_core_isolation.py`
用静态扫描守着（core 下出现 `fastapi` / `PySide6` 之类的 import，或反向导入 `fdy.web` / `fdy.gui`，测试即失败）。
`fdy.core` 自身也是自洽入口，`from fdy.core import snake_case` 可以直接用。

可选子包**不进顶层命名空间**，需要显式导入：

| 子包 | 用途 | 主要符号 |
| --- | --- | --- |
| `web` | 把 `APIException` 转成统一 JSON 响应（需 `fdy[web]`） | `register_exception_handlers` `api_exception_handler` |
| `gui` | 控件链式配置、声明式信号槽、表格模型适配、对话框封装、配置持久化（需 `fdy[gui]`） | `Chain` `on` `bind` `unbind` `Column` `TableModel` `Settings` `dialogs` |

## 设计说明

- **core 是通用边界**：`fdy.core` 只放框架无关的实现，`fdy.web` / `fdy.gui` 单向依赖它，顶层 `fdy` 只是门面、不含实现。这样「通用部分」是可验证的，不靠约定。
- **仅一个运行时依赖**：`pydantic`（用于 `core.models`）。`http_client` 所需的 httpx 走可选依赖 `fdy[http]`，其余全部基于标准库。
- **延迟导入 httpx**：`http_client` 在函数内部经 `core._optional.require("httpx")` 导入，保证未安装 httpx 时 `import fdy` 不失败。
- **extras 分层不改变 core 契约**：顶层始终 78 个符号，`import fdy` 不加载任何可选依赖（实测 `fastapi` / `starlette` / `PySide6` / `httpx` 都不进入 `sys.modules`）。`fdy.web` / `fdy.gui` 走同一个 `core._optional.require()`，缺依赖时在导入处即刻失败并给出可直接执行的安装命令。
- **`APIResponse` 只有一对构造入口**：成功 `APIResponse.success(...)`、失败 `APIResponse.fail(...)`，两者均为 keyword-only，`code` / `message` / `data` 都可覆盖。不额外提供模块级 `success` / `fail` 函数，免得把这类通用名注入调用方命名空间。
- **`dialogs` 的函数不重导出到 `fdy.gui` 包级**：`fdy.gui.error` / `fdy.gui.info` 会和日志语义撞车，调用方写 `dialogs.confirm(...)` 更清楚。这与 `chain` 只有类、没有同名函数是同一条原则。
- **配置持久化只包一层，不改存储格式**：`Settings` 就是 QSettings 的薄封装（另有 `.store` 逃逸口），值仍以 QSettings 原生格式落盘，不会变成不可读的私有格式。
- **`code` / `message` 是必填字段**：默认值只由 `success` / `fail` 提供，直接 `APIResponse(...)` 构造时必须显式传入。
- **默认文案不外泄**：`success` / `fail` 的默认文案写死在签名里，不作模块常量导出 —— 措辞随时可改，导出即成为契约。
- **`APIResponse.data` 的类型校验需显式参数化**：Python 泛型在运行期拿不到 `T`，`APIResponse.success(data=...)` 不会校验 `data`（JSON schema 里 `data` 为 `Any`）；要强校验应写 `APIResponse[Foo](...)` 或 `APIResponse[Foo].success(data=...)`，FastAPI 场景由 `response_model=APIResponse[Foo]` 兜住。
- **Python 3.14+**：依赖 3.14 的三项语言特性 —— PEP 695（`class APIResponse[T]`、`def chunk[T](...)` 泛型语法）、PEP 649（注解延迟求值）、PEP 758（`except A, B:` 可省略括号）。
- **不 monkey-patch Qt 类型**：`Chain` 是独立包装器，不往 `QPushButton` 之类上塞方法，宿主项目的 Qt 命名空间保持干净；`chain` 只有类、没有同名函数，避免「模块名与函数名撞车」时 `fdy.gui.chain` 指向谁取决于导入方式。
- **`@on` 不在装饰时产生副作用**：只给函数挂标记，连接统一由 `bind(obj)` 完成，接线时机由调用方掌握（测试里也就能手工控制）。
- **PySide6 下限 6.10**：那是首个支持 Python 3.14 的版本（6.9 及以下没有可用的 cp314 wheel），不可下调。
- **GUI 测试走无头平台**：`tests/conftest.py` 默认设置 `QT_QPA_PLATFORM=offscreen`，并复用会话级 `QApplication`（Qt 只允许进程内存在一个实例）；未装 PySide6 时相关测试整体跳过，不影响 core。
- **模块命名避开标准库**：用 `containers` / `checks` / `dates`，避免与 `collections` / `types` / `datetime` 混淆。
- `chunk` 返回生成器，按需迭代；需要列表时用 `list(...)` 包裹。

## 开发

```bash
uv sync                                # 安装依赖（含 dev 组）
uv sync --extra web --extra gui        # 需要跑 web / gui 测试时补齐 extras
uv run pytest                          # 运行测试
uv run ruff check src tests            # 静态检查
uv run ruff format --check src tests   # 格式检查，只校验不改文件
uv run ruff format src tests           # 自动重排格式
```

## License

MIT
