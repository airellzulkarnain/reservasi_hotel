from pydantic import BaseModel, Field, EmailStr
from datetime import date

from models import Role
from database import Base


class User(BaseModel):
    username: str = Field(..., regex="^[a-zA-Z0-9\s]+$")
    nama: str = Field(..., regex="^[a-zA-Z0-9\s]+$")
    role: Role

    class Config:
        orm_mode = True


class InsertKamar(BaseModel):
    jumlah: int = Field(..., gt=0)
    tipe_kamar: str = Field(..., regex="^[a-zA-Z0-9\s]+$")


class GetKamar(InsertKamar):
    id: int

    class Config:
        orm_mode = True


class Reservasi(BaseModel):
    nama_pemesan: str = Field(..., regex="^[a-zA-Z0-9\s]+$", max_length=50)
    email: EmailStr
    no_telp: str = Field(..., regex="^[0-9\-\+]+$", max_length=20)
    nama_tamu: str = Field(..., regex="^[a-zA-Z0-9\s]+$", max_length=50)
    jumlah_kamar: int = Field(..., gt=0)
    tanggal_check_in: date
    tanggal_check_out: date
    id_kamar: int = Field(..., gt=0)


class FasilitasKamar(BaseModel):
    nama: str = Field(..., max_length=50)
    id_kamar: int = Field(..., gt=0)


class FasilitasHotel(BaseModel):
    nama: str = Field(..., regex="^[a-zA-Z0-9\s]+$", max_length=50)
    keterangan: str = Field(..., regex="^[a-zA-Z0-9\s]+$", max_length=100)
