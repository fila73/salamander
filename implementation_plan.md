# Plán implementace: Oprava detekce cílového panelu, mezipaměti prohlížeče archivu a copy dialogu

Tento dokument rekapituluje plán a realizaci oprav v rámci větve `fix/archive-cache-and-copy-target-folder`.

---

## 1. Cíl úkolu
1. **Oprava přepsání cílové složky z historie v dialogu kopírování/přesunu:**
   Při kopírování z archivu nebo Plugin FS (např. GDrive, SFTP, SharePoint, S3) do panelu s nadřazenou složkou docházelo při inicializaci ComboBoxu k automatickému nahrazení cílové složky podadresářem z historie (prefix auto-complete při `WM_SETFOCUS`).
2. **Oprava zjištění cílové cesty z protějšího panelu (F5):**
   V prostředí s více taby a odepnutými okny (detached tabs) zajistit spolehlivé určení protějšího panelu a uchování jeho cesty i při návratu `FALSE` z pluginu.
3. **Zneplatnění cache prohlížeče (F3):**
   Při změně ZIP souboru se stejným názvem a cestou zajistit okamžité zneplatnění mezipaměti podle času modifikace archivu na disku a metadat souborů uvnitř archivu.
4. **Čistota repozitáře a sestavení:**
   Oprava `.gitignore`, aby nesledoval vygenerované výstupní adresáře, oprava XML v `NuGet.config` a oprava stínování proměnné ve WinSCP.

---

## 2. Realizované změny

### Komponenta: Dialogy kopírování a přesunu (ComboBox auto-complete)
- **`src/dialogs.h` & `src/dialogs3.cpp` (`CCopyMoveDialog`, `CCopyMoveMoreDialog`):**
  - Přidán stav `InitialFocus`.
  - Při zachycení `CBN_SETFOCUS` během prvotního zobrazení dialog zkontroluje, zda ComboBox svévolně nezměnil text cesty na položku z historie.
  - V případě neshody obnoví přesnou hodnotu `Path` a nastaví výběr celého textu.
  - Používá bezpečný heap-backed `CPathBuffer` pro textové vyrovnávací paměti bez přetížení zásobníku.

### Komponenta: Detekce panelů a cílové cesty
- **`src/mainwnd.h` (`GetNonActivePanel`):**
  Detekce protějšího panelu nyní plně respektuje odepnutá okna (`IsDetachedTabPanel`, `FindDetachedTab`) i strany panelů (`GetPanelSide`), čímž spolehlivě vrací protější panel i při práci se záložkami.
- **`src/mainwnd4.cpp` (`GetPanel`):**
  Při dotazu na `PANEL_LEFT` a `PANEL_RIGHT` ověřuje detached taby a vrací odpovídající okno.
- **`src/zip.cpp` (`GetPanelWithPluginFS`):**
  Rozšířeno vyhledávání Plugin FS napříč všemi záložkami (levá i pravá strana) i odepnutými okny.
- **`src/fileswna.cpp` (`PluginFSFilesAction`):**
  Při `mode == 1` v `CopyOrMoveFromFS` uchovává obecnou cestu protějšího panelu jako fallback i v situaci, kdy cílový plugin vrátí `FALSE`.
- **`src/fileswn7.cpp` (`UnpackZIPArchive`):**
  Fallback na protější panel, pokud je `target == NULL`, a uchování platné cílové cesty pro dialog.
- **`src/fileswn8.cpp` (`FilesAction`):**
  Zachování cílové cesty při kopírování z disku do Plugin FS, pokud plugin vrátí `FALSE` bez modifikace bufferu.

### Komponenta: Zneplatnění mezipaměti prohlížeče archivu
- **`src/fileswn5.cpp` (`BuildArchiveCacheKey`):**
  Klíč pro diskovou mezipaměť zahrnuje:
  - Čas poslední modifikace archivu na disku (`ftLastWriteTime`) a 64bitovou velikost (`nFileSize`).
  - Metadata konkrétní položky v archivu: velikost (`f->Size`), čas modifikace (`f->LastWrite`) a název (`f->Name`).
  Detekce je 100% spolehlivá a okamžitá (bez nutnosti číst celý ZIP soubor z disku pro hashování).

---

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
