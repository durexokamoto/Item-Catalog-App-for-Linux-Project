#!/usr/bin/python
from os import remove
from os.path import isfile
from shutil import copytree, rmtree

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from catalog import Base, Category, Item, RELATIVE_IMAGE_DIRECTORY, User


USERS = [
    {
        'id': 1,
        'name': '',
        'email': 'neroyen@gmail.com',
        'picture': '',
        'group': 'admin'
    }
]


CATEGORIES = [
    {
        'id': 'guitars',
        'name': 'Guitars'
    },
    {
        'id': 'bass',
        'name': 'Bass Guitars'
    },
    {
        'id': 'amplifiers-effects',
        'name': 'Amplifiers & Effects'
    },
    {
        'id': 'drums-percussion',
        'name': 'Drums & Percussion'
    },
    {
        'id': 'live-sound',
        'name': 'Live Sound'
    },
    {
        'id': 'recording-gear',
        'name': 'Recording'
    },
    {
        'id': 'accessories',
        'name': 'Accessories'
    }
]


ITEMS = [
    {
        "category_id": "accessories",
        "description": "A",
        "id": "AAA",
        "image_path": "/img/5043619.png",
        "name": "AAAA",
        "price": "$9.99",
        "short_description": "AAA",
        "user_id": 1
    }
]


# Copy seed images to img.
rmtree('img', ignore_errors=True)
copytree('seed_images', RELATIVE_IMAGE_DIRECTORY)

# Remove catalog.db, if exists.
if isfile('catalog.db'):
    remove('catalog.db')

# Create the database.
engine = create_engine('postgresql://catalog:catalog@localhost/catalog')
Base.metadata.create_all(engine)
db_session = sessionmaker(bind=engine)
catalog = db_session()

# Add users to the database.
for user in USERS:
    catalog.add(User(name=user['name'],
                     email=user['email'], picture=user['picture'],
                     group=user['group']))

# Add categories to the database.
for category in CATEGORIES:
    catalog.add(Category(id=category['id'], name=category['name']))

# Add items to the database.
for item in ITEMS:
    catalog.add(
        Item(id=item['id'], name=item['name'],
             short_description=item['short_description'],
             description=item['description'], price=item['price'],
             image_path=item['image_path'],
             category_id=item['category_id'],
             user_id=item['user_id']))

# Commit all the database changes.
catalog.commit()
