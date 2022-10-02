import enum
from sqlalchemy import String, Integer, Date, Column, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database import Base, engine


class Role(enum.Enum):
    administrator = "administrator"
    resepsionis = "resepsionis"


# class Status(enum.Enum):
#     booked = 'booked'
#     checked_in = 'checked_in'
#     checked_out = 'checked_out'


class FasilitasHotel(Base):
    __tablename__ = "fasilitas_hotel"

    id = Column(Integer, primary_key=True)
    nama = Column(String(50), nullable=False)
    keterangan = Column(String(100), nullable=False)
    gambar = Column(String(100))

    def __repr__(self):
        return f"Table {self.__tablename__}:>\n\t{self.id}>\n\t{self.nama}>\n\t{self.gambar}"


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(25), nullable=False, unique=True)
    nama = Column(String(25), nullable=False)
    password = Column(String(100), nullable=False)

    role = Column(Enum(Role), nullable=False)

    def __repr__(self):
        return f"Table {self.__tablename__}:>\n\t{self.id}>\n\t{self.username}>\n\t{self.nama}>\n\t{self.password}"


class Kamar(Base):
    __tablename__ = "kamar"

    id = Column(Integer, primary_key=True)
    jumlah = Column(Integer, nullable=False)
    gambar = Column(String(100), nullable=False)
    tipe_kamar = Column(String(15), nullable=False, unique=True)
    himpunan_reservasi = relationship("Reservasi", back_populates="kamar")
    fasilitas_kamar = relationship("FasilitasKamar", back_populates="kamar")

    def __repr__(self):
        return f"Table {self.__tablename__}:>\n\t{self.id}>\n\t{self.jumlah}>\n\t{self.gambar}>\n\t{self.tipe_kamar}"


class Reservasi(Base):
    __tablename__ = "reservasi"

    id = Column(Integer, primary_key=True)
    nama_pemesan = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
    no_telp = Column(String(20), nullable=False)
    nama_tamu = Column(String(50), nullable=False)
    jumlah_kamar = Column(Integer, nullable=False)
    tanggal_check_in = Column(Date, nullable=False)
    tanggal_check_out = Column(Date, nullable=False)

    # status = Column(Enum(Status), nullable=False)
    id_kamar = Column(Integer, ForeignKey("kamar.id"), nullable=False)

    kamar = relationship("Kamar", back_populates="himpunan_reservasi")

    def __repr__(self):
        return f"Table {self.__tablename__}:>\n\t{self.id}>\n\t{self.nama_pemesan}>\n\t{self.email}>\n\t{self.no_telp}>\n\t{self.nama_tamu}>\n\t{self.tanggal_check_in}>\n\t{self.tanggal_check_out}"


class FasilitasKamar(Base):
    __tablename__ = "fasilitas_kamar"

    id = Column(Integer, primary_key=True)
    nama = Column(String(50), nullable=False)

    id_kamar = Column(Integer, ForeignKey("kamar.id"), nullable=False)
    kamar = relationship("Kamar", back_populates="fasilitas_kamar")

    def __repr__(self):
        return f"Table {self.__tablename__}:>\n\t{self.id}>\n\t{self.nama}>\n\t{self.id_kamar}"


def migrate():
    Base.metadata.create_all(engine)


def drop():
    Base.metadata.drop_all(engine)
