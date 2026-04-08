# Tandoor Dodatki

Zestaw narzędzi do automatyzacji pracy z przepisami w aplikacji Tandoor (open-source recipe manager).

## Opis

Repozytorium zawiera skrypty Pythonowe do:

1. **Scrapowania składników** z polskich blogów kulinarnych
2. **Generowania odmian gramatycznych** nazw składników za pomocą LLM
3. **Tworzenia gotowych zapytań SQL** do wstawienia automatyzacji do bazy Tandoor
4. **Pobierania dokumentacji** Tandoor z GitHub i oficjalnej strony

## Struktura plików

| Plik                             | Opis                                                |
| -------------------------------- | --------------------------------------------------- |
| `main.py`                        | Główny skrypt - generuje SQL z odmianami składników |
| `blog_scraper.py`                | Scraper pobierający składniki z blogów kulinarnych  |
| `docs_and_repo_scrap.py`         | Pobieranie dokumentacji i release notes z Tandoor   |
| `ingredients_list.py`            | Lista bazowych składników (~370 pozycji)            |
| `brudne_skladniki.txt`           | Surowe dane wyjściowe ze scrapera                   |
| `tandoor_automations_insert.sql` | Wygenerowane zapytanie SQL                          |

## Wymagania

```
Python 3.12+
curl-cffi
beautifulsoup4
litellm
python-dotenv
requests
```

Instalacja:

```bash
pip install curl-cffi beautifulsoup4 litellm python-dotenv requests
```

## Konfiguracja

Utwórz plik `.env` z kluczem API OpenRouter:

```
OPENROUTER_API_KEY=your_api_key_here
```

## Użycie

### Blog Scraper

```bash
python blog_scraper.py
```

Pobiera składniki z predefiniowanych polskich blogów kulinarnych:

- aniagotuje.pl
- kwestiasmaku.com
- jadlonomia.com
- mojewypieki.com
- przepisy.pl
- smaker.pl

Wyniki zapisuje do `brudne_skladniki.txt`.

### Dokumentacja Tandoor

```bash
python docs_and_repo_scrap.py
```

Pobiera:

1. Release notes z GitHub API (`vabene1111/recipes`)
2. Pliki .md z folderu `/docs` w repozytorium
3. Treść z oficjalnej strony docs.tandoor.dev

Wyniki:

- `tandoor_releases.txt` - historia wydań
- `tandoor_docs_summary.txt` - dokumentacja z repo
- `tandoor_website_docs.txt` - treść ze strony

### Generator automatyzacji

```bash
python main.py
```

Dla każdego składnika z `ingredients_list.py`:

1. Wywołuje LLM (Grok 4.1 Fast przez OpenRouter)
2. Generuje odmiany gramatyczne (mianownik l.mn., dopełniacz l.p. i l.mn.)
3. Tworzy rekordy automatyzacji typu `FOOD_ALIAS`
4. Zapisuje gotowe zapytanie SQL do `tandoor_automations_insert.sql`

### Wstawienie do bazy

Po wygenerowaniu pliku SQL, wstaw dane do bazy Tandoor:

```sql
-- Przed uruchomieniem sprawdź dane w pliku!
psql -h localhost -U tandoor -d tandoor -f tandoor_automations_insert.sql
```

## Architektura

- **blog_scraper.py**: Obsługuje wiele formatów HTML oraz JSON-LD. Dla każdego blogu używa dedykowanych selektorów CSS.
- **main.py**: Używa `litellm` do komunikacji z dowolnym modelem LLM (domyślnie x-ai/grok-4.1-fast). Generuje semantycznie poprawne odmiany gramatyczne dla polskich składników.

## Licencja

MIT

---

## TODO / Pomysły
