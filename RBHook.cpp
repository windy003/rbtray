// ****************************************************************************
//
// RBTray
// 版权所有 (C) 1998-2010  Nikolay Redko, J.D. Purcell
// 版权所有 (C) 2015 Benbuck Nason
//
// 本程序是自由软件;你可以根据自由软件基金会发布的
// GNU 通用公共许可证(GPL)的条款(许可证的第 2 版,
// 或者(由你选择)任何更高的版本)重新分发和/或修改本程序。
//
// 发布本程序的目的是希望它有用,但不提供任何担保;
// 甚至不包含适销性或对特定用途适用性的隐含担保。
// 详情请参阅 GNU 通用公共许可证。
//
// 你应该已经随本程序收到一份 GNU 通用公共许可证的副本;
// 如果没有,请写信给自由软件基金会:
// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//
// ****************************************************************************

#include <windows.h>
#include <stdio.h>
#include "RBTray.h"

static HHOOK _hMouse = NULL;
static HHOOK _hWndProcRet = NULL;
static HWND _hLastHit = NULL;


//#define DEBUG_PRINTF(fmt, ...) do { char buf[1024]; snprintf(buf, sizeof(buf), fmt, ##__VA_ARGS__); OutputDebugStringA(buf); } while (0)

// 适用于 32 位和 64 位应用程序
LRESULT CALLBACK MouseProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode >= 0) {
        //if ((wParam != WM_MOUSEMOVE) && (wParam != WM_NCMOUSEMOVE)) DEBUG_PRINTF("%s(%d): nCode %d, wParam %llx, lParam %llx\n", __FUNCTION__, __LINE__, nCode, (long long int)wParam, (long long int)lParam);
        MOUSEHOOKSTRUCT * info = (MOUSEHOOKSTRUCT *)lParam;
        //if ((wParam != WM_MOUSEMOVE) && (wParam != WM_NCMOUSEMOVE)) DEBUG_PRINTF("%s(%d): pt (%ld, %ld), hwnd %p, wHitTestCode %u, dwExtraInfo %llx\n", __FUNCTION__, __LINE__, info->pt.x, info->pt.y, info->hwnd, info->wHitTestCode, info->dwExtraInfo);
        if ((wParam == WM_NCRBUTTONDOWN) || (wParam == WM_NCRBUTTONUP)) {
            //DEBUG_PRINTF("%s(%d): button\n", __FUNCTION__, __LINE__);
            if (info->wHitTestCode == HTCLIENT) {
                //DEBUG_PRINTF("%s(%d): ignoring client hit test code for non-client message\n", __FUNCTION__, __LINE__);
            } else {
                BOOL shiftKeyDown = (GetKeyState(VK_SHIFT) & 0x8000) ? TRUE : FALSE;
                BOOL isHit = (info->wHitTestCode == HTMINBUTTON) || ((info->wHitTestCode == HTCAPTION) && shiftKeyDown);
                //DEBUG_PRINTF("%s(%d): shift %s, hit %s\n", __FUNCTION__, __LINE__, shiftKeyDown ? "yes" : "no", isHit ? "yes" : "no");
                if ((wParam == WM_NCRBUTTONDOWN) && isHit) {
                    //DEBUG_PRINTF("%s(%d): down hit\n", __FUNCTION__, __LINE__);
                    _hLastHit = info->hwnd;
                    return 1;
                } else if ((wParam == WM_NCRBUTTONUP) && isHit) {
                    //DEBUG_PRINTF("%s(%d): up hit\n", __FUNCTION__, __LINE__);
                    if (info->hwnd == _hLastHit) {
                        //DEBUG_PRINTF("%s(%d): up hit match\n", __FUNCTION__, __LINE__);
                        PostMessage(FindWindow(NAME, NAME), WM_ADDTRAY, 0, (LPARAM)info->hwnd);
                    }
                    _hLastHit = NULL;
                    return 1;
                } else {
                    //DEBUG_PRINTF("%s(%d): miss\n", __FUNCTION__, __LINE__);
                    _hLastHit = NULL;
                }
            }
        } else if ((wParam == WM_RBUTTONDOWN) || (wParam == WM_RBUTTONUP)) {
            //DEBUG_PRINTF("%s(%d): not button\n", __FUNCTION__, __LINE__);
            _hLastHit = NULL;
        }
    }
    return CallNextHookEx(_hMouse, nCode, wParam, lParam);
}

// 仅适用于 32 位应用程序或 64 位应用程序,
// 具体取决于本程序是以 32 位还是 64 位编译
LRESULT CALLBACK CallWndProcRet(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode >= 0) {
        CWPRETSTRUCT * msg = (CWPRETSTRUCT *)lParam;
        if (((msg->message == WM_WINDOWPOSCHANGED) &&
            (((WINDOWPOS *)msg->lParam)->flags & SWP_SHOWWINDOW) != 0) ||
            (msg->message == WM_NCDESTROY))
        {
            PostMessage(FindWindow(NAME, NAME), WM_REFRTRAY, 0, (LPARAM)msg->hwnd);
        }

        //if ((msg->message == WM_SYSCOMMAND)) {// && (msg->wParam == SC_MINIMIZE)) {
        //    DEBUG_PRINTF("%s(%d): minimize\n", __FUNCTION__, __LINE__);
        //    WCHAR text[256];
        //    GetWindowText(msg->hwnd, text, sizeof(text) / sizeof(text[0]));
        //    if (wcsstr(text, L"Notepad")) {
        //        //PostMessage(FindWindow(NAME, NAME), WM_ADDTRAY, 0, (LPARAM)msg->hwnd);
        //    }
        //}
    }
    return CallNextHookEx(_hWndProcRet, nCode, wParam, lParam);
}

BOOL DLLEXPORT RegisterHook(HMODULE hLib) {
    //DEBUG_PRINTF("%s(%d): register hook\n", __FUNCTION__, __LINE__);
    _hMouse = SetWindowsHookEx(WH_MOUSE, (HOOKPROC)MouseProc, hLib, 0);
    _hWndProcRet = SetWindowsHookEx(WH_CALLWNDPROCRET, (HOOKPROC)CallWndProcRet, hLib, 0);
    if ((_hMouse == NULL) || (_hWndProcRet == NULL)) {
        UnRegisterHook();
        return FALSE;
    }
    return TRUE;
}

void DLLEXPORT UnRegisterHook() {
    //DEBUG_PRINTF("%s(%d): unregister hook\n", __FUNCTION__, __LINE__);
    if (_hMouse) {
        UnhookWindowsHookEx(_hMouse);
        _hMouse = NULL;
    }
    if (_hWndProcRet) {
        UnhookWindowsHookEx(_hWndProcRet);
        _hWndProcRet = NULL;
    }
}
