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
1. Standardní Win32 `ComboBox` sám o sobě nepřepisuje text v editačním poli položkou z historie při získání fokusu.
2. V původním Open Salamanderu posílala funkce `HistoryComboBox` (`src/viewer.cpp`) zprávu `WM_SETTEXT` přímo hlavnímu oknu ComboBoxu (`hwnd`).
3. V rámci starších UTF-8 úprav byla zavedena pomocná funkce `SetHistoryControlTextUtf8`, která detekovala vnitřní `Edit` control (`info.hwndItem`) a zavolala `SetWindowTextW(target, ...)` **pouze na tento vnitřní Edit control**, aniž by poslala `WM_SETTEXT` nadřazenému ComboBoxu (`ctrl`).
4. Tím zůstal interní textový buffer ComboBoxu prázdný a desynchronizovaný od editačního pole. Při následném přidávání položek historie (`CB_ADDSTRING`) a při obdržení fokusu pak ComboBox provedl interní synchronizaci se seznamem položek, čímž došlo k přepsání textu prefixově shodnou položkou z historie.
5. Tento problém se projevoval všude, kde byla použita `HistoryComboBox` – nejvýrazněji v dialogu Hledat (`Alt+F7`) v poli "Look in" (`IDC_FIND_LOOKIN`), kde po předvyplnění aktuální cesty došlo k jejímu přepsání delší podadresářovou cestou z historie.
6. Dřívější oprava v `fix/archive-cache-and-copy-target-folder` v `src/dialogs3.cpp` sice opravila `SetControlTextUtf8` (aby posílala `WM_SETTEXT` i ComboBoxu), ale zároveň obsahovala berličku `InitialFocus`.

### 4.2 Provedené změny
1. **Sjednocení v `src/gui.h` a `src/gui.cpp`:**
   - Centralizovány a plně implementovány sdílené pomocné funkce: `ResolveComboEditControl`, `Utf8ToWideString`, `GetControlTextUtf8`, `SetControlTextUtf8` a `ComboAddStringUtf8`.
   - `SetControlTextUtf8` zaručuje obousměrnou synchronizaci: volá `SendMessageW(ctrl, WM_SETTEXT, ...)` pro ComboBox i `SetWindowTextW` pro podřízený Edit.
2. **Oprava `src/viewer.cpp`:**
   - Odstraněny lokální funkce `ResolveHistoryComboEditControl`, `GetHistoryControlTextUtf8` a vadná `SetHistoryControlTextUtf8`.
   - `HistoryComboBox` nyní používá sdílené `SetControlTextUtf8`, `GetControlTextUtf8` a `ComboAddStringUtf8`. Tím je opraveno chování ve všech dialozích používajících `HistoryComboBox` (včetně Find dialogu).
3. **Vyčištění `src/finddlg1.cpp`:**
   - Odstraněny lokální duplicitní implementace `ResolveFindComboEditControl` a `GetFindControlTextUtf8`.
   - Využity unifikované funkce z `gui.h`.
4. **Odstranění berličky v `src/dialogs.h` a `src/dialogs3.cpp`:**
   - Z `CCopyMoveDialog` a `CCopyMoveMoreDialog` byl kompletně odstraněn zástupný stav `InitialFocus` a obsluha `CBN_SETFOCUS` zachycující falešný autokomplet.
   - Odstraněny lokální duplikáty v `src/dialogs3.cpp`.
5. **Automatizované testy smluvního rozhraní:**
   - Vytvořen nový test `src/tests/combobox_text_sync_contract_tests.py`, který ověřuje deklaraci, definici a správné posílání `WM_SETTEXT` ComboBoxu i odstranění workaroundů.
