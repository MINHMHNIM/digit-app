import socket
import urllib.request
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .model import tai_mo_hinh
from .xu_ly_anh import LoiAnh, chuyen_ve_8x8, giai_ma_anh

THU_MUC_GIAO_DIEN = Path(__file__).resolve().parent / "static"
DIA_CHI_METADATA = "http://169.254.169.254/latest"

app = FastAPI(title="Nhận diện chữ số viết tay")
goi_mo_hinh = tai_mo_hinh()
mo_hinh = goi_mo_hinh["mo_hinh"]
trinh_mo_khong_proxy = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class YeuCauDuDoan(BaseModel):
    anh: str = Field(..., max_length=2_000_000)


def doc_metadata(duong_dan, token):
    yeu_cau = urllib.request.Request(
        f"{DIA_CHI_METADATA}/meta-data/{duong_dan}",
        headers={"X-aws-ec2-metadata-token": token},
    )
    return trinh_mo_khong_proxy.open(yeu_cau, timeout=1).read().decode()


@lru_cache
def thong_tin_ec2():
    try:
        yeu_cau_token = urllib.request.Request(
            f"{DIA_CHI_METADATA}/api/token",
            method="PUT",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
        )
        token = trinh_mo_khong_proxy.open(yeu_cau_token, timeout=1).read().decode()
        return {
            "instance_id": doc_metadata("instance-id", token),
            "loai_may": doc_metadata("instance-type", token),
            "vung": doc_metadata("placement/availability-zone", token),
        }
    except OSError:
        return None


@app.get("/")
def trang_chu():
    return FileResponse(THU_MUC_GIAO_DIEN / "index.html")


@app.get("/health")
def kiem_tra_suc_khoe():
    return {"trang_thai": "ok"}


@app.get("/api/thong-tin")
def thong_tin():
    return {
        "hostname": socket.gethostname(),
        "ec2": thong_tin_ec2(),
        "do_chinh_xac_tap_test": round(goi_mo_hinh["do_chinh_xac"], 4),
    }


@app.post("/api/du-doan")
def du_doan(yeu_cau: YeuCauDuDoan):
    try:
        anh_8x8 = chuyen_ve_8x8(giai_ma_anh(yeu_cau.anh))
    except LoiAnh as loi:
        raise HTTPException(status_code=400, detail=str(loi)) from loi
    xac_suat = mo_hinh.predict_proba(anh_8x8.reshape(1, 64))[0]
    nhan = [int(x) for x in mo_hinh.classes_]
    return {
        "chu_so": nhan[int(xac_suat.argmax())],
        "xac_suat": {str(n): round(float(p), 4) for n, p in zip(nhan, xac_suat)},
        "anh_8x8": anh_8x8.astype(int).tolist(),
    }
