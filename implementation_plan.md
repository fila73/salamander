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
