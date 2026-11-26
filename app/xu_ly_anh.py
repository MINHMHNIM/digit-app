import base64
import binascii
import io

import numpy as np
from PIL import Image, ImageFilter, UnidentifiedImageError

KICH_THUOC_KHUNG = 32
HE_SO_PHONG = 4
KHUNG_LON = KICH_THUOC_KHUNG * HE_SO_PHONG
NGUONG_NET_VE = 50
NGUONG_NHI_PHAN = 100
DO_DAY_MUC_TIEU = 5 * HE_SO_PHONG
TI_LE_RONG_TOI_THIEU = 0.6
KICH_THUOC_LOC_TOI_DA = 31


class LoiAnh(ValueError):
    pass


def giai_ma_anh(chuoi_base64):
    if "," in chuoi_base64:
        chuoi_base64 = chuoi_base64.split(",", 1)[1]
    try:
        du_lieu = base64.b64decode(chuoi_base64, validate=True)
        anh = Image.open(io.BytesIO(du_lieu))
        anh.load()
    except (binascii.Error, UnidentifiedImageError, OSError) as loi:
        raise LoiAnh("Ảnh gửi lên không hợp lệ") from loi
    if anh.mode in ("RGBA", "LA", "P"):
        nen = Image.new("RGBA", anh.size, (0, 0, 0, 255))
        anh = Image.alpha_composite(nen, anh.convert("RGBA"))
    return anh.convert("L")


def uoc_luong_do_day(nhi_phan):
    vien = np.pad(nhi_phan, 1)
    ben_trong = vien[:-2, 1:-1] & vien[2:, 1:-1] & vien[1:-1, :-2] & vien[1:-1, 2:]
    diem_bien = nhi_phan & ~ben_trong
    return 2 * nhi_phan.sum() / max(1, diem_bien.sum())


def chuan_hoa_do_day(anh_nhi_phan, nhi_phan):
    chenh_lech = round(DO_DAY_MUC_TIEU - uoc_luong_do_day(nhi_phan))
    kich_thuoc_loc = min(abs(chenh_lech) | 1, KICH_THUOC_LOC_TOI_DA)
    if chenh_lech >= 2:
        return anh_nhi_phan.filter(ImageFilter.MaxFilter(kich_thuoc_loc))
    if chenh_lech <= -2:
        return anh_nhi_phan.filter(ImageFilter.MinFilter(kich_thuoc_loc))
    return anh_nhi_phan


def chuyen_ve_8x8(anh):
    mang = np.asarray(anh, dtype=np.float32)
    if mang.mean() > 127:
        mang = 255 - mang
    vi_tri = np.argwhere(mang > NGUONG_NET_VE)
    if len(vi_tri) == 0:
        raise LoiAnh("Bạn chưa vẽ gì cả")
    (y_dau, x_dau), (y_cuoi, x_cuoi) = vi_tri.min(axis=0), vi_tri.max(axis=0) + 1
    vung_chu = Image.fromarray(mang[y_dau:y_cuoi, x_dau:x_cuoi].astype(np.uint8))

    rong, cao = vung_chu.size
    ti_le = KHUNG_LON / max(rong, cao)
    rong_moi, cao_moi = rong * ti_le, cao * ti_le
    rong_moi = max(rong_moi, TI_LE_RONG_TOI_THIEU * cao_moi)
    vung_chu = vung_chu.resize((max(1, round(rong_moi)), max(1, round(cao_moi))), Image.LANCZOS)

    nhi_phan = np.asarray(vung_chu) > NGUONG_NHI_PHAN
    anh_nhi_phan = Image.fromarray((nhi_phan * 255).astype(np.uint8))
    anh_nhi_phan = chuan_hoa_do_day(anh_nhi_phan, nhi_phan)

    khung = Image.new("L", (KHUNG_LON, KHUNG_LON), 0)
    rong_net, cao_net = anh_nhi_phan.size
    khung.paste(anh_nhi_phan, ((KHUNG_LON - rong_net) // 2, (KHUNG_LON - cao_net) // 2))
    khung_nho = np.asarray(khung.resize((KICH_THUOC_KHUNG, KICH_THUOC_KHUNG), Image.BOX)) > 127
    return khung_nho.reshape(8, 4, 8, 4).sum(axis=(1, 3)).astype(np.float32)
