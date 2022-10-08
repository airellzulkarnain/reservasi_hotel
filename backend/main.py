from types import NoneType
from fastapi import (
    FastAPI,
    Query,
    Depends,
    HTTPException,
    status,
    Request,
    UploadFile,
    Form,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, date
from fpdf import FPDF, HTMLMixin
from io import BytesIO
from database import SessionLocal
import models, crud, schemas
import uvicorn
import sys
import os

SECRET_KEY = "54c859181e1fafd5611ef27160ad54967e3b4aed46b80e906b0ebd673773a8ca"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class PDF(FPDF, HTMLMixin):
    pass


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(
    title="Reservasi Hotel",
    version="1.0.0",
    description="""
RESTful API untuk mentenagai backend dari aplikasi website atau website reservasi hotel. 
reservasi hotel merupakan tugas PBO yang diberikan ke pada siswa/i SMKN 5 Kota Tangerang 
untuk menguji kompentensi keahlian para siswanya dalam membuat sebuah aplikasi.""",
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

app.mount("/images", StaticFiles(directory="images"), name="images")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_login(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could Not Validate Credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username: str
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user(db, username)
    if user is None:
        raise credentials_exception
    return user

@app.get('/check_expired')
def check_expired(current_user: schemas.User = Depends(check_login)):
    return current_user
    

@app.post("/login", tags=["Login"])
def login(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = crud.get_user(db, form_data.username)
    if not isinstance(user, NoneType) and pwd_context.verify(
        form_data.password, user.password
    ):
        return {
            "access_token": jwt.encode(
                {
                    "sub": user.username,
                    "exp": datetime.utcnow()
                    + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
                },
                SECRET_KEY,
                algorithm=ALGORITHM,
            ),
            "token_type": "bearer",
            "role": user.role
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/get_kamar", tags=["Tamu"])
def get_kamar(db: Session = Depends(get_db)):
    return crud.get_kamar(db)


@app.post("/reservasi", tags=["Tamu"])
def reservasi(data: schemas.Reservasi, db: Session = Depends(get_db)):
    reservasi = crud.reservasi(db, data)
    if reservasi is not None:
        pdf = PDF()
        pdf.add_page()
        pdf.write_html(
            f"""
		<h1>HOTEL HEBAT</h1>
		<h2>Bukti Reservasi</h2>
		<table width='100%'>
		<thead>
			<tr>
				<th width='26%'>Nama Pemesan</th>
				<th width='26%'>Nama Tamu</th>
				<th width='28%'>Email</th>
				<th width='20%'>No. Telp</th>
			</tr>
		</thead>
		<tbody>
			<tr>
				<td>{reservasi.nama_pemesan}</td>
				<td>{reservasi.nama_tamu}</td>
				<td>{reservasi.email}</td>
				<td>{reservasi.no_telp}</td>
			</tr>
		</tbody>
		</table>
        <table width='100%'>
		<thead>
			<tr>
				<th width='20%'>Tipe_Kamar</th>
				<th width='20%'>Jumlah Kamar</th>
				<th width='30%'>Tanggal Check In</th>
				<th width='30%'>Tanggal Check Out</th>
			</tr>
		</thead>
		<tbody>
			<tr>
				<td>{reservasi.kamar.tipe_kamar}</td>
				<td>{reservasi.jumlah_kamar}</td>
				<td>{reservasi.tanggal_check_in}</td>
				<td>{reservasi.tanggal_check_out}</td>
			</tr>
		</tbody>
		</table>
		"""
        )
        try:
            return StreamingResponse(
                BytesIO(pdf.output()), media_type="application/pdf"
            )
        except:
            pass
    return "FAILED"


@app.post("/insert_kamar", tags=["administrator"])
def insert_kamar(
    pict: UploadFile,
    jumlah: int = Form(...),
    tipe_kamar: str = Form(...),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(check_login),
):
    if current_user.role.value == models.Role.administrator.value:
        if pict.content_type.startswith("image"):
            data = {"jumlah": jumlah, "tipe_kamar": tipe_kamar}
            data.update(
                {
                    "gambar": f'images/kamar/{str(datetime.now()).replace(" ", "")}{pict.filename}'
                }
            )
            kamar = crud.insert_kamar(db, data)
            with open(data["gambar"], "wb") as image:
                image.write(pict.file.read())
            return kamar


@app.put("/update_kamar", tags=["administrator"])
def update_kamar(
    id: int = Form(..., gt=0),
    pict: UploadFile | None = None,
    jumlah: int | None = Form(None),
    tipe_kamar: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(check_login),
):
    if current_user.role.value == models.Role.administrator.value:
        data = {"id": id}
        kamar: models.Kamar
        tmp_name: str
        if jumlah is not None:
            data.update({"jumlah": jumlah})
        if tipe_kamar is not None:
            data.update({"tipe_kamar": tipe_kamar})
        if pict is not None:
            if pict.content_type.startswith("image"):
                tmp_name = db.scalar(select(models.Kamar.gambar).where(models.Kamar.id == data['id']))
                os.remove(tmp_name)
                data.update(
                    {
                        "gambar": f'images/kamar/{str(datetime.now()).replace(" ", "")}{pict.filename}'
                    }
                )
        try:
            kamar = crud.update_kamar(db, data)
        except:
            pass
        else:
            try:
                with open(data["gambar"], "wb") as image:
                    image.write(pict.file.read())
            except KeyError:
                pass
        return kamar


@app.get("/get_fasilitas_kamar/{id}", tags=["Tamu"])
def get_fasilitas_kamar(id: int, db: Session = Depends(get_db)):
    return crud.get_fasilitas_kamar(db, id)


@app.post("/insert_fasilitas_kamar", tags=["administrator"])
def insert_fasilitas_kamar(
    data: schemas.FasilitasKamar,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(check_login),
):
    if current_user.role.value == models.Role.administrator.value:
        return crud.insert_fasilitas_kamar(db, data)


@app.put("/update_fasilitas_kamar", tags=["administrator"])
async def update_fasilitas_kamar(
    request: Request,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(check_login),
):
    if current_user.role.value == models.Role.administrator.value:
        data: dict = await request.json()
        return crud.update_fasilitas_kamar(db, data)


@app.get("/get_fasilitas_hotel", tags=["Tamu"])
def get_fasilitas_hotel(db: Session = Depends(get_db)):
    return crud.get_fasilitas_hotel(db)


@app.post("/insert_fasilitas_hotel", tags=["administrator"])
def insert_fasilitas_hotel(
    pict: UploadFile,
    nama: str = Form(..., max_length=50),
    keterangan: str = Form(..., max_length=100),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(check_login),
):

    if current_user.role.value == models.Role.administrator.value:
        if pict.content_type.startswith("image"):
            data = {"nama": nama, "keterangan": keterangan}
            data.update(
                {
                    "gambar": f'images/fasilitas_hotel/{str(datetime.now()).replace(" ", "")}{pict.filename}'
                }
            )
            fasilitas_hotel = crud.insert_fasilitas_hotel(db, data)
            with open(data["gambar"], "wb") as image:
                image.write(pict.file.read())
            return fasilitas_hotel


@app.put("/update_fasilitas_hotel", tags=["administrator"])
def update_fasilitas_hotel(
    id: int = Form(..., gt=0),
    pict: UploadFile | None = None,
    nama: str | None = Form(None, max_length=50),
    keterangan: str | None = Form(None, max_length=100),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(check_login),
):
    if current_user.role.value == models.Role.administrator.value:
        data = {"id": id}
        tmp_name: str
        fasilitas_hotel: models.FasilitasHotel
        if nama is not None:
            data.update({"nama": nama})
        if keterangan is not None:
            data.update({"keterangan": keterangan})
        if pict is not None:
            if pict.content_type.startswith("image"):
                tmp_name = db.scalar(select(models.FasilitasHotel.gambar).where(models.FasilitasHotel.id == data['id']))
                os.remove(tmp_name)
                data.update(
                    {
                        "gambar": f'images/fasilitas_hotel/{str(datetime.now()).replace(" ", "")}{pict.filename}'
                    }
                )
        try:
            fasilitas_hotel = crud.update_fasilitas_hotel(db, data)
        except:
            pass
        else:
            try:
                with open(data["gambar"], "wb") as image:
                    image.write(pict.file.read())
            except KeyError:
                pass
        return fasilitas_hotel


@app.get("/jumlah_kamar/{id}", tags=["Tamu"])
def jumlah_kamar(id: int, db: Session = Depends(get_db)):
    return crud.get_jumlah_kamar(db, id)


@app.get("/tipe_kamar", tags=["Tamu"])
def tipe_kamar(db: Session = Depends(get_db)):
    return crud.get_tipe_kamar(db)


@app.get("/get_reservasi", tags=["resepsionis"])
def get_reservasi(
    db: Session = Depends(get_db), current_user: schemas.User = Depends(check_login)
):
    if current_user.role.value == models.Role.resepsionis.value:
        return crud.get_reservasi(db)


@app.get("/get_reservasi_by_tanggal_check_in", tags=["resepsionis"])
def filter_reservasi_by_tanggal_check_in(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(check_login),
    tanggal_check_in: date | None = Query(None),
):
    if current_user.role.value == models.Role.resepsionis.value:
        return crud.filter_reservasi_by_tanggal_check_in(db, tanggal_check_in)


@app.get("/get_reservasi_by_nama_tamu", tags=["resepsionis"])
def search_reservasi_by_nama_tamu(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(check_login),
    nama_tamu: str | None = Query(None, regex="^[a-zA-Z\s]+$"),
):
    if current_user.role.value == models.Role.resepsionis.value:
        return crud.search_reservasi_by_nama_tamu(db, nama_tamu)

@app.put("/check_in/{id}")
def check_in(id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(check_login)):
    if current_user.role.value == models.Role.resepsionis.value: 
        return crud.check_in(db, id)

if __name__ == "__main__":
    if sys.argv[1] == "migrate":
        models.migrate()
    elif sys.argv[1] == "drop":
        models.drop()
    elif sys.argv[1] == "run":
        uvicorn.run(app, host="0.0.0.0", port=8000)
