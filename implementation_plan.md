# Plán implementace: Vyhledávání ve viewerech (WebView2 / Prism), oprava focusu a optimalizace startu (#758, #738, #745, #749)

Tento plán řeší 4 související issues ve větví `feature/viewer-search-and-prism-fixes` založené na `upstream/release/5.0-samandarin-0.16`.

---

## 1. Rozdělení issues a vztah k WebView2 a Prism

| Issue | Název / Podstata | Týká se | Důvod |
| :--- | :--- | :--- | :--- |
| **#738** | Focus po otevření (nefunguje Ctrl+F) | **WebView2 i Prism** | Společný kód `native_viewer.cpp` neobsluhuje `WM_SETFOCUS` a nevolá `controller_->MoveFocus()`. |
| **#758** | Naplnění vyhledávací fráze z okna Hledat | **WebView2 i Prism** | Salamander nepředává `GlobalFindDialog.Text` do pluginových viewerů. |
| **#745** | Nevyhledá slova v textu | **Především Prism** | Prism používá virtuální scroller (`virtual-viewer.js`), kde jsou v DOMu jen viditelné řádky; slova mimo viewport nejsou v DOMu přítomna. |
| **#749** | Pomalý start (~3 sekundy) | **WebView2 i Prism** | Start procesu `msedgewebview2.exe` na vyžádání + u Prism kaskáda asynchronních IPC zpráv před zobrazením. |

---

## 2. Navrhované změny

### Komponenta 1: Oprava focusu ve WebView2 & Prism ([#738](https://github.com/KRtkovo-eu-AI/salamander/issues/738))
- **`src/plugins/shared/webviewviewer/native_viewer.cpp`:**
  - V `ViewerWindow::WndProc` přidat obsluhu zprávy `WM_SETFOCUS` volající `controller_->MoveFocus(COREWEBVIEW2_MOVE_FOCUS_REASON_PROGRAMMATIC)`.
  - Při zobrazení prohlížeče (`ShowPrismBrowser()` a `domContentLoadedToken_`) zajistit předání fokusu.

### Komponenta 2: Propagace vyhledávací fráze z okna Hledat ([#758](https://github.com/KRtkovo-eu-AI/salamander/issues/758))
- **`src/plugins/shared/spl_gen.h`:**
  - Přidat konstanty `SALCFG_VIEWERFINDTEXT`, `SALCFG_VIEWERFINDCASE` a `SALCFG_VIEWERFINDWHOLEWORDS`.
  - Rozšířit `CSalamanderPluginViewerSelectionData` o `const char* SearchPhrase;` a `DWORD SearchFlags;`.
- **`src/mainwnd2.cpp`:**
  - Implementovat podporu nových konfiguračních parametrů v `CSalamanderGeneral::GetConfigParameter`.
- **`src/plugins1.cpp`:**
  - V `CPluginData::ViewFile` naplnit `SearchPhrase` a předat strukturu do pluginu.
- **`src/plugins/textviewer/managed_bridge.cpp` & `src/plugins/webview2renderviewer/managed_bridge.cpp`:**
  - Předat hledanou frázi do `NativeViewerRequest`.
- **`src/plugins/shared/webviewviewer/native_viewer.cpp`:**
  - Uložit frázi a při zobrazení ji předvyplnit/spustit vyhledání:
    - V `RenderDocument` přes `window.find(...)`.
    - V `PrismText` přes interní hledání.

### Komponenta 3: Vyhledávání ve virtualizovaném textu Prism ([#745](https://github.com/KRtkovo-eu-AI/salamander/issues/745))
- **`src/plugins/shared/webviewviewer/native_viewer.cpp`:**
  - Využít existující `virtualText_` a `virtualLineStarts_` pro celotextové vyhledání pozice v textu.
  - Poslat do `virtual-viewer.js` zprávu s nalezeným řádkem a sloupcem.
- **`src/plugins/shared/webviewviewer/prism/viewer/virtual-viewer.js`:**
  - Odrolovat na nalezený řádek (čímž se chunk materializuje do DOMu) a zvýraznit výskyt.

### Komponenta 4: Optimalizace startu WebView2 & Prism ([#749](https://github.com/KRtkovo-eu-AI/salamander/issues/749))
- **`src/plugins/shared/webviewviewer/native_viewer.cpp`:**
  - Pre-warmed WebView2 controller v `NativeViewer_EnsureInitialized()`.
  - Optimalizace a zkrácení asynchronního handshake před prvním zobrazením.

---

## 3. Plán ověření a testování
- Spuštění contract testů (`webview2_render_viewer_contract_tests.py`, `ui_font_contract_tests.py`).
- Vyčištění Python cache (`__pycache__`, `*.pyc`).
- Ověření sestavení Release x64 v MSBuild.
- Manuální ověření klávesových zkratek, F3 přechodů z okna Hledat a focusu.

---

## 4. Stav realizace (Dokončeno)
- ✅ **#738**: Vyřešeno předáváním fokusu do browser controlleru při `WM_SETFOCUS`, `ShowPrismBrowser()`, `CompletePrismDisplay()` a `domContentLoadedToken_`.
- ✅ **#758**: Vyřešeno rozšířením SDK (`spl_gen.h`), předáváním `SearchPhrase` a `SearchFlags` z jádra (`plugins1.cpp`, `zip.cpp`), mostů (`managed_bridge.cpp`) a automatickým spuštěním vyhledávání v Prism i WebView2.
- ✅ **#745**: Vyřešeno celotextovým vyhledáváním v `native_viewer.cpp` napříč všemi virtuálními chunky, integrovaným Find Barem v `virtual-viewer.html` / `virtual-viewer.js` a plnou navigací F3 / Shift+F3 / Enter / Shift+Enter.
- ✅ **#749**: Vyřešeno paralelní přípravou dokumentu (`StartPreparation` souběžně s inicializací WebView2 v `WM_CREATE`) a eliminací zbytečných zpoždění při ready notifikaci.
- ✅ **Testy**: Všechny contract testy procházejí bez chyb.

## 4. Navazující úkol: Sjednocení synchronizace ComboBoxů a oprava Find Look in (`fix/combobox-sync-and-find-lookin`)

### 4.1 Identifikovaný kořenový problém (Root Cause)
Při hlubší analýze chování editačních polí s historií (`ComboBox` se stylem `CBS_DROPDOWN`) napříč kódem Salamanderu bylo zjištěno:
1. **Obrácené pořadí v `HistoryComboBox` (`src/viewer.cpp`):**
   `HistoryComboBox` dříve volala `SetControlTextUtf8(hwnd, Text)` *před* přidáním položek historie. Následné volání `ComboAddStringUtf8` pro položky z historie mohlo ovlivnit interní stav ComboBoxu.
2. **Win32 ComboBox prefix matching při získání fokusu (`CBN_SETFOCUS`):**
   Pokud je aktuální adresář v editačním poli ComboBoxu (se stylem `CBS_DROPDOWN`) striktním prefixem některé položky z historie (např. `...\AntigravityProjects` vs `...\AntigravityProjects\salamander-sftp-plugin\test`), Windows ComboBox při inicializaci a získání fokusu automaticky vyhledá shodu a nahradí obsah pole touto delší položkou z historie.
3. **Chybějící ochrana ve Find dialogu:**
   Zatímco v `CCopyMoveDialog` byla dříve přidána ochrana na `CBN_SETFOCUS`, v `CFindDialog` pro `IDC_FIND_LOOKIN` a `IDC_FIND_NAMED` zcela chyběla.
4. **Desynchronizace UTF-8 textu:**
   Při dřívější migraci na UTF-8 zavedená funkce `SetHistoryControlTextUtf8` v `src/viewer.cpp` posílala `SetWindowTextW` pouze na vnitřní Edit control, čímž byl buffer ComboBoxu ponechán desynchronizovaný.

### 4.2 Provedené změny
1. **Sjednocení v `src/gui.h` a `src/gui.cpp`:**
   - Centralizovány a plně implementovány sdílené pomocné funkce: `ResolveComboEditControl`, `Utf8ToWideString`, `GetControlTextUtf8`, `SetControlTextUtf8` a `ComboAddStringUtf8`.
   - `SetControlTextUtf8` zaručuje obousměrnou synchronizaci: volá `SendMessageW(ctrl, WM_SETTEXT, ...)` pro ComboBox i `SetWindowTextW` pro podřízený Edit.
2. **Oprava pořadí plnění v `src/viewer.cpp`:**
   - V `HistoryComboBox` se nejprve naplní seznam historie (`ComboAddStringUtf8`) a teprve poté se nastaví cílový text pomocí `SetControlTextUtf8(hwnd, Text)`. Tím je zaručeno, že explicitní text je vždy nastaven jako poslední.
3. **Systematická ochrana na `CBN_SETFOCUS`:**
   - V `CFindDialog` (`src/find.h`, `src/finddlg1.cpp`) zavedeny stavy `InitialFocusLookIn` a `InitialFocusNamed`. Na zprávu `CBN_SETFOCUS` dialog detekuje případné nežádoucí přepsání textu z historie a obnoví zadaný text.
   - V `CCopyMoveDialog` a `CCopyMoveMoreDialog` (`src/dialogs.h`, `src/dialogs3.cpp`) obnovena a zachována ochrana `InitialFocus` na zprávu `CBN_SETFOCUS` pro `IDE_PATH`.
4. **Automatizované testy smluvního rozhraní:**
   - Test `src/tests/combobox_text_sync_contract_tests.py` ověřuje deklaraci, definici a správné posílání `WM_SETTEXT` ComboBoxu i přítomnost ochrany `InitialFocus` v hlavičkách i dialogových procedurách.
5. **Nasazení (Deployment):**
   - Vždy je nutné společně nasadit jak zkompilovaný `salamand.exe`, tak `lang\english.slg` do cílového umístění `C:\Apps\samandarin\`.
