from sqlalchemy.orm import DeclarativeBase, mapped_column,relationship
from sqlalchemy import Integer,String, create_engine,ForeignKey

class Base(DeclarativeBase):
    pass

class Image(Base):
    __tablename__ = "Images"
    idi = mapped_column(Integer, primary_key = True)
    path = mapped_column(String(40),nullable=False)
    date = mapped_column(String(20),nullable=False)

    def __str__(self):
        return f"{self.idi}:{self.titre},{self.genre.genre}"
    
class Battrie(Base):
    __tablename__ = "Battrie"
    idb = mapped_column(Integer, primary_key = True)
    poucentage = mapped_column(Integer,nullable=False)
    date = mapped_column(String(20),nullable=False)

    def __str__(self):
        return f"{self.idb}:{self.poucentage},{self.date}"
    
class Temperature(Base):
    __tablename__ = "Temperature"
    idt = mapped_column(Integer, primary_key = True)
    temperature = mapped_column(String(40),nullable=False)
    date = mapped_column(String(20),nullable=False)

    def __str__(self):
        return f"{self.idt}:{self.temperature},{self.date}"
    
def main():
    engine = create_engine("mariadb+mariadbconnector://martin:123456@192.168.2.35:3306/RPG", echo = True)
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    main()