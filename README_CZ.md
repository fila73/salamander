# Open Salamander: Samandarin

Open Salamander: Samandarin je rychlý, spolehlivý a modernizovaný dvoupanelový správce souborů pro systém Windows.

Projekt navazuje na původní [Open Salamander](https://github.com/OpenSalamander/salamander) s důrazem na nová vylepšení, Unicode podporu, tmavý režim, moderní prohlížeče a ekosystém pluginů při zachování plné zpětné kompatibility.

---

## 🚀 Klíčové vlastnosti

### Správa souborů a operace
- **Plná podpora Unicode a dlouhých cest:** Názvy souborů v Unicode a rozšířené Win32 cesty (delší než MAX_PATH i UNC cesty) napříč celou aplikací i pluginy.
- **Inteligentní plánování Copy/Move:** Možnost sekvenčního i paralelního přenosu s detekcí kolizí a samostatnými limity pro SSD/NVMe úložiště.
- **Přenosy mezi pluginy a archivy:** Přímé kopírování mezi FS pluginy (SFTP, GDrive, S3, SharePoint) a archivy; funkce `Shift+F5` pro kopírování do více vybraných složek.
- **Detekce archivů (`Ctrl+PgDown`):** Otevření archivů i v případě chybějící nebo nesprávné přípony.
- **Katalogy DiskDir a seznamy souborů:** Tvorba rekurzivních seznamů souborů a podpora formátu katalogů DiskDir kompatibilního s Total Commanderem.

### Uživatelské rozhraní a panely
- **Záložky (Tabs) a samostatná okna:** Podpora více záložek na panel, odepínání záložek do samostatných oken (detached tabs), uzamykání záložek a perzistentní historie.
- **Tmavý režim (Dark Mode):** Podpora experimentálního tmavého schématu pro všechna okna, dialogy a zúčastněné pluginy.
- **Per-Monitor V2 DPI Awareness:** Ostré vykreslování písma, dialogů a ikon na různých monitorech a měřítkách bez nutnosti restartu.
- **Stromové zobrazení (Tree View):** Dokovatelný i plovoucí synchronizovaný strom složek.
- **Sloupce Průzkumníka:** Rozšířené vlastnosti, řazení a editace tagů přímo v panelu.

### Prohlížeče a rozšíření
- **Interní prohlížeč (F3):** Rychlé prohlížení textových a binárních souborů, Unicode podpora, zobrazení čísel řádků a režim sledování logů (Log View Mode).
- **Prism & WebView2 Prohlížeč:** Zvýraznění syntaxe kódu, vykreslování HTML, Markdownu, SVG, PDF a moderních formátů obrázků. Integrované celotextové vyhledávání napříč virtualizovaným textem, navigace F3 / Shift+F3, napojení na dialog Hledat a optimalizovaný rychlý start.
- **PictView:** Prohlížeč obrázků s podporou WIC i nativních dekodérů, 3D náhledy STL a generování miniatur.
- **Platforma Salamatrix:** Skriptování a tvorba rozšíření v JavaScriptu, Pythonu, PowerShellu, PHP a Lua.

---

## 🛠️ Sestavení projektu

Projekt lze sestavit pomocí Microsoft Visual Studio (verze 2022 nebo novější):
- Otevřete řešení `src/vcxproj/salamand.sln`.
- Zvolte konfiguraci `Release` a platformu `x64`.
- Sestavte řešení (`Build Solution`).

---

## 📄 Licence

Projekt je šířen pod licencí **GPL-2.0-or-later**.
Informace o licencích třetích stran naleznete v souboru [doc/third_party.md](doc/third_party.md).
