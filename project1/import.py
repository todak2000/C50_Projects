import os, csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    with open("books.csv", "r") as f:
        reader = csv.reader(f)
        for isbn, title, author, year in reader:
            db.execute("INSERT INTO books (isbn, title, author, year) \
            VALUES (:isbn, :title, :author, :year)",
            {"isbn": isbn, "title": title, "author": author, "year": year})
            print(f"Added book: {title} by {author}, published in {year}.")
        db.commit()
        
if __name__ == "__main__":
    main()