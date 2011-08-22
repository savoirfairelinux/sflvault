"""SQLAlchemy Metadata and Session object"""
from sqlalchemy import MetaData

__all__ = ['engine', 'metadata', 'Session']

# SQLAlchemy database engine.  Updated by model.init_model().
engine = None

# SQLAlchemy session manager.  Updated by model.init_model().
Session = None

# Global metadata. If you have multiple databases with overlapping table 
# names, you'll need a metadata for each database.
metadata = MetaData()

# For use in paster shell:
# from sqlalchemy import create_engine
# model.init_model(create_engine('sqlite:///./vault-database.db', echo=True))
