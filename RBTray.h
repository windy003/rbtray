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

#define NAME L"RBTrayHook"

#define WM_TRAYCMD  0x0404
#define IDM_RESTORE 0x1001
#define IDM_CLOSE   0x1002
#define IDM_EXIT    0x1003
#define IDM_ABOUT   0x1004

#define HOTKEY_MINIMIZE 0
#define HOTKEY_CHROME   1
#define HOTKEY_CURSOR   2
#define HOTKEY_MSTSC 3
#define HOTKEY_WINDOWS_TERMINAL 4
#define HOTKEY_ANDROID_STUDIO 5
#define HOTKEY_DOUYIN 6
#define HOTKEY_XSHELL 7
