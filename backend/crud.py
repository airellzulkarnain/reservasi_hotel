from sqlalchemy.orm import Session
from sqlalchemy import select, and_, update
from sqlalchemy import func
from datetime import date, datetime
import pytz
import models, schemas


# Tamu :
# 1.Tamu dapat melihat informasi tentang tipe kamar yang tersedia beserta fasilitas setiap tipe kamar dan fasilitas-fasilitas yang tersedia di Hotel
# 2.Tamu dapat melakukan reservasi kamar secara online
# 3.Tamu hanya bisa memesan tipe kamar yang sama saat melakukan pemesanan lebih dari 1 kamar dalam 1 kali pemesanan
# 4.Tamu dapat mencetak bukti reservasi untuk diserahkan resepsionis pada saat check-in.
def get_kamar(db: Session):
    return db.execute(select(models.Kamar)).all()


def reservasi(db: Session, data: schemas.Reservasi):
    kamar: models.Kamar = db.scalar(
        select(models.Kamar).where(models.Kamar.id == data.id_kamar)
    )
    today = datetime.now(pytz.timezone("Asia/Jakarta")).date()
    jumlah_terisi = sum(
        [
            x.jumlah_kamar
            for x in kamar.himpunan_reservasi
            if x.tanggal_check_out >= today
        ]
    )
    if data.jumlah_kamar <= kamar.jumlah - jumlah_terisi and today <= data.tanggal_check_in < data.tanggal_check_out:
        reservasi = models.Reservasi(**data.dict())
        db.add(reservasi)
        db.commit()
        db.refresh(reservasi)
        return reservasi


# Administrator :
def insert_kamar(db: Session, data: schemas.InsertKamar):
    kamar = models.Kamar(**data)
    db.add(kamar)
    db.commit()
    db.refresh(kamar)
    return kamar


def update_kamar(db: Session, data: dict):
    id = data.pop("id")
    kamar = db.scalar(select(models.Kamar).where(models.Kamar.id == id))
    db.execute(update(models.Kamar).where(models.Kamar.id == id).values(**data))
    db.commit()
    db.refresh(kamar)
    return kamar


def get_fasilitas_kamar(db: Session, id: int):
    if id != -1: 
        return db.execute(
            select(models.FasilitasKamar).where(models.FasilitasKamar.id_kamar == id)
        ).all()
    return db.execute(select(models.FasilitasKamar)).all();


def insert_fasilitas_kamar(db: Session, data: schemas.FasilitasKamar):
    fasilitas_kamar = models.FasilitasKamar(**data.dict())
    db.add(fasilitas_kamar)
    db.commit()
    db.refresh(fasilitas_kamar)
    return fasilitas_kamar


def update_fasilitas_kamar(db: Session, data: dict):
    id = data.pop("id")
    fasilitas_kamar = db.scalar(
        select(models.FasilitasKamar).where(models.FasilitasKamar.id == id)
    )
    db.execute(
        update(models.FasilitasKamar)
        .where(models.FasilitasKamar.id == id)
        .values(**data)
    )
    db.commit()
    db.refresh(fasilitas_kamar)
    return fasilitas_kamar


def insert_fasilitas_hotel(db: Session, data: schemas.FasilitasHotel):
    fasilitas_hotel = models.FasilitasHotel(**data)
    db.add(fasilitas_hotel)
    db.commit()
    db.refresh(fasilitas_hotel)
    return fasilitas_hotel


def update_fasilitas_hotel(db: Session, data: dict):
    id = data.pop("id")
    fasilitas_hotel = db.scalar(
        select(models.FasilitasHotel).where(models.FasilitasHotel.id == id)
    )
    db.execute(
        update(models.FasilitasHotel)
        .where(models.FasilitasHotel.id == id)
        .values(**data)
    )
    db.commit()
    db.refresh(fasilitas_hotel)
    return fasilitas_hotel


def get_fasilitas_hotel(db: Session):
    return db.execute(select(models.FasilitasHotel)).all()


# 1.Admin dapat menambah, dan mengupdate data kamar
# 2.Admin dapat menambah, dan mengupdate data fasilitas kamar
# 3.Admin dapat menambah, dan mengupdate data fasilitas umum hotel

# Resepsionis :
def get_reservasi(db: Session):
    return db.execute(
        select(models.Reservasi).where(and_(
            models.Reservasi.tanggal_check_out
            >= datetime.now(pytz.timezone("Asia/Jakarta")).date(), 
            models.Reservasi.status != 'checked_in'
        )
        )
    ).all()


def filter_reservasi_by_tanggal_check_in(db: Session, tanggal_check_in: date | None = None):
    if tanggal_check_in is not None: 
        return db.execute(
            select(models.Reservasi).where(and_(
                models.Reservasi.tanggal_check_in == tanggal_check_in, 
                models.Reservasi.tanggal_check_out
                >= datetime.now(pytz.timezone("Asia/Jakarta")).date(), 
                models.Reservasi.status != 'checked_in'
            )
            )
        ).all()
    return get_reservasi(db)


def search_reservasi_by_nama_tamu(db: Session, nama_tamu: str | None = None):
    if nama_tamu is not None: 
        return db.execute(
            select(models.Reservasi).where(and_(
                models.Reservasi.nama_tamu.like(f"%{nama_tamu}%"), 
                models.Reservasi.tanggal_check_out
                >= datetime.now(pytz.timezone("Asia/Jakarta")).date(), 
                models.Reservasi.status != 'checked_in'
                )
            )
        ).all()
    return get_reservasi(db)

def check_in(db: Session, id: int): 
    reservasi: models.Reservasi = db.scalar(select(models.Reservasi).where(models.Reservasi.id == id))
    reservasi.status = 'checked_in'
    db.commit()
    db.refresh(reservasi)
    return {"status": "check in succeed"}
# 1.Resepsionis dapat melakukan pengecekan data reservasi
# 2.Resepsionis dapat melakukan filtering berdasarkan tanggal check-in
# 3.Resepsionis dapat melakukan pencarian data reservasi berdasarkan nama tamu.

# additional
def get_tipe_kamar(db: Session):
    return db.execute(select(models.Kamar.tipe_kamar)).all()


def get_jumlah_kamar(db: Session, id: int):
    kamar: models.Kamar = db.scalar(select(models.Kamar).where(models.Kamar.id == id))
    jumlah_terisi = sum(
        [
            x.jumlah_kamar
            for x in kamar.himpunan_reservasi
            if x.tanggal_check_out >= datetime.now(pytz.timezone("Asia/Jakarta")).date()
        ]
    )
    return {"jumlah": f"{jumlah_terisi}/{kamar.jumlah}"}


def get_user(db: Session, username: str):
    return db.scalar(select(models.User).where(models.User.username == username))
