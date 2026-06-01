# RBTray - Python 版本

这是 RBTray 的 Python 移植版本，功能与上级目录的 C++ 版本保持一致：把窗口
最小化到 Windows 系统托盘，并支持用快捷键快速激活常用程序。

## 功能

### 全局快捷键

| 快捷键   | 功能                                    |
| -------- | --------------------------------------- |
| `Alt+F1` | 把当前前台窗口最小化到系统托盘          |
| `Alt+F2` | 从托盘激活/恢复 Chrome (chrome.exe)     |
| `Alt+F3` | 从托盘激活/恢复 Cursor (cursor.exe)     |
| `Alt+F5` | 从托盘激活/恢复 远程桌面 (mstsc.exe)    |
| `Alt+F6` | 从托盘激活/恢复 Windows Terminal        |
| `Alt+F7` | 从托盘激活/恢复 Android Studio          |
| `Alt+F8` | 从托盘激活/恢复 抖音 (douyin.exe)       |
| `Alt+F9` | 从托盘激活/恢复 Xshell (Xshell.exe)     |

> 注意：`Alt+F2~F9` 只能恢复**已经被最小化到托盘**的对应程序窗口。

### 托盘图标操作

- **左键单击**：恢复对应窗口
- **右键单击**：弹出菜单
  - Restore Window —— 恢复窗口
  - Close Window —— 关闭窗口
  - About RBTray —— 关于
  - Exit RBTray —— 退出本程序

## 安装依赖

```powershell
pip install -r requirements.txt
```

或者直接：

```powershell
pip install pywin32
```

## 运行

```powershell
python rbtray.py
```

退出已运行的实例：

```powershell
python rbtray.py --exit
```

如果不想出现命令行黑框，可以用 `pythonw.exe` 启动，或双击 `start.vbs`。

## 打包成 exe（可选）

```powershell
pip install pyinstaller
pyinstaller --noconsole --onefile --name RBTray rbtray.py
```

生成的 `dist\RBTray.exe` 即为单文件可执行程序。若想开机自启，把它的快捷方式
放到启动目录（`Win+R` 输入 `shell:Startup`）。

## 与 C++ 版本的差异

- 关于对话框用 `MessageBox` 实现（C++ 版本是一个对话框资源），内容等价。
- 进程激活逻辑、托盘逻辑、热键完全一致。
- 不包含鼠标钩子（C++ 原版的 RBHook.dll 功能），即不支持"右键最小化按钮"
  这种方式，仅通过热键最小化，这与当前 C++ 分支的实际行为一致。

## 自定义快捷键 / 程序

打开 `rbtray.py`，修改顶部的 `HOTKEYS` 配置表即可。每一项格式为：

```python
(热键ID, 修饰键, 虚拟键, "进程名.exe" 或 None)
```

`None` 表示该热键执行"最小化当前窗口"动作；填进程名则表示"从托盘激活该程序"。
