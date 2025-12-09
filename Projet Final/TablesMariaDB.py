from sqlalchemy.orm import DeclarativeBase, mapped_column,relationship
from sqlalchemy import Integer,String, create_engine,ForeignKey

class Base(DeclarativeBase):
    pass

class Camera(Base):
    __tablename__ = "Camera"
    id = mapped_column(Integer, primary_key = True)
    Nom = mapped_column(String(40),nullable=False)

    def __str__(self):
        return f"{self.id}:{self.Nom}"
    

class Image(Base):
    __tablename__ = "Image"
    idi = mapped_column(Integer, primary_key = True)
    path = mapped_column(String(100),nullable=False)
    date = mapped_column(String(20),nullable=False)
    NumeroCam = mapped_column(Integer,ForeignKey('Camera.id'))

    def __str__(self):
        return f"{self.idi}:{self.path},{self.date}"
    
class Battrie(Base):
    __tablename__ = "Battrie"
    id = mapped_column(Integer, primary_key = True)
    poucentage = mapped_column(Integer,nullable=False)
    voltage = mapped_column(Integer,nullable=False)
    date = mapped_column(String(20),nullable=False)
    NumeroCam = mapped_column(Integer,ForeignKey('Camera.id'))

    def __str__(self):
        return f"{self.id}:{self.poucentage},{self.voltage},{self.date}"

class Wifi(Base):
    __tablename__ = "Wifi"
    id = mapped_column(Integer, primary_key = True)
    ssid = mapped_column(String(40),nullable=False)
    pasword = mapped_column(String(40),nullable=False)
    date = mapped_column(String(20),nullable=False)
    NumeroCam = mapped_column(Integer,ForeignKey('Camera.id'))


    def __str__(self):
        return f"{self.id}:{self.ssid},{self.pasword}"
    
class CamParametre(Base):
    __tablename__ = "CamParametre"
    id = mapped_column(Integer, primary_key = True)
    resolution = mapped_column(String(50), nullable=False)
    brightness = mapped_column(Integer, nullable=False)
    contrast = mapped_column(Integer, nullable=False)
    saturation = mapped_column(Integer, nullable=False)
    quality = mapped_column(Integer, nullable=False)
    mirror = mapped_column(String(5), nullable=True)
    flip = mapped_column(String(5), nullable=True)
    date = mapped_column(String(20),nullable=False)
    NumeroCam = mapped_column(Integer,ForeignKey('Camera.id'))

    def __str__(self):
        return f"{self.id}:{self.resolution},{self.brightness},{self.contrast},{self.saturation},{self.quality},{self.mirror},{self.flip}"
    
def main():
    engine = create_engine("mariadb+mariadbconnector://martin:1234@192.168.2.58:3306/RPG", echo = True)
    Base.metadata.create_all(engine)
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    if not session.query(Camera).first():
        cam1 = Camera(Nom="ESP32-Salon")
        session.add(cam1)
        session.commit()
        print("Camera par defaut cree !")
    session.close()

if __name__ == "__main__":
    main()
