import json
from litellm import completion
from ingredients_list import all_ingredients
from dotenv import load_dotenv

load_dotenv()

# --- KONFIGURACJA BAZOWA ---
# Wartości wyciągnięte z Twojego przykładowego rekordu
AUTOMATION_TYPE = "FOOD_ALIAS"
ORDER_VALUE = 1000
CREATED_BY_ID = 1
SPACE_ID = 1

# Przykładowa lista Twoich 370 składników (najlepiej pobrać je wprost z bazy osobnym zapytaniem)
# Zapisane z wielkiej litery, tak jak główny składnik "Banan" w Twoim przykładzie
base_ingredients = all_ingredients

sql_statements = []

def get_declensions(word):
    """Pobiera odmienione formy słowa za pomocą LLM przez OpenRouter."""
    
    # Podajemy słowo bazowe małymi literami do promptu, aby uniknąć dziwnych kapitalizacji
    word_lower = word.lower()
    
    prompt = f"""
    Zwróć najczęstsze odmienione formy podanego polskiego składnika spożywczego (np. mianownik l.mn., dopełniacz l.p. i l.mn.), które występują w przepisach.
    Wynik zwróć JAKO CZYSTY JSON w formacie: {{"forms": ["forma1", "forma2", "forma3"]}}
    Zwróć TYLKO małe litery.
    Słowo bazowe: {word_lower}
    """
    
    try:
        # np. openrouter/google/gemini-3.1-flash-lite lub openrouter/openai/gpt-4o-mini
        response = completion(
            model="openrouter/x-ai/grok-4.1-fast", 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        content = json.loads(response.choices[0].message.content)
        forms = content.get("forms", [])
        
        # Zwracamy unikalne formy, odrzucając formę bazową jeśli model ją zwrócił
        return list(set([f for f in forms if f != word_lower]))
        
    except Exception as e:
        print(f"Błąd przetwarzania dla {word}: {e}")
        return []

# --- GENEROWANIE ZAPYTAŃ ---
for base_word in base_ingredients:
    variations = get_declensions(base_word)
    print(f"Pobrano formy dla '{base_word}': {variations}")
    
    for variation in variations:
        # Escapowanie pojedynczych cudzysłowów dla T-SQL / PostgreSQL
        safe_variation = variation.replace("'", "''")
        safe_base = base_word.replace("'", "''")
        
        # Formatowanie kolumny name zbieżne z Twoim przykładem: "Scal banany kiść -> Banan"
        name_field = f"Scal {safe_variation} -> {safe_base}"
        
        # Budowanie pojedynczego rekordu VALUES
        # description i param_3 są puste ('')
        sql_value = (
            f"('{AUTOMATION_TYPE}', '{name_field}', '', '{safe_variation}', "
            f"'{safe_base}', '', {ORDER_VALUE}, false, NOW(), NOW(), {CREATED_BY_ID}, {SPACE_ID})"
        )
        sql_statements.append(sql_value)

# --- SKŁADANIE I ZAPIS SQL ---
final_sql = f"""
INSERT INTO public.cookbook_automation 
(type, name, description, param_1, param_2, param_3, "order", disabled, updated_at, created_at, created_by_id, space_id)
VALUES 
{",\n".join(sql_statements)};
"""

with open("tandoor_automations_insert.sql", "w", encoding="utf-8") as file:
    file.write(final_sql)

print(f"\nGotowe! Wygenerowano {len(sql_statements)} rekordów. Skrypt zapisany do tandoor_automations_insert.sql")