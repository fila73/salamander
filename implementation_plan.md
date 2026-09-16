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

## 3. Ověření a testy
- Spuštěny Python testy smluvního rozhraní (`src/tests/*.py`). Všechny testy (včetně `detached_tab_contract_tests.py`, `copy_move_scheduling_contract_tests.py`, `copy_move_conflict_state_tests.py`) úspěšně prošly.
- Úspěšně zkompilováno Release x64 (0 chyb, 0 varování).
- Ručně ověřeno v běžící aplikaci: cíl `C:\Users\filip\AntigravityProjects` se při kopírování ze ZIP archivu i Plugin FS nepřepisuje na `salamander-s3-plugin` a rozbalovací historie zůstává plně k dispozici.
