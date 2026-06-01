# -*- coding: utf-8 -*-
# ****************************************************************************
#
# RBTray (Python 版本)
# 原始版权所有 (C) 1998-2010  Nikolay Redko, J.D. Purcell
# 原始版权所有 (C) 2015 Benbuck Nason
#
# 本程序是自由软件;你可以根据自由软件基金会发布的
# GNU 通用公共许可证(GPL)的条款(许可证的第 2 版,
# 或者(由你选择)任何更高的版本)重新分发和/或修改本程序。
#
# 发布本程序的目的是希望它有用,但不提供任何担保。
#
# ****************************************************************************
#
# 这是 RBTray 的 Python 移植版本,功能与 C++ 版本保持一致:
#   - Alt+F1 : 把当前前台窗口最小化到系统托盘
#   - Alt+F2 : 从托盘激活/恢复 chrome.exe
#   - Alt+F3 : 从托盘激活/恢复 cursor.exe
#   - Alt+F5 : 从托盘激活/恢复 mstsc.exe (远程桌面)
#   - Alt+F6 : 从托盘激活/恢复 WindowsTerminal.exe
#   - Alt+F7 : 从托盘激活/恢复 studio64.exe (Android Studio)
#   - Alt+F8 : 从托盘激活/恢复 douyin.exe
#   - Alt+F9 : 从托盘激活/恢复 Xshell.exe
#
# 托盘图标操作:
#   - 左键单击: 恢复窗口
#   - 右键单击: 弹出菜单(恢复窗口 / 关闭窗口 / 关于 / 退出)
#
# 依赖: pywin32  (pip install pywin32)
# ****************************************************************************

import sys
import time

import win32api
import win32con
import win32gui
import win32process

# ---------------------------------------------------------------------------
# 常量定义 (与 RBTray.h 保持一致)
# ---------------------------------------------------------------------------
NAME = "RBTrayHook"          # 隐藏窗口的类名/标题,用于检测是否已运行

MAXTRAYITEMS = 64

WM_TRAYCMD = win32con.WM_USER + 4   # 0x0404, 托盘图标回调消息

IDM_RESTORE = 0x1001
IDM_CLOSE   = 0x1002
IDM_EXIT    = 0x1003
IDM_ABOUT   = 0x1004

# 热键 ID
HOTKEY_MINIMIZE         = 0
HOTKEY_CHROME           = 1
HOTKEY_CURSOR           = 2
HOTKEY_MSTSC            = 3
HOTKEY_WINDOWS_TERMINAL = 4
HOTKEY_ANDROID_STUDIO   = 5
HOTKEY_DOUYIN           = 6
HOTKEY_XSHELL           = 7

# 托盘回调消息中的事件类型 (Shell_NotifyIcon version 3)
NIN_SELECT = win32con.WM_USER + 0   # 0x0400, 单击托盘图标

# Shell_NotifyIcon 版本相关
NOTIFYICON_VERSION = 3

# 窗口图标相关
ICON_SMALL = 0
ICON_BIG   = 1
GCLP_HICON   = -14
GCLP_HICONSM = -34

# GetAncestor 标志
GA_ROOT = 2

# 热键配置表: (热键ID, 修饰键, 虚拟键, 目标进程名或 None 表示最小化动作)
HOTKEYS = [
    (HOTKEY_MINIMIZE,         win32con.MOD_ALT, win32con.VK_F1, None),
    (HOTKEY_CHROME,           win32con.MOD_ALT, win32con.VK_F2, "chrome.exe"),
    (HOTKEY_CURSOR,           win32con.MOD_ALT, win32con.VK_F3, "cursor.exe"),
    (HOTKEY_MSTSC,            win32con.MOD_ALT, win32con.VK_F5, "mstsc.exe"),
    (HOTKEY_WINDOWS_TERMINAL, win32con.MOD_ALT, win32con.VK_F6, "WindowsTerminal.exe"),
    (HOTKEY_ANDROID_STUDIO,   win32con.MOD_ALT, win32con.VK_F7, "studio64.exe"),
    (HOTKEY_DOUYIN,           win32con.MOD_ALT, win32con.VK_F8, "douyin.exe"),
    (HOTKEY_XSHELL,           win32con.MOD_ALT, win32con.VK_F9, "Xshell.exe"),
]


class RBTray:
    def __init__(self):
        self.hwnd_hook = None                       # 本程序的隐藏消息窗口
        self.hwnd_items = [None] * MAXTRAYITEMS      # 已最小化到托盘的窗口列表
        self.hwnd_for_menu = None                    # 当前右键菜单针对的窗口
        self.wm_taskbar_created = None               # 资源管理器重启时的消息
        self.registered_hotkeys = []                 # 已成功注册的热键 ID

    # -------------------------------------------------------------------
    # 托盘项查找
    # -------------------------------------------------------------------
    def find_in_tray(self, hwnd):
        """返回 hwnd 在托盘列表中的索引,找不到返回 -1。"""
        for i in range(MAXTRAYITEMS):
            if self.hwnd_items[i] == hwnd:
                return i
        return -1

    # -------------------------------------------------------------------
    # 获取窗口图标
    # -------------------------------------------------------------------
    def get_window_icon(self, hwnd):
        try:
            icon = win32gui.SendMessage(hwnd, win32con.WM_GETICON, ICON_SMALL, 0)
            if icon:
                return icon
            icon = win32gui.SendMessage(hwnd, win32con.WM_GETICON, ICON_BIG, 0)
            if icon:
                return icon
            icon = win32gui.GetClassLong(hwnd, GCLP_HICONSM)
            if icon:
                return icon
            icon = win32gui.GetClassLong(hwnd, GCLP_HICON)
            if icon:
                return icon
        except Exception:
            pass
        # 退而求其次,使用默认图标
        return win32gui.LoadIcon(0, win32con.IDI_WINLOGO)

    # -------------------------------------------------------------------
    # 添加托盘图标
    # -------------------------------------------------------------------
    def add_to_tray(self, i):
        hwnd = self.hwnd_items[i]
        if not hwnd:
            return False
        try:
            title = win32gui.GetWindowText(hwnd)
        except Exception:
            title = ""
        icon = self.get_window_icon(hwnd)
        flags = win32gui.NIF_MESSAGE | win32gui.NIF_ICON | win32gui.NIF_TIP
        nid = (self.hwnd_hook, i, flags, WM_TRAYCMD, icon, title)
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
        except Exception:
            return False
        return True

    def add_window_to_tray(self, hwnd):
        i = self.find_in_tray(None)
        if i == -1:
            return False
        self.hwnd_items[i] = hwnd
        return self.add_to_tray(i)

    # -------------------------------------------------------------------
    # 最小化窗口到托盘
    # -------------------------------------------------------------------
    def minimize_window_to_tray(self, hwnd):
        ex_style = win32api.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if ex_style & win32con.WS_EX_MDICHILD:
            return

        style = win32api.GetWindowLong(hwnd, win32con.GWL_STYLE)
        if style & win32con.WS_CHILD:
            hwnd = win32gui.GetAncestor(hwnd, GA_ROOT)

        # 先隐藏窗口再添加到托盘
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        win32gui.ShowWindow(hwnd, win32con.SW_HIDE)

        if self.find_in_tray(hwnd) == -1:
            if not self.add_window_to_tray(hwnd):
                # 托盘添加失败,恢复窗口
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)

    # -------------------------------------------------------------------
    # 移除托盘图标
    # -------------------------------------------------------------------
    def remove_from_tray(self, i):
        nid = (self.hwnd_hook, i)
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        except Exception:
            return False
        return True

    def remove_window_from_tray(self, hwnd):
        i = self.find_in_tray(hwnd)
        if i == -1:
            return False
        if not self.remove_from_tray(i):
            return False
        self.hwnd_items[i] = None
        return True

    # -------------------------------------------------------------------
    # 从托盘恢复窗口
    # -------------------------------------------------------------------
    def restore_window_from_tray(self, hwnd):
        if not hwnd:
            return
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
        self.remove_window_from_tray(hwnd)

    # -------------------------------------------------------------------
    # 从托盘关闭窗口
    # -------------------------------------------------------------------
    def close_window_from_tray(self, hwnd):
        if not hwnd:
            return
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        time.sleep(0.05)
        if win32gui.IsWindow(hwnd):
            time.sleep(0.05)
        if not win32gui.IsWindow(hwnd):
            self.remove_window_from_tray(hwnd)

    # -------------------------------------------------------------------
    # 刷新托盘提示文字
    # -------------------------------------------------------------------
    def refresh_window_in_tray(self, hwnd):
        i = self.find_in_tray(hwnd)
        if i == -1:
            return
        if not win32gui.IsWindow(hwnd) or win32gui.IsWindowVisible(hwnd):
            self.remove_window_from_tray(hwnd)
        else:
            try:
                title = win32gui.GetWindowText(hwnd)
            except Exception:
                title = ""
            nid = (self.hwnd_hook, i, win32gui.NIF_TIP, 0, 0, title)
            try:
                win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid)
            except Exception:
                pass

    # -------------------------------------------------------------------
    # 通过进程名从托盘激活程序
    # -------------------------------------------------------------------
    def activate_application_from_tray(self, process_name):
        target = process_name.lower()

        def enum_proc(hwnd, _):
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                hproc = win32api.OpenProcess(
                    win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
                    False, pid)
                try:
                    path = win32process.GetModuleFileNameEx(hproc, 0)
                finally:
                    win32api.CloseHandle(hproc)
                name = path.rsplit("\\", 1)[-1]
                if name.lower() == target:
                    if self.find_in_tray(hwnd) != -1:
                        self.restore_window_from_tray(hwnd)
                        return False   # 停止枚举
            except Exception:
                pass
            return True   # 继续枚举

        try:
            win32gui.EnumWindows(enum_proc, None)
        except Exception:
            # EnumWindows 回调返回 False 时 pywin32 会抛异常,属正常的提前结束
            pass

    # -------------------------------------------------------------------
    # 弹出右键菜单
    # -------------------------------------------------------------------
    def execute_menu(self):
        menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(menu, win32con.MF_STRING, IDM_ABOUT,   "About RBTray")
        win32gui.AppendMenu(menu, win32con.MF_STRING, IDM_EXIT,    "Exit RBTray")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        win32gui.AppendMenu(menu, win32con.MF_STRING, IDM_CLOSE,   "Close Window")
        win32gui.AppendMenu(menu, win32con.MF_STRING, IDM_RESTORE, "Restore Window")

        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(self.hwnd_hook)
        win32gui.TrackPopupMenu(
            menu,
            win32con.TPM_LEFTBUTTON | win32con.TPM_RIGHTBUTTON
            | win32con.TPM_RIGHTALIGN | win32con.TPM_BOTTOMALIGN,
            pos[0], pos[1], 0, self.hwnd_hook, None)
        win32gui.PostMessage(self.hwnd_hook, win32con.WM_NULL, 0, 0)
        win32gui.DestroyMenu(menu)

    # -------------------------------------------------------------------
    # 窗口消息处理函数
    # -------------------------------------------------------------------
    def wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_COMMAND:
            cmd = win32api.LOWORD(wparam)
            if cmd == IDM_RESTORE:
                self.restore_window_from_tray(self.hwnd_for_menu)
            elif cmd == IDM_CLOSE:
                self.close_window_from_tray(self.hwnd_for_menu)
            elif cmd == IDM_ABOUT:
                win32gui.MessageBox(
                    self.hwnd_hook,
                    "RBTray (Python 版本)\n\n"
                    "把窗口最小化到系统托盘。\n"
                    "Alt+F1 最小化当前窗口到托盘。\n\n"
                    "基于 Nikolay Redko, J.D. Purcell, Benbuck Nason 的 RBTray。",
                    "About RBTray", win32con.MB_OK | win32con.MB_ICONINFORMATION)
            elif cmd == IDM_EXIT:
                win32gui.SendMessage(self.hwnd_hook, win32con.WM_DESTROY, 0, 0)
            return 0

        elif msg == WM_TRAYCMD:
            event = lparam
            index = wparam
            if event == NIN_SELECT:
                self.restore_window_from_tray(self.hwnd_items[index])
            elif event == win32con.WM_CONTEXTMENU or event == win32con.WM_RBUTTONUP:
                self.hwnd_for_menu = self.hwnd_items[index]
                self.execute_menu()
            elif event == win32con.WM_MOUSEMOVE:
                self.refresh_window_in_tray(self.hwnd_items[index])
            return 0

        elif msg == win32con.WM_HOTKEY:
            self.on_hotkey(wparam)
            return 0

        elif msg == win32con.WM_DESTROY:
            for i in range(MAXTRAYITEMS):
                if self.hwnd_items[i]:
                    self.restore_window_from_tray(self.hwnd_items[i])
            win32gui.PostQuitMessage(0)
            return 0

        elif self.wm_taskbar_created is not None and msg == self.wm_taskbar_created:
            # 资源管理器重启,重新添加所有托盘图标
            for i in range(MAXTRAYITEMS):
                if self.hwnd_items[i]:
                    self.add_to_tray(i)
            return 0

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    # -------------------------------------------------------------------
    # 热键处理
    # -------------------------------------------------------------------
    def on_hotkey(self, hotkey_id):
        if hotkey_id == HOTKEY_MINIMIZE:
            fg = win32gui.GetForegroundWindow()
            if not fg:
                return
            style = win32api.GetWindowLong(fg, win32con.GWL_STYLE)
            if not (style & win32con.WS_MINIMIZEBOX):
                return  # 没有最小化按钮,跳过
            self.minimize_window_to_tray(fg)
        else:
            # 其余热键都是"按进程名激活程序"
            for hk_id, _mod, _vk, proc in HOTKEYS:
                if hk_id == hotkey_id and proc:
                    self.activate_application_from_tray(proc)
                    break

    # -------------------------------------------------------------------
    # 创建隐藏窗口
    # -------------------------------------------------------------------
    def create_window(self):
        hinst = win32api.GetModuleHandle(None)
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.wnd_proc
        wc.hInstance = hinst
        wc.hbrBackground = win32con.COLOR_WINDOW + 1
        wc.lpszClassName = NAME
        class_atom = win32gui.RegisterClass(wc)

        self.hwnd_hook = win32gui.CreateWindow(
            class_atom, NAME, win32con.WS_OVERLAPPED,
            0, 0, 0, 0, 0, 0, hinst, None)

        self.wm_taskbar_created = win32gui.RegisterWindowMessage("TaskbarCreated")

    # -------------------------------------------------------------------
    # 注册热键
    # -------------------------------------------------------------------
    def register_hotkeys(self):
        # 注意: win32gui.RegisterHotKey 成功时返回 None,失败时抛出异常,
        # 不像 C++ 的 RegisterHotKey 返回 BOOL,所以要用 try/except 判断。
        for hk_id, mod, vk, _proc in HOTKEYS:
            try:
                win32gui.RegisterHotKey(self.hwnd_hook, hk_id, mod, vk)
                self.registered_hotkeys.append(hk_id)
            except Exception:
                vk_name = {
                    win32con.VK_F1: "F1", win32con.VK_F2: "F2",
                    win32con.VK_F3: "F3", win32con.VK_F5: "F5",
                    win32con.VK_F6: "F6", win32con.VK_F7: "F7",
                    win32con.VK_F8: "F8", win32con.VK_F9: "F9",
                }.get(vk, str(vk))
                win32gui.MessageBox(
                    0, "无法注册热键 Alt+%s (可能已被其他程序占用)" % vk_name,
                    "RBTray", win32con.MB_OK | win32con.MB_ICONERROR)

    def unregister_hotkeys(self):
        for hk_id in self.registered_hotkeys:
            try:
                win32gui.UnregisterHotKey(self.hwnd_hook, hk_id)
            except Exception:
                pass

    # -------------------------------------------------------------------
    # 主循环
    # -------------------------------------------------------------------
    def run(self):
        # 检测是否已经在运行
        existing = win32gui.FindWindow(NAME, NAME)
        if existing:
            if "--exit" in sys.argv:
                win32gui.SendMessage(existing, win32con.WM_CLOSE, 0, 0)
            else:
                win32gui.MessageBox(
                    0, "RBTray 已经在运行了。", "RBTray",
                    win32con.MB_OK | win32con.MB_ICONINFORMATION)
            return 0

        if "--exit" in sys.argv:
            # 没有正在运行的实例,直接退出
            return 0

        self.create_window()
        self.register_hotkeys()

        # 消息循环
        win32gui.PumpMessages()

        self.unregister_hotkeys()
        return 0


def main():
    app = RBTray()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
