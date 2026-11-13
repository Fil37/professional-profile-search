# Agent de recherche de profils professionnels publics

Application Streamlit et CLI qui recherchent des profils LinkedIn publics à partir de critères explicites. Ollama/Llama extrait les critères d'une demande en langage naturel; les résultats viennent de moteurs de recherche et ne sont jamais complétés par le modèle.

## Recherche et validation

Les fournisseurs sont interrogés dans cet ordre : DDGS, Brave, Exa, puis SerpApi. Les fournisseurs nécessitant une clé sont ignorés lorsqu'elle n'est pas configurée. SerpApi n'est appelé que si les résultats précédents n'offrent pas de candidat avec un score d'au moins 65/100 et une correspondance du nom.

Chaque résultat conserve son titre, son URL, son extrait et ses sources. Le score indique la part des critères demandés corroborée par le titre ou l'extrait; les critères non corroborés sont listés comme non vérifiés. Un score n'est pas une confirmation d'identité.

## Modules

- `keyword_extractor.py` converts a request into explicit Pydantic criteria.
- `profile_search.py` coordinates DDGS, Brave, Exa and SerpApi in order.
- `profile_validation.py` scores evidence in result titles and snippets.
- `streamlit_app.py` and `main.py` expose the UI and CLI.
- `test_profile_search.py` tests the validation and fallback behavior offline.

## Prérequis

- Python 3.10 ou supérieur
- Ollama installé et démarré
- Le modèle défini par `OLLAMA_MODEL` téléchargé localement (par défaut `llama3.1:8b`)

## Installation

Depuis ce dossier :

```bash
python -m venv .venv
source .venv/bin/activate  # Windows : .venv\Scripts\activate
python -m pip install -e ".[dev]"
cp .env.example .env
ollama pull llama3.1:8b
```

## Lancer l'interface Streamlit

```bash
streamlit run streamlit_app.py
```

Le modèle Ollama doit être démarré localement.

## Utiliser le CLI

```bash
python main.py "Je cherche Franck Essome, ingénieur chez BNBXTECH à Orsay en France"
```

Le modèle Ollama et son URL se configurent dans `.env` avec `OLLAMA_MODEL` et `OLLAMA_BASE_URL`. Les clés optionnelles `BRAVE_SEARCH_API_KEY`, `EXA_API_KEY` et `SERPAPI_API_KEY` activent les fournisseurs de secours correspondants. Ne publiez jamais votre fichier `.env`.

## Tests

```bash
pytest
```

## Limites et précautions

- L'outil effectue une recherche web et ne garantit ni l'exhaustivité ni l'exactitude de l'identité trouvée. Les homonymes doivent être vérifiés par une personne.
- Seules les pages publiques renvoyées par le moteur sont utilisées. Le projet ne se connecte pas à LinkedIn, ne contourne pas de contrôle d'accès et ne collecte pas de données privées.
- Respecter les conditions d'utilisation des services interrogés et les règles applicables à la protection des données. Ne pas utiliser les résultats pour prendre automatiquement une décision concernant une personne.
- Les noms et les autres critères sont comparés aux titres et extraits fournis par les moteurs; une information absente est signalée comme non vérifiée.

## Évolutions envisagées

- Ajouter d'autres outils de recherche derrière la même interface.
- Conserver les sources et dates de consultation pour rendre les résultats auditables.
- Ajouter d'autres fournisseurs de recherche derrière la même interface.