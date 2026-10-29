# SPDX-FileCopyrightText: 2026 Open Salamander Authors
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
GUI_H = SRC / "gui.h"
GUI_CPP = SRC / "gui.cpp"
VIEWER_CPP = SRC / "viewer.cpp"
FIND_H = SRC / "find.h"
FINDDLG1_CPP = SRC / "finddlg1.cpp"
DIALOGS_H = SRC / "dialogs.h"
DIALOGS3_CPP = SRC / "dialogs3.cpp"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_gui_combobox_helpers_declared_and_defined():
    gui_h_text = GUI_H.read_text(encoding="utf-8", errors="replace")
    gui_cpp_text = GUI_CPP.read_text(encoding="utf-8", errors="replace")

    for fn in ("ResolveComboEditControl", "Utf8ToWideString", "GetControlTextUtf8", "SetControlTextUtf8", "ComboAddStringUtf8"):
        require(fn in gui_h_text, f"{fn} must be declared in gui.h")
        require(f"{fn}(" in gui_cpp_text, f"{fn} must be defined in gui.cpp")

    # Verify SetControlTextUtf8 sends WM_SETTEXT to the combo control itself to keep internal state synced
    require("SendMessageW(ctrl, WM_SETTEXT, 0, (LPARAM)wideStr);" in gui_cpp_text,
            "SetControlTextUtf8 must send WM_SETTEXT to the parent combo window")


def test_viewer_history_combo_uses_unified_helpers():
    viewer_text = VIEWER_CPP.read_text(encoding="utf-8", errors="replace")

    require("SetHistoryControlTextUtf8" not in viewer_text,
            "Broken SetHistoryControlTextUtf8 must be eliminated from viewer.cpp")
    require("GetHistoryControlTextUtf8" not in viewer_text,
            "GetHistoryControlTextUtf8 must be eliminated from viewer.cpp")
    require("ResolveHistoryComboEditControl" not in viewer_text,
            "ResolveHistoryComboEditControl must be eliminated from viewer.cpp")

    require("SetControlTextUtf8(hwnd, Text);" in viewer_text,
            "HistoryComboBox must use SetControlTextUtf8")
    require("GetControlTextUtf8(hwnd, Text, textLen);" in viewer_text,
            "HistoryComboBox must use GetControlTextUtf8")
    require("ComboAddStringUtf8(hwnd, history[i]);" in viewer_text,
            "HistoryComboBox must use ComboAddStringUtf8 for history item insertion")


def test_find_dialog_uses_unified_helpers():
    find_h_text = FIND_H.read_text(encoding="utf-8", errors="replace")
    finddlg_text = FINDDLG1_CPP.read_text(encoding="utf-8", errors="replace")

    require("ResolveFindComboEditControl" not in finddlg_text,
            "ResolveFindComboEditControl must be eliminated from finddlg1.cpp")
    require("GetFindControlTextUtf8" not in finddlg_text,
            "GetFindControlTextUtf8 must be eliminated from finddlg1.cpp")
    require("GetControlTextUtf8(hLookInWnd, Data.LookInText, LOOKIN_TEXT_LEN);" in finddlg_text,
            "Find LookIn must use GetControlTextUtf8")


def main():
    test_gui_combobox_helpers_declared_and_defined()
    test_viewer_history_combo_uses_unified_helpers()
    test_find_dialog_uses_unified_helpers()
    print("combobox_text_sync_contract_tests: ok")


if __name__ == "__main__":
    main()
