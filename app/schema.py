"""
GraphQL schema using Strawberry.
Demonstrates: nested resolvers, filtering, pagination, aggregates.
"""

from __future__ import annotations
import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import Optional, Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from app import models
from app.database import get_db


# ── GraphQL types ─────────────────────────────────────────────────────────────

@strawberry.type
class GenerationType:
    id: int
    name: str
    region: Optional[str]

    @strawberry.field
    def species_count(self, info: strawberry.types.Info) -> int:
        db: Session = info.context["db"]
        return db.query(models.Species).filter(models.Species.generation_id == self.id).count()


@strawberry.type
class TypeType:
    id: int
    name: str

    @strawberry.field
    def pokemon(self, info: strawberry.types.Info) -> list["PokemonType"]:
        db: Session = info.context["db"]
        type_obj = db.get(models.Type, self.id)
        return [_pokemon_to_gql(p) for p in type_obj.pokemon] if type_obj else []


@strawberry.type
class AbilityType:
    id: int
    name: str
    effect: Optional[str]


@strawberry.type
class MoveType:
    id: int
    name: str
    power: Optional[int]
    pp: Optional[int]
    accuracy: Optional[int]
    damage_class: Optional[str]
    type_name: str


@strawberry.type
class SpeciesType:
    id: int
    name: str
    capture_rate: Optional[int]
    base_happiness: Optional[int]
    is_legendary: bool
    is_mythical: bool
    color: Optional[str]
    shape: Optional[str]
    generation: Optional[GenerationType]


@strawberry.type
class PokemonType:
    id: int
    name: str
    base_experience: Optional[int]
    height: Optional[int]
    weight: Optional[int]
    base_hp: Optional[int]
    base_attack: Optional[int]
    base_defense: Optional[int]
    base_speed: Optional[int]
    sprite_url: Optional[str]
    types: list[TypeType]
    abilities: list[AbilityType]
    moves: list[MoveType]
    species: Optional[SpeciesType]


@strawberry.type
class TypeCount:
    type_name: str
    count: int


# ── Conversion helpers ────────────────────────────────────────────────────────

def _gen_to_gql(g: models.Generation) -> GenerationType:
    return GenerationType(id=g.id, name=g.name, region=g.region)


def _type_to_gql(t: models.Type) -> TypeType:
    return TypeType(id=t.id, name=t.name)


def _ability_to_gql(a: models.Ability) -> AbilityType:
    return AbilityType(id=a.id, name=a.name, effect=a.effect)


def _move_to_gql(m: models.Move) -> MoveType:
    return MoveType(
        id=m.id,
        name=m.name,
        power=m.power,
        pp=m.pp,
        accuracy=m.accuracy,
        damage_class=m.damage_class,
        type_name=m.type.name if m.type else "unknown",
    )


def _species_to_gql(s: models.Species | None) -> SpeciesType | None:
    if not s:
        return None
    gen = _gen_to_gql(s.generation) if s.generation else None
    return SpeciesType(
        id=s.id,
        name=s.name,
        capture_rate=s.capture_rate,
        base_happiness=s.base_happiness,
        is_legendary=s.is_legendary,
        is_mythical=s.is_mythical,
        color=s.color,
        shape=s.shape,
        generation=gen,
    )


def _pokemon_to_gql(p: models.Pokemon) -> PokemonType:
    return PokemonType(
        id=p.id,
        name=p.name,
        base_experience=p.base_experience,
        height=p.height,
        weight=p.weight,
        base_hp=p.base_hp,
        base_attack=p.base_attack,
        base_defense=p.base_defense,
        base_speed=p.base_speed,
        sprite_url=p.sprite_url,
        types=[_type_to_gql(t) for t in p.types],
        abilities=[_ability_to_gql(a) for a in p.abilities],
        moves=[_move_to_gql(m) for m in p.moves],
        species=_species_to_gql(p.species),
    )


# ── Query ─────────────────────────────────────────────────────────────────────

@strawberry.type
class Query:

    @strawberry.field(description="Fetch a single Pokémon by ID or name.")
    def pokemon(
        self,
        info: strawberry.types.Info,
        id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> Optional[PokemonType]:
        db: Session = info.context["db"]
        if id is not None:
            p = db.get(models.Pokemon, id)
        elif name:
            p = db.query(models.Pokemon).filter(models.Pokemon.name == name.lower()).first()
        else:
            return None
        return _pokemon_to_gql(p) if p else None

    @strawberry.field(description="List Pokémon with optional filtering and pagination.")
    def pokemons(
        self,
        info: strawberry.types.Info,
        type_name: Optional[str] = None,
        is_legendary: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[PokemonType]:
        db: Session = info.context["db"]
        q = db.query(models.Pokemon)
        if type_name:
            q = q.join(models.pokemon_types).join(models.Type).filter(
                models.Type.name == type_name.lower()
            )
        if is_legendary is not None:
            q = q.join(models.Species).filter(models.Species.is_legendary == is_legendary)
        return [_pokemon_to_gql(p) for p in q.offset(offset).limit(limit).all()]

    @strawberry.field(description="List all types.")
    def types(self, info: strawberry.types.Info) -> list[TypeType]:
        db: Session = info.context["db"]
        return [_type_to_gql(t) for t in db.query(models.Type).all()]

    @strawberry.field(description="Fetch a type by name.")
    def type(self, info: strawberry.types.Info, name: str) -> Optional[TypeType]:
        db: Session = info.context["db"]
        t = db.query(models.Type).filter(models.Type.name == name.lower()).first()
        return _type_to_gql(t) if t else None

    @strawberry.field(description="List abilities.")
    def abilities(
        self,
        info: strawberry.types.Info,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AbilityType]:
        db: Session = info.context["db"]
        return [
            _ability_to_gql(a)
            for a in db.query(models.Ability).offset(offset).limit(limit).all()
        ]

    @strawberry.field(description="List moves, optionally filtered by type or damage class.")
    def moves(
        self,
        info: strawberry.types.Info,
        type_name: Optional[str] = None,
        damage_class: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MoveType]:
        db: Session = info.context["db"]
        q = db.query(models.Move)
        if type_name:
            q = q.join(models.Type).filter(models.Type.name == type_name.lower())
        if damage_class:
            q = q.filter(models.Move.damage_class == damage_class.lower())
        return [_move_to_gql(m) for m in q.offset(offset).limit(limit).all()]

    @strawberry.field(description="List all generations.")
    def generations(self, info: strawberry.types.Info) -> list[GenerationType]:
        db: Session = info.context["db"]
        return [_gen_to_gql(g) for g in db.query(models.Generation).all()]

    @strawberry.field(description="List legendary Pokémon species.")
    def legendary_species(self, info: strawberry.types.Info) -> list[SpeciesType]:
        db: Session = info.context["db"]
        return [
            _species_to_gql(s)
            for s in db.query(models.Species).filter(models.Species.is_legendary == True).all()
        ]

    @strawberry.field(description="Pokémon count grouped by type (descending).")
    def pokemon_count_by_type(self, info: strawberry.types.Info) -> list[TypeCount]:
        db: Session = info.context["db"]
        from sqlalchemy import func
        rows = (
            db.query(models.Type.name, func.count(models.pokemon_types.c.pokemon_id))
            .join(models.pokemon_types, models.Type.id == models.pokemon_types.c.type_id)
            .group_by(models.Type.name)
            .order_by(func.count(models.pokemon_types.c.pokemon_id).desc())
            .all()
        )
        return [TypeCount(type_name=r[0], count=r[1]) for r in rows]


# ── Schema + Router ───────────────────────────────────────────────────────────

schema = strawberry.Schema(query=Query)


async def get_context(db: Session = Depends(get_db)):
    return {"db": db}


graphql_router = GraphQLRouter(schema, context_getter=get_context)
