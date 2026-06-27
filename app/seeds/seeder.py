"""
Fetches data from PokeAPI and seeds the database.
Run once on startup if tables are empty.
"""

import httpx
import logging
from sqlalchemy.orm import Session
from app import models

log = logging.getLogger(__name__)

BASE = "https://pokeapi.co/api/v2"
POKEMON_LIMIT = 151  # first generation; bump to 386/493/... for more


def _get(client: httpx.Client, url: str) -> dict:
    r = client.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


# ── Generations ───────────────────────────────────────────────────────────────

def seed_generations(db: Session, client: httpx.Client) -> dict[int, models.Generation]:
    data = _get(client, f"{BASE}/generation?limit=9")
    gen_map: dict[int, models.Generation] = {}
    for item in data["results"]:
        detail = _get(client, item["url"])
        gen_id = detail["id"]
        region = detail["main_region"]["name"] if detail.get("main_region") else None
        obj = db.get(models.Generation, gen_id)
        if not obj:
            obj = models.Generation(id=gen_id, name=detail["name"], region=region)
            db.add(obj)
        gen_map[gen_id] = obj
    db.commit()
    log.info("Generations seeded: %d", len(gen_map))
    return gen_map


# ── Types ─────────────────────────────────────────────────────────────────────

def seed_types(db: Session, client: httpx.Client) -> dict[str, models.Type]:
    data = _get(client, f"{BASE}/type?limit=30")
    type_map: dict[str, models.Type] = {}
    for item in data["results"]:
        detail = _get(client, item["url"])
        obj = db.get(models.Type, detail["id"])
        if not obj:
            obj = models.Type(id=detail["id"], name=detail["name"])
            db.add(obj)
        type_map[detail["name"]] = obj
    db.commit()
    log.info("Types seeded: %d", len(type_map))
    return type_map


# ── Abilities ─────────────────────────────────────────────────────────────────

def seed_abilities(db: Session, client: httpx.Client) -> dict[str, models.Ability]:
    data = _get(client, f"{BASE}/ability?limit=300")
    ability_map: dict[str, models.Ability] = {}
    for item in data["results"]:
        detail = _get(client, item["url"])
        effect_text = ""
        for entry in detail.get("effect_entries", []):
            if entry["language"]["name"] == "en":
                effect_text = entry["short_effect"]
                break
        obj = db.get(models.Ability, detail["id"])
        if not obj:
            obj = models.Ability(id=detail["id"], name=detail["name"], effect=effect_text[:500])
            db.add(obj)
        ability_map[detail["name"]] = obj
    db.commit()
    log.info("Abilities seeded: %d", len(ability_map))
    return ability_map


# ── Moves ─────────────────────────────────────────────────────────────────────

def seed_moves(
    db: Session,
    client: httpx.Client,
    type_map: dict[str, models.Type],
    limit: int = 200,
) -> dict[str, models.Move]:
    data = _get(client, f"{BASE}/move?limit={limit}")
    move_map: dict[str, models.Move] = {}
    for item in data["results"]:
        detail = _get(client, item["url"])
        type_obj = type_map.get(detail["type"]["name"])
        obj = db.get(models.Move, detail["id"])
        if not obj:
            obj = models.Move(
                id=detail["id"],
                name=detail["name"],
                power=detail.get("power"),
                pp=detail.get("pp"),
                accuracy=detail.get("accuracy"),
                damage_class=detail["damage_class"]["name"] if detail.get("damage_class") else None,
                type=type_obj,
            )
            db.add(obj)
        move_map[detail["name"]] = obj
    db.commit()
    log.info("Moves seeded: %d", len(move_map))
    return move_map


# ── Pokemon + Species ─────────────────────────────────────────────────────────

def seed_pokemon(
    db: Session,
    client: httpx.Client,
    type_map: dict[str, models.Type],
    ability_map: dict[str, models.Ability],
    move_map: dict[str, models.Move],
):
    data = _get(client, f"{BASE}/pokemon?limit={POKEMON_LIMIT}")
    for item in data["results"]:
        detail = _get(client, item["url"])
        pokemon_id = detail["id"]

        if db.get(models.Pokemon, pokemon_id):
            continue

        # base stats
        stats = {s["stat"]["name"]: s["base_stat"] for s in detail.get("stat", detail.get("stats", []))}

        sprite = None
        sprites = detail.get("sprites", {})
        sprite = sprites.get("front_default") or sprites.get("other", {}).get("official-artwork", {}).get("front_default")

        poke = models.Pokemon(
            id=pokemon_id,
            name=detail["name"],
            base_experience=detail.get("base_experience"),
            height=detail.get("height"),
            weight=detail.get("weight"),
            base_hp=stats.get("hp"),
            base_attack=stats.get("attack"),
            base_defense=stats.get("defense"),
            base_speed=stats.get("speed"),
            sprite_url=sprite,
        )

        # types
        for t in detail.get("types", []):
            type_obj = type_map.get(t["type"]["name"])
            if type_obj and type_obj not in poke.types:
                poke.types.append(type_obj)

        # abilities
        for a in detail.get("abilities", []):
            ab = ability_map.get(a["ability"]["name"])
            if ab and ab not in poke.abilities:
                poke.abilities.append(ab)

        # moves (cap at 20 per pokemon to keep seeding fast)
        for m in detail.get("moves", [])[:20]:
            mv = move_map.get(m["move"]["name"])
            if mv and mv not in poke.moves:
                poke.moves.append(mv)

        db.add(poke)
        db.flush()

        # species
        species_url = detail.get("species", {}).get("url")
        if species_url:
            try:
                sp_detail = _get(client, species_url)
                gen_id = sp_detail["generation"]["id"] if sp_detail.get("generation") else None
                color = sp_detail.get("color", {}).get("name")
                shape = sp_detail.get("shape", {}).get("name") if sp_detail.get("shape") else None

                existing_species = db.get(models.Species, sp_detail["id"])
                if not existing_species:
                    species = models.Species(
                        id=sp_detail["id"],
                        name=sp_detail["name"],
                        capture_rate=sp_detail.get("capture_rate"),
                        base_happiness=sp_detail.get("base_happiness"),
                        is_legendary=sp_detail.get("is_legendary", False),
                        is_mythical=sp_detail.get("is_mythical", False),
                        color=color,
                        shape=shape,
                        pokemon_id=pokemon_id,
                        generation_id=gen_id,
                    )
                    db.add(species)
            except Exception as e:
                log.warning("Could not fetch species for %s: %s", detail["name"], e)

        db.commit()
        log.info("Seeded pokemon: %s (%d)", detail["name"], pokemon_id)


# ── Entry point ───────────────────────────────────────────────────────────────

def run_seed(db: Session):
    if db.query(models.Pokemon).count() > 0:
        log.info("Database already seeded — skipping.")
        return

    log.info("Starting seed from PokeAPI (limit=%d pokemon)...", POKEMON_LIMIT)
    with httpx.Client() as client:
        gen_map = seed_generations(db, client)
        type_map = seed_types(db, client)
        ability_map = seed_abilities(db, client)
        move_map = seed_moves(db, client, type_map)
        seed_pokemon(db, client, type_map, ability_map, move_map)

    log.info("Seed complete.")
