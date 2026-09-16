# Návod na vývoj pluginů pro Open Salamander: Samandarin

Tento dokument slouží jako referenční příručka pro vývoj a údržbu pluginů v prostředí Open Salamander / Samandarin.

---

## 1. Architektura a adresářová struktura pluginu

Plugin do Salamandera je dynamická knihovna:
- **`*.spl`** – Samotná dynamická knihovna pluginu (Windows DLL přejmenovaná na `.spl`).
- **`lang/*.slg`** – Jazykové knihovny s přeloženými texty a dialogy (`english.slg`, `czech.slg`).

### Exportní funkce pluginu
Každý plugin exportuje funkci:
```cpp
extern "C" __declspec(dllexport) CPluginInterfaceAbstract* WINAPI SalamanderPluginEntry2(
    CSalamanderGeneralAbstract* salamanderGeneral,
    int salamanderVersion);
```

---

## 2. Práce s panely a cestami (Klíčová pravidla)

### 2.1 Konstanty panelů
V hlavičkovém souboru SDK `plugins.h` / `spl_gen.h` jsou definovány:
```cpp
#define PANEL_LEFT    0
#define PANEL_RIGHT   1
#define PANEL_SOURCE  2
#define PANEL_TARGET  3
```

### 2.2 Zjištění cesty a protějšího panelu
Při dotazu na cestu přes rozhraní `CSalamanderGeneralAbstract`:
* `GetPanelPath(PANEL_SOURCE, ...)` vrátí cestu v aktuálně aktivním (zdrojovém) panelu.
* `GetPanelPath(PANEL_TARGET, ...)` vrátí cestu v protějším (neaktivním) panelu.
* `GetPanelWithPluginFS(pluginFS, panel)` vyhledá panel (včetně všech záložek a detached oken), ve kterém je daný FS otevřen.

### 2.3 Životní cyklus `CopyOrMoveFromFS`
Při stisku klávesy `F5` v panelu s Plugin FS volá Salamander metodu:
```cpp
BOOL WINAPI CPluginFSInterface::CopyOrMoveFromFS(
    BOOL copy, int mode, const char* fsName, HWND parent,
    int panel, int selectedFiles, int selectedDirs,
    char* targetPath, BOOL& operationMask,
    BOOL& cancelOrHandlePath, HWND dropTarget);
```
* **`mode == 1` (Příprava dialogu):**
  - Salamander předvyplní do bufferu `targetPath` navrženou cílovou cestu z protějšího panelu.
  - Pokud chce plugin použít standardní kopírovací dialog Salamanderu, **ponechá navrženou cestu v `targetPath` a vrátí `FALSE`** (`cancelOrHandlePath` je `FALSE`).
  - Pozor: Parametr `panel` předaný ze Salamanderu je `PANEL_LEFT` (0) nebo `PANEL_RIGHT` (1), **nikoliv `PANEL_SOURCE`**! Pro získání protějšího panelu používejte `PANEL_TARGET` nebo `(panel == PANEL_LEFT ? PANEL_RIGHT : PANEL_LEFT)`.
* **`mode == 2` (Po potvrzení dialogu):**
  - `targetPath` obsahuje řetězec zadaný uživatelem v dialogu.
* **`mode == 4` (Chyba v zadané cestě):**
  - Umožňuje uživateli opravit neplatnou cestu.

### 2.4 Životní cyklus `CopyOrMoveFromDiskToFS`
Při kopírování z disku do pluginu:
* **`mode == 1`:** Umožňuje pluginu upravit cílovou cestu pro standardní dialog. Pokud plugin do `targetPath` nic nezapíše, Salamander zachová obecnou cestu k FS.

---

## 3. Binární kompatibilita Plugin SDK

* **Neměňte pořadí virtuálních metod:** Ve virtuálních rozhraních `*Abstract` (jako `CSalamanderGeneralAbstract`, `CSalamanderGUIAbstract`, `CPluginInterfaceAbstract`) nikdy neměňte signaturu, pořadí ani neodstraňujte existující metody.
* **Nové metody vždy přidávejte na konec vtable.** Starší pluginy volají metody přes sloty ve vtable, takže jakékoliv posunutí způsobí pád starších binárek.

---

## 4. Práce s cestami a kódováním

* **Žádné `MAX_PATH` buffery:** Pro cesty používejte kapacitu `SAL_MAX_PATH` nebo dynamické buffery (`std::wstring`, `std::string`, `CPathBuffer`).
* **Explicitní kódování:** Pro Win32 API preferujte široké varianty (`*W`).
* **Font dialogů:** Nepoužívejte `Segoe UI`, standardní font pro Win32 dialogy je:
  ```rc
  FONT 8, "MS Shell Dlg"
  ```
* **Podpora Dark Mode:** Každý nový dialog, okno nebo ovládací prvek musí podporovat Dark Mode (`USE_DARKMODELIB=1`).
