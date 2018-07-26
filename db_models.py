from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///db.db', echo=True)
Base = declarative_base()

class Person(Base):
    __tablename__ = 'persons'
    id = Column(Integer, primary_key=True)
    person = Column(String)
    marks = Column(String)

    def __init__(self, person, marks):
        self.person = person
        self.marks = marks

    def __repr__(self):
        return '<Person({} {} {})>'.format(self.id, self.person, self.marks)

Base.metadata.create_all(engine)
session = sessionmaker(bind=engine)()