from yandex_school import db

"""
    Run this file to create a blank database.

    *********************************************
    ***CAUTION: DELETES ALL THE EXISTING DATA!***
    *********************************************
"""

"""
    Presents an import entity. Serves as an import_id counter.
"""
Import = db.Table(
    'import',
    db.metadata,
    db.Column('id', db.Integer, primary_key=True)
)

"""
    Presents a citizen entity, stores all the citizen data
"""
Citizen = db.Table(
    'citizen',
    db.metadata,
    db.Column('id', db.Integer, primary_key=True),
    db.Column('import_id', db.Integer, db.ForeignKey(Import.c.id)),
    db.Column('citizen_id', db.Integer, nullable=False),
    db.Column('town', db.String, nullable=False),
    db.Column('street', db.String, nullable=False),
    db.Column('building', db.String, nullable=False),
    db.Column('apartment', db.Integer, nullable=False),
    db.Column('name', db.String, nullable=False),
    db.Column('birth_date', db.Date, nullable=False),
    db.Column('gender', db.String, nullable=False)
)

"""
    Relationship entry between citizens. Consists of a composite primary key: citizen_id, relative_id both
    referencing citizen's id field.
"""
Relative = db.Table(
    'relative',
    db.metadata,
    db.Column('citizen_id', db.Integer, db.ForeignKey('citizen.id'), primary_key=True),
    db.Column('relative_id', db.Integer, db.ForeignKey('citizen.id'), primary_key=True)
)

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
