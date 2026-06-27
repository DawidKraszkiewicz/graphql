# Pokemon GraphQL API

Python + Strawberry + FastAPI + PostgreSQL demo pokazujące GraphQL vs REST.

## Stack

- **Strawberry** — GraphQL
- **FastAPI** — web framework
- **SQLAlchemy** — ORM
- **PostgreSQL** — baza danych
- **PokeAPI** — źródło danych (darmowe, bez klucza)

## Tabele

```
generations ← species → pokemon → pokemon_types     → types
                                 → pokemon_abilities → abilities
                                 → pokemon_moves     → moves → types
```

---

## Uruchomienie

```bash
docker compose up --build
```

Pierwsze uruchomienie seeduje ~151 pokemonów z PokeAPI — trwa ok. 3-5 minut.
API wstaje dopiero po zakończeniu seedowania.

Kolejne uruchomienia są natychmiastowe (baza już wypełniona):

```bash
docker compose up
```

### Reset bazy

```bash
docker compose down -v
docker compose up --build
```

---

## Endpointy

| URL | Opis |
|-----|------|
| http://localhost:8000/graphql | GraphQL playground (GraphiQL) |
| http://localhost:8000/health | Health check |

---

## Wysyłanie requestów

GraphQL zawsze używa **POST** na endpoint `/graphql` z body w JSON.

### Postman

1. Metoda: **POST**
2. URL: `http://localhost:8000/graphql`
3. Zakładka **Headers** → `Content-Type: application/json`
4. Zakładka **Body → GraphQL** → wklej query

### curl

Podstawowy format:

```bash
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ tutaj_query }"}' \
  | python -m json.tool
```

---

## Przykładowe zapytania — curl

### Jeden pokemon z pełnymi danymi

```bash
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ pokemon(name: \"pikachu\") { name baseHp baseAttack baseSpeed spriteUrl types { name } abilities { name effect } moves { name power pp damageClass } species { isLegendary captureRate color generation { name region } } } }"}' \
  | python -m json.tool
```

### Pokemon po ID

```bash
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ pokemon(id: 6) { name baseAttack types { name } } }"}' \
  | python -m json.tool
```

### Lista fire-type pokemonów

```bash
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ pokemons(typeName: \"fire\", limit: 10) { name baseAttack types { name } } }"}' \
  | python -m json.tool
```

### Legendarne pokemony

```bash
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ pokemons(isLegendary: true) { name baseHp species { color generation { name } } } }"}' \
  | python -m json.tool
```

### Paginacja — druga strona water-type

```bash
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ pokemons(typeName: \"water\", limit: 10, offset: 10) { name baseAttack baseDefense } }"}' \
  | python -m json.tool
```

### Liczba pokemonów per typ

```bash
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ pokemonCountByType { typeName count } }"}' \
  | python -m json.tool
```

### Fizyczne fire-type ruchy

```bash
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ moves(typeName: \"fire\", damageClass: \"physical\", limit: 10) { name power accuracy pp } }"}' \
  | python -m json.tool
```

### Wszystkie generacje ze statystykami

```bash
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ generations { name region speciesCount } }"}' \
  | python -m json.tool
```

### Trzy query w jednym requeście (aliasy — niemożliwe w REST)

```bash
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ special: moves(damageClass: \"special\", limit: 5) { name power typeName } physical: moves(damageClass: \"physical\", limit: 5) { name power typeName } status: moves(damageClass: \"status\", limit: 5) { name pp typeName } }"}' \
  | python -m json.tool
```

---

## Przykładowe zapytania — GraphQL (Postman / GraphiQL)

### Pełne dane jednego pokemona

```graphql
{
  pokemon(name: "mewtwo") {
    name
    baseHp
    baseAttack
    baseDefense
    baseSpeed
    spriteUrl
    types { name }
    abilities { name effect }
    moves { name power pp damageClass typeName }
    species {
      isLegendary
      isMythical
      captureRate
      color
      generation { name region }
    }
  }
}
```

### Filtrowanie i paginacja

```graphql
{
  pokemons(typeName: "water", limit: 10, offset: 10) {
    id
    name
    baseAttack
    baseDefense
    types { name }
  }
}
```

### Wszystkie generacje

```graphql
{
  generations {
    name
    region
    speciesCount
  }
}
```

### Typy z zagnieżdżonymi pokemonami

```graphql
{
  types {
    name
    pokemon {
      name
      baseAttack
      baseSpeed
    }
  }
}
```

### Trzy query w jednym requeście (aliasy)

```graphql
{
  special: moves(damageClass: "special", limit: 5) {
    name
    power
    typeName
  }
  physical: moves(damageClass: "physical", limit: 5) {
    name
    power
    typeName
  }
  status: moves(damageClass: "status", limit: 5) {
    name
    pp
    typeName
  }
}
```

---

## GraphQL vs REST — kluczowa różnica

Żeby pobrać jednego pokemona z typami, abilities i movami w REST potrzebujesz:

```
GET /pokemon/pikachu
GET /ability/static
GET /ability/lightning-rod
GET /move/thunder-shock
GET /move/quick-attack
... (N+1 requestów)
```

W GraphQL — **jeden request**, wybierasz dokładnie które pola chcesz.
