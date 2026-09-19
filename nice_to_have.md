# Zásobník vylepšení (Nice-to-Have & Backlog) – Open Salamander: Samandarin

Tento dokument shromažďuje náměty na další vylepšení a optimalizace jádra správce souborů Samandarin.

---

## 💡 Náměty a plánovaná rozšíření

### 1. Asynchronní náhledy miniatur (Thumbnail Cache & Worker)
- **Popis**: Rozšíření generování miniatur do plně asynchronního vlákna na pozadí s mezipamětí na disku pro okamžité znovuzobrazení miniatur při návratu do složky.
- **Přínos**: Plynulé procházení složek s tisíci obrázků bez jakéhokoliv zaškubnutí panelu.

### 2. Sjednocená podpora hashování (Integrace Checksum přímo do vlastností a dialogů)
- **Popis**: Zobrazení MD5/SHA-1/SHA-256 souboru přímo na záložce vlastností souboru a možnost rychlého ověření proti schránce.
- **Přínos**: Pohodlné ověřování integrity stažených souborů a instalátorů.

### 3. Vylepšený dialog výběru cíle při kopírování mezi taby
- **Popis**: Při stisku F5 v detached okně nebo při více otevřených záložkách nabídnout rychlý přepínač cílové záložky (např. klávesou `Tab` nebo dropdownem přímo v dialogu).
- **Přínos**: Intuitivní přesouvání dat mezi libovolnou kombinací otevřených panelů a záložek.

### 4. Podpora virtuálních disků a kontejnerů (VHDX / ISO zápis)
- **Popis**: Možnost připojení a procházení obrazů disků VHD/VHDX a ISO s podporou extrakce i přidávání souborů.
- **Přínos**: Plnohodnotná práce s virtuálními disky bez nutnosti externích nástrojů.

### 5. Export a synchronizace nastavení přes cloud
- **Popis**: Možnost volitelného uložení a synchronizace přenosné konfigurace (`salamand.cfg`) na vybrané cloudové úložiště (GDrive, OneDrive, S3).
- **Přínos**: Konzistentní pracovní prostředí na všech počítačích uživatele.

### 6. Podpora regulárních výrazů a značky výskytů na posuvníku v Prism Text Vieweru
- **Popis**: Rozšíření vyhledávání v Prism Text Vieweru o regulární výrazy (Regex) a vizuální značky (markery) nalezených shod přímo na svislém posuvníku (scrollbar markery).
- **Přínos**: Rychlá vizuální orientace ve velkých zdrojových kódech a log souborech při ladění.

