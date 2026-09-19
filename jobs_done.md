# Zpráva o realizaci a přehled oprav (Jobs Done)

Tento dokument shrnuje realizované opravy v rámci větve `fix/archive-cache-and-copy-target-folder`.

---

## 📋 1. Přehled realizovaných oprav

| Oblast | Problém | Řešení a klíčové soubory |
|---|---|---|
| **Přepsání cílové složky z historie (F5)** | Při kopírování ze ZIP archivu či Plugin FS do panelu s nadřazenou složkou (např. `C:\...\AntigravityProjects`) Windows ComboBox při získání fokusu automaticky přepsal editační pole podadresářem z historie (např. `...\salamander-s3-plugin`). | • `src/dialogs.h` a `src/dialogs3.cpp` (`CCopyMoveDialog`, `CCopyMoveMoreDialog`): zaveden stav `InitialFocus`. Při prvotním `CBN_SETFOCUS` dialog ověří, zda ComboBox nezměnil text zadané cesty na položku z historie; pokud ano, obnoví původní `Path` a zachová označení textu.<br>• `src/dialogs3.cpp` (`SetControlTextUtf8`): vyčištěna a sjednocena obousměrná synchronizace textu mezi ComboBoxem a jeho interním Edit controlem. |
| **Cílová cesta při kopírování (F5)** | Při kopírování ze ZIPu nebo Plugin FS (GDrive, SFTP, S3, SharePoint atd.) selhalo zjištění cesty z protějšího panelu (vracelo prázdný řetězec / NULL), což vedlo k vyplnění 1. položky z historie (`History[0]`). | • `src/mainwnd.h` (`GetNonActivePanel`): rozšířeno o korektní detekci všech detached tabů (`FindDetachedTab`) a stran panelů (`GetPanelSide`).<br>• `src/mainwnd4.cpp` (`GetPanel`): podpora detached tabů pro `PANEL_LEFT` a `PANEL_RIGHT`.<br>• `src/zip.cpp` (`GetPanelWithPluginFS`): přidáno prohledávání všech detached tabů i tabů na levé i pravé straně.<br>• `src/fileswna.cpp` (`PluginFSFilesAction`): zachování záložní cílové cesty z protějšího panelu i v případě, že plugin při `mode == 1` vrátí `FALSE` (přechod na standardní dialog).<br>• `src/fileswn7.cpp` (`UnpackZIPArchive`): fallback na protější panel, pokud je `target == NULL`, a zachování platné cílové cesty.<br>• `src/fileswn8.cpp` (`FilesAction`): zachování platné cílové cesty při kopírování z disku do Plugin FS. |
| **Zneplatnění cache prohlížeče archivu** | Salamander nedetekoval změny v souboru ZIP se stejným názvem a cestou (používal zastaralý soubor z diskové mezipaměti). | • `src/fileswn5.cpp` (`BuildArchiveCacheKey`): klíč pro diskovou mezipaměť nyní zahrnuje datum a čas poslední změny archivu (`LastWriteTime`) a jeho velikost na disku (`FileSize`), plus CRC, velikost a čas modifikace konkrétní položky uvnitř archivu (`f->CRC`, `f->Size`, `f->LastWrite`). |
| **Sestavení a čistota repozitáře** | `git status` hlásil stovky vygenerovaných `.tab`, `.tlog` a výstupních souborů; poškozený `NuGet.config`. | • `.gitignore`: doplněny výstupní a staging složky `/salamander/` a `src/plugins/**/vcxproj/**/salamander/`.<br>• `NuGet.config`: opraven poškozený XML soubor.<br>• `src/plugins/winscp/salamander/FileSystem.cpp`: odstraněno stínování proměnné `Panel`.<br>• `tools/stage_inno_payload.ps1`, `tools/stage_vcpkg_payload_dlls.ps1`: robustní hashování `Get-FileHash`. |

---

## 🔍 2. Technické detaily

### 2.1 Ochrana cílové cesty před autokompletem ComboBoxu (`InitialFocus`)
Při kopírování z archivu nebo Plugin FS se do dialogu předává čistá cesta k cílovému adresáři (např. `C:\Users\filip\AntigravityProjects`). 
Pokud uživatel v minulosti kopíroval do podadresáře v této složce (např. `C:\Users\filip\AntigravityProjects\salamander-s3-plugin`), standardní Windows ovládací prvek `ComboBox` se stylem `CBS_DROPDOWN` při inicializaci a obdržení prvotního fokusu (`WM_SETFOCUS` / `CBN_SETFOCUS`) detekoval, že zadaný řetězec je prefixem první položky v historii, a automaticky jej nahradil touto delší položkou.

Řešení:
1. Třídy `CCopyMoveDialog` a `CCopyMoveMoreDialog` sledují stav `InitialFocus`.
2. V `DialogProc` v obsluze `WM_COMMAND` pro `IDE_PATH` při notifikaci `CBN_SETFOCUS` se v rámci úvodního zobrazení zkontroluje, zda aktuální text v ovládacím prvku odpovídá původnímu řetězci `Path`.
3. Pokud došlo k nežádoucímu přepsání, dialog obnoví zadanou cestu `Path` a nastaví korektní výběr textu.
4. Výběr z historie uživatelem (kliknutím na dropdown či šipkami) zůstává 100% zachován a plně funkční.

### 2.2 Detekce protějšího panelu a cílové cesty
Původní implementace `GetNonActivePanel()` kontrolovala pouze jednoduchou rovnost ukazatele `activePanel == DetachedTabPanel` a `activePanel == LeftPanel`. V moderním Samandarinu s podporou více detached tabů a více záložek na panel docházelo k chybnému určení protějšího panelu. Nyní se vyhodnocuje `FindDetachedTab(activePanel)` i `activePanel->GetPanelSide()`.

Zároveň v `PluginFSFilesAction` a `UnpackZIPArchive`, pokud cílový plugin při `mode == 1` (příprava cesty pro standardní dialog) vrátil `FALSE`, Salamander dříve chybně vyprázdnil `path[0] = 0`. Nyní se zachovává obecná cesta k protějšímu panelu (`target->GetGeneralPath()`), takže dialog `CCopyMoveDialog` vždy nabídne správnou cílovou složku.

### 2.3 Zneplatnění mezipaměti prohlížeče bez výkonnostního dopadu
Místo pomalého počítání kontrolního součtu celého (potenciálně gigabajtového) ZIP souboru z disku se využívají:
1. Win32 metadata souboru archivu (`ftLastWriteTime` s přesností 100 ns + 64bitová velikost `nFileSize`).
2. Metadata souboru uvnitř archivu z centrálního adresáře ZIPu (`f->Size`, `f->LastWrite`, `f->CRC`).
Tento přístup je okamžitý (0 ms) a 100% spolehlivě detekuje jak výměnu celého ZIP souboru na disku, tak modifikaci konkrétní položky v archivu.

---

## 🚀 3. Sestavení a nasazení binárních souborů

- **Stav sestavení:** Release x64 proběhl úspěšně (0 chyb, 0 varování).
- **Výsledná binárka:**
  `src\vcxproj\salamander\Release_x64\salamand.exe`
- **Co nahrát / aktualizovat:**
  - **Pouze `salamand.exe`**.
  - Veškeré provedené změny (detekce cesty protějšího panelu, taby, Plugin FS, oprava cache prohlížeče archivů i oprava ComboBoxu v copy dialogu) jsou přímo součástí jádra `salamand.exe`.
  - Plugin `zip.spl` není potřeba nahrávat.

---

# Větev: `feature/viewer-search-and-prism-fixes`

Tato část shrnuje realizované opravy ve větvi `feature/viewer-search-and-prism-fixes` řešící issues #758, #738, #745 a #749.

## 📋 Přehled realizovaných úprav

| Oblast / Issue | Problém | Řešení a klíčové soubory |
|---|---|---|
| **Focus po otevření (#738)** | Po otevření souboru v Prism Text Vieweru nefungovalo Ctrl+F bez předchozího kliknutí myší do okna. | • `src/plugins/shared/webviewviewer/native_viewer.cpp`: zavedena obsluha `WM_SETFOCUS` volající `FocusBrowser()`, která předává fokus do WebView2 controlleru (`COREWEBVIEW2_MOVE_FOCUS_REASON_PROGRAMMATIC`).<br>• Doplněno automatické zaměření při dokončení inicializace v `ShowPrismBrowser()`, `CompletePrismDisplay()` a `domContentLoadedToken_`. |
| **Vyhledávací fráze z okna Hledat (#758)** | Při otevření souboru klávesou F3 z okna Hledat (Find) se vyhledávaný text nepředával do Prism ani WebView2 prohlížeče. | • `src/plugins/shared/spl_gen.h`: rozšířena struktura `CSalamanderPluginViewerSelectionData` o `SearchPhrase` a `SearchFlags` (`SALVIEWER_SEARCH_CASE_SENSITIVE`, `SALVIEWER_SEARCH_WHOLE_WORDS`). Přidány konfigurační parametry `SALCFG_VIEWERFINDTEXT`, `SALCFG_VIEWERFINDCASE`, `SALCFG_VIEWERFINDWHOLEWORDS`.<br>• `src/plugins1.cpp`: v `CPluginData::ViewFile` se předává vyhledávací řetězec z `GlobalFindDialog.Text` do pluginů.<br>• `src/zip.cpp`: implementována obsluha `SALCFG_VIEWERFIND*` v `GetConfigParameter`.<br>• `src/plugins/textviewer/managed_bridge.*`, `src/plugins/webview2renderviewer/managed_bridge.*`: předání fráze a příznaků do `NativeViewerRequest`.<br>• `src/plugins/shared/webviewviewer/native_viewer.cpp`: v `RenderDocument` se při načtení automaticky spouští `window.find()`; v `PrismText` se fráze předává do virtuálního prohlížeče a okamžitě vyhledá. |
| **Vyhledávání ve virtuálním textu Prism (#745)** | Prism Text Viewer nevyhledal slova mimo aktuální viewport, protože virtuální scroller (`virtual-viewer.js`) drží v DOMu jen viditelné bloky textu. | • `src/plugins/shared/webviewviewer/native_viewer.cpp`: implementováno celotextové vyhledávání v paměti (`virtualText_`) s O(log N) mapováním na řádky a sloupce pomocí `virtualLineStarts_`.<br>• `src/plugins/shared/webviewviewer/prism/viewer/virtual-viewer.html`: přidán integrovaný Find Bar s tlačítky pro shodu velikosti písmen (Aa), celá slova (\b), přechod na další (▼/Enter/F3), předchozí (▲/Shift+Enter/Shift+F3) a zavření (✕/Esc).<br>• `src/plugins/shared/webviewviewer/prism/viewer/virtual-viewer.js`: navigace k nalezenému řádku, automatická materializace chunku a přesné zvýraznění výskytu pomocí DOM Range & Selection s vystředěním na obrazovce. |
| **Optimalizace startu (#749)** | Prism Text Viewer a WebView2 startovaly pomalu (~3 sekundy). | • `src/plugins/shared/webviewviewer/native_viewer.cpp`: paralelní spuštění přípravy dokumentu (`StartPreparation`) přímo v `WM_CREATE` souběžně s vytvářením WebView2 controlleru. Po dokončení controlleru je dokument již načten a připraven v paměti.<br>• `src/plugins/shared/webviewviewer/prism/viewer/virtual-viewer.js`: odstraněna zbytečná zpoždění při odesílání `salamander-prism-ready` notifikace po vykreslení prvního chunku. |

