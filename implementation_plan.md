# Plán implementace: Oprava detekce cílového panelu a mezipaměti prohlížeče archivu

Tento dokument rekapituluje plán a realizaci oprav v rámci větve `fix/archive-cache-and-copy-target-path`.

---

## 1. Cíl úkolu
1. **Oprava zjištění cílové cesty (F5):**
   Při kopírování ze ZIP archivu i Plugin FS (např. GDrive, SFTP, SharePoint, S3) docházelo k selhání načtení cesty z protějšího panelu, cesta zůstala prázdná (`""`) a do dialogu se předvyplnila 1. položka z historie (`History[0]`).
2. **Zneplatnění cache prohlížeče (F3):**
   Při změně ZIP souboru se stejným názvem a cestou Salamander používal starý soubor z mezipaměti.
3. **Čistota repozitáře a sestavení:**
   Oprava `.gitignore`, aby nesledoval vygenerované výstupní adresáře, oprava XML v `NuGet.config` a oprava stínování proměnné ve WinSCP.

---

## 2. Realizované změny

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
- Čistý `git status` bez nezpracovaných změn a bez zbytečných vygenerovaných souborů.
