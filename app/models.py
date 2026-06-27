from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Table, Float
)
from sqlalchemy.orm import relationship
from app.database import Base

# ── Association tables ────────────────────────────────────────────────────────

pokemon_types = Table(
    "pokemon_types",
    Base.metadata,
    Column("pokemon_id", Integer, ForeignKey("pokemon.id"), primary_key=True),
    Column("type_id", Integer, ForeignKey("types.id"), primary_key=True),
)

pokemon_abilities = Table(
    "pokemon_abilities",
    Base.metadata,
    Column("pokemon_id", Integer, ForeignKey("pokemon.id"), primary_key=True),
    Column("ability_id", Integer, ForeignKey("abilities.id"), primary_key=True),
    Column("is_hidden", Boolean, default=False),
)

pokemon_moves = Table(
    "pokemon_moves",
    Base.metadata,
    Column("pokemon_id", Integer, ForeignKey("pokemon.id"), primary_key=True),
    Column("move_id", Integer, ForeignKey("moves.id"), primary_key=True),
)

# ── Core tables ───────────────────────────────────────────────────────────────

class Generation(Base):
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    region = Column(String(100))

    species = relationship("Species", back_populates="generation")


class Type(Base):
    __tablename__ = "types"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)

    pokemon = relationship("Pokemon", secondary=pokemon_types, back_populates="types")
    moves = relationship("Move", back_populates="type")


class Ability(Base):
    __tablename__ = "abilities"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    effect = Column(String(500))

    pokemon = relationship("Pokemon", secondary=pokemon_abilities, back_populates="abilities")


class Move(Base):
    __tablename__ = "moves"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    power = Column(Integer)
    pp = Column(Integer)
    accuracy = Column(Integer)
    damage_class = Column(String(50))  # physical / special / status

    type_id = Column(Integer, ForeignKey("types.id"))
    type = relationship("Type", back_populates="moves")

    pokemon = relationship("Pokemon", secondary=pokemon_moves, back_populates="moves")


class Pokemon(Base):
    __tablename__ = "pokemon"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    base_experience = Column(Integer)
    height = Column(Integer)   # decimetres
    weight = Column(Integer)   # hectograms
    base_hp = Column(Integer)
    base_attack = Column(Integer)
    base_defense = Column(Integer)
    base_speed = Column(Integer)
    sprite_url = Column(String(300))

    types = relationship("Type", secondary=pokemon_types, back_populates="pokemon")
    abilities = relationship("Ability", secondary=pokemon_abilities, back_populates="pokemon")
    moves = relationship("Move", secondary=pokemon_moves, back_populates="pokemon")
    species = relationship("Species", back_populates="pokemon", uselist=False)


class Species(Base):
    __tablename__ = "species"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    capture_rate = Column(Integer)
    base_happiness = Column(Integer)
    is_legendary = Column(Boolean, default=False)
    is_mythical = Column(Boolean, default=False)
    color = Column(String(50))
    shape = Column(String(50))

    pokemon_id = Column(Integer, ForeignKey("pokemon.id"), unique=True)
    generation_id = Column(Integer, ForeignKey("generations.id"))

    pokemon = relationship("Pokemon", back_populates="species")
    generation = relationship("Generation", back_populates="species")
