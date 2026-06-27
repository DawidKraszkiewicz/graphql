# Example GraphQL Queries

Open GraphiQL at: http://localhost:8000/graphql

---

## 1. Fetch a single Pokémon with all relations in ONE request
```graphql
query {
  pokemon(name: "pikachu") {
    id
    name
    baseHp
    baseAttack
    baseSpeed
    spriteUrl
    types { name }
    abilities { name effect }
    moves { name power pp damageClass typeName }
    species {
      isLegendary
      captureRate
      color
      generation { name region }
    }
  }
}
```

---

## 2. List fire-type Pokémon (filtered, paginated)
```graphql
query {
  pokemons(typeName: "fire", limit: 10, offset: 0) {
    name
    baseAttack
    types { name }
  }
}
```

---

## 3. List legendary Pokémon
```graphql
query {
  pokemons(isLegendary: true) {
    name
    baseHp
    species { isLegendary isMythical generation { name } }
  }
}
```

---

## 4. Get all types + their Pokémon (nested — impossible cleanly in REST without N+1)
```graphql
query {
  types {
    name
    pokemon { name baseAttack }
  }
}
```

---

## 5. Count Pokémon per type
```graphql
query {
  pokemonCountByType {
    typeName
    count
  }
}
```

---

## 6. Physical moves of a specific type
```graphql
query {
  moves(typeName: "fire", damageClass: "physical", limit: 20) {
    name
    power
    accuracy
    pp
  }
}
```

---

## 7. All generations with species count
```graphql
query {
  generations {
    name
    region
    speciesCount
  }
}
```

---

## REST vs GraphQL — the key difference

With REST you'd need multiple requests to get what query #1 returns in one:
- GET /pokemon/pikachu
- GET /ability/static
- GET /ability/lightning-rod
- GET /move/thunder-shock
- GET /move/quick-attack
- ... etc

With GraphQL: one request, you pick exactly which fields you want.
