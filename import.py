import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
engine=create_engine("postgres://cbgfiufiugsgld:f5f49d9548f4c3fb1f9d8360a4415b8172fe574dcffe889ed9e82859153451df@ec2-35-172-73-125.compute-1.amazonaws.com:5432/d3ap3dqmbg5aof")
db = scoped_session(sessionmaker(bind=engine))

def main():
    f=open("books.csv")
    reader=csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT into books (isbn, title, author, year) values (:isbn, :title, :author, :year)", {"isbn": isbn, "title": title, "author": author, "year": year})
    db.commit()
if __name__=="__main__":
    main()
