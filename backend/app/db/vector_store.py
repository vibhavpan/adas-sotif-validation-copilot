from sentence_transformers import SentenceTransformer
from sqlalchemy import Column, Integer, String
from pgvector.sqlalchemy import Vector
from app.db.database import Base, SessionLocal

# Free local embeddings (384 dimensions)
embedder = SentenceTransformer('all-MiniLM-L6-v2')

class ScenarioRequirement(Base):
    __tablename__ = "scenario_requirements"
    id = Column(Integer, primary_key=True, index=True)
    rule_text = Column(String)
    embedding = Column(Vector(384))

def add_requirement(text: str):
    db = SessionLocal()
    vector = embedder.encode(text).tolist()
    req = ScenarioRequirement(rule_text=text, embedding=vector)
    db.add(req)
    db.commit()
    db.close()
