import json
from curl_cffi import requests
from bs4 import BeautifulSoup
import re

urls = [
    "https://aniagotuje.pl/przepis/butter-chicken",
    "https://www.kwestiasmaku.com/przepis/wielkanocny-zur-na-wedzonce",
    "https://www.kwestiasmaku.com/przepis/kotlet-de-volaille-z-mielonego-miesa-drobiowego",
    "https://www.kwestiasmaku.com/przepis/ciasto-truskawkowa-chmurka",
    "https://aniagotuje.pl/przepis/quesadilla",
    "https://aniagotuje.pl/przepis/kurczak-z-ryzem",
    "https://jadlonomia.com/przepisy/domowa-bezglutenowa-granola/",
    "https://mojewypieki.com/przepis/sernik-pistacjowy-z-biala-czekolada",
    "https://www.przepisy.pl/przepis/lazania-z-miesem-mielonym-i-szpinakiem",
    "https://smaker.pl/przepisy-salatki/przepis-najlepsza-salatka-na-wielkanoc,2070088,smaker.html"
]

all_ingredients = set()

def extract_from_json_ld(soup):
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            if not script.string:
                continue
            data = json.loads(script.string)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                if "@graph" in item:
                    for sub_item in item["@graph"]:
                        if isinstance(sub_item, dict) and sub_item.get("@type") == "Recipe":
                            return sub_item.get("recipeIngredient", [])
                if isinstance(item, dict) and item.get("@type") == "Recipe":
                    ingredients = item.get("recipeIngredient", [])
                    return [ingredients] if isinstance(ingredients, str) else ingredients
        except (json.JSONDecodeError, AttributeError):
            continue
    return []

for url in urls:
    print(f"\n{'='*60}\nPrzetwarzam: {url}\n{'-'*60}")
    try:
        response = requests.get(url, impersonate="chrome120", timeout=15)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, 'html.parser')
        extracted_texts = []
        
        json_ingredients = extract_from_json_ld(soup)
        
        if json_ingredients:
            print(f"[METODA] Sukces: Znaleziono strukturę JSON-LD.")
            extracted_texts.extend(json_ingredients)
        else:
            print(f"[METODA] Brak JSON-LD. Fallback do parsowania HTML...")
            
            if "jadlonomia.com" in url:
                # Rozwiązanie na podstawie Twoich ustaleń - szukamy div.recipecard
                recipe_cards = soup.select('.recipecard')
                if recipe_cards:
                    for card in recipe_cards:
                        for p in card.find_all('p'):
                            # Rozbijamy tag <p> po miękkich enterach
                            for line in p.get_text(separator="\n").split("\n"):
                                if line.strip():
                                    extracted_texts.append(line.strip())
                else:
                    # Na wypadek jeszcze innych starych wpisów - szukanie paragrafów po tytule "składniki"
                    headings = soup.find_all(string=re.compile(r'składniki', re.IGNORECASE))
                    for heading in headings:
                        parent = heading.find_parent()
                        if parent:
                            for sibling in parent.find_next_siblings(['p', 'ul']):
                                if sibling.name == 'ul':
                                    for li in sibling.find_all('li'):
                                        extracted_texts.append(li.get_text(strip=True))
                                elif sibling.name == 'p':
                                    for line in sibling.get_text(separator="\n").split("\n"):
                                        if line.strip():
                                            extracted_texts.append(line.strip())

            elif "mojewypieki.com" in url:
                # Dodałem wskazaną przez Ciebie klasę .article__content
                items = soup.select('.article__content ul li, .article-recipe__ingredients li, .recipe-box ul li')
                for item in items:
                    extracted_texts.append(item.get_text(separator=" ", strip=True))

            elif "aniagotuje.pl" in url:
                items = soup.select('.recipe-ing-list li')
                for item in items: extracted_texts.append(item.get_text(separator=" ", strip=True))
                
            elif "kwestiasmaku.com" in url:
                items = soup.select('.field-name-field-skladniki li')
                for item in items: extracted_texts.append(item.get_text(separator=" ", strip=True))
                
            elif "przepisy.pl" in url:
                items = soup.select('.ingredients-list-content li, .ingredient-name')
                for item in items: extracted_texts.append(item.get_text(separator=" ", strip=True))
                
            elif "smaker.pl" in url:
                items = soup.select('.ingredients-list li, [itemprop="recipeIngredient"]')
                for item in items: extracted_texts.append(item.get_text(separator=" ", strip=True))

        print(f"\n[ANALIZA SKŁADNIKÓW]:")
        if not extracted_texts:
            print("  ❌ NIE ZNALEZIONO ŻADNYCH SUROWYCH TEKSTÓW! (Sprawdź selektory CSS)")
            
        for text in extracted_texts:
            clean_text = " ".join(text.split())
            
            if not clean_text:
                continue
                
            if len(clean_text) <= 2:
                print(f"  🔴 ODRZUCONO (Za krótkie, {len(clean_text)} znaków): '{clean_text}'")
                continue
                
            if len(clean_text) >= 250:
                print(f"  🔴 ODRZUCONO (Za długie, {len(clean_text)} znaków): '{clean_text[:50]}...'")
                continue
                
            # Bardziej precyzyjna czarna lista, by nie ucinała prawdziwych składników
            blacklist_exact = ["składniki", "składniki:", "dodaj komentarz", "zobacz wpis", "poprzedni wpis", "następny wpis"]
            if clean_text.lower() in blacklist_exact:
                print(f"  🔴 ODRZUCONO (Czarna lista): '{clean_text}'")
                continue
                
            print(f"  🟢 ZAAKCEPTOWANO: '{clean_text}'")
            all_ingredients.add(clean_text)
                
    except Exception as e:
        print(f" BŁĄD KRYTYCZNY przy {url}: {e}")

file_path = "brudne_skladniki.txt"
with open(file_path, "w", encoding="utf-8") as f:
    for ing in sorted(all_ingredients):
        f.write(ing + "\n")

print(f"\n{'='*60}\nGotowe! Zapisano {len(all_ingredients)} unikalnych wyrażeń w pliku {file_path}")