from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Item, User, Base, Post

engine = create_engine('sqlite:///chatboard.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#Dummy User
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Categories - Social
Social = Category(id=1, name="Social")
session.add(Social)
session.commit()

Outdoor_Activities = Item(name="Outdoor Activities", description="This forum is deticated to talk about outdoor activities which can include abseiling, backpacking, coasteering, cycling, camping, canoeing, canyoning, caving, fastpacking, fishing, hiking, horseback riding, hunting, kayaking, rafting, rock climbing, running, sailing, skiing, or more.", category_id=1, id=1)
session.add(Outdoor_Activities)
session.commit()

Post1 = Post(post="Today is a good day to go to a beach", item_id=1)
session.add(Post1)
session.commit()

Social_Media = Item(name="Social Media", description="This forum is deticated to talk about anything social media", category_id=1, id=2)
session.add(Social_Media)
session.commit()

Post2 = Post(post="Is facebook down today?", item_id=2)
session.add(Post2)
session.commit()

# Categories - Tech

Tech = Category(id=2, name="Tech")
session.add(Tech)
session.commit()

Tech_News = Item(name="Tech News", description="What's new in the tech industry?", category_id=2, id=3)
session.add(Tech_News)
session.commit()

Post3 = Post(post="Did you guys see Elon Musk's new statement?", item_id=3)
session.add(Post3)
session.commit()

Products = Item(name="Products", description="This forum is deticated to tech products", category_id=2,id=4 )
session.add(Products)
session.commit()

Post4 = Post(post="Did you guys see the new iPhone feature?", item_id=4)
session.add(Post4)
session.commit()


# Categories - News

News = Category(id=3, name="News")
session.add(News)
session.commit()

Local = Item(name="Local", description="What's happening in the US?", category_id=3, id=5)
session.add(Local)
session.commit()

Post5 = Post(post="Did you guys see local governemnt?", item_id=5)
session.add(Post5)
session.commit()

International = Item(name="International", description="What's happening in the world?", category_id=3, id=6)
session.add(International)
session.commit()

Post6 = Post(post="War in Syria?", item_id=6)
session.add(Post6)
session.commit()


# Categories - Entertainment

Entertainment = Category(id=4, name="Entertainment")
session.add(Entertainment)
session.commit()

Books = Item(name="Books", description="What are you reading these days??", category_id=4, id=7)
session.add(Books)
session.commit()


Post7 = Post(post="Harry Potter new realease?", item_id=7)
session.add(Post7)
session.commit()

Movies = Item(name="Movies", description="What are you watching these days??", category_id=4, id=8)
session.add(Movies)
session.commit()

Post8 = Post(post="Harry Potter?", item_id=8)
session.add(Post8)
session.commit()



print("Added data")