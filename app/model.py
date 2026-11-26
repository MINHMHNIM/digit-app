from pathlib import Path

import joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC

DUONG_DAN_MO_HINH = Path(__file__).resolve().parent / "mo_hinh.joblib"


def huan_luyen():
    du_lieu = load_digits()
    x_train, x_test, y_train, y_test = train_test_split(
        du_lieu.data,
        du_lieu.target,
        test_size=0.2,
        random_state=42,
        stratify=du_lieu.target,
    )
    mo_hinh = CalibratedClassifierCV(SVC(gamma=0.0005, C=10), ensemble=False)
    mo_hinh.fit(x_train, y_train)
    do_chinh_xac = mo_hinh.score(x_test, y_test)
    joblib.dump({"mo_hinh": mo_hinh, "do_chinh_xac": do_chinh_xac}, DUONG_DAN_MO_HINH)
    return do_chinh_xac


def tai_mo_hinh():
    if not DUONG_DAN_MO_HINH.exists():
        huan_luyen()
    return joblib.load(DUONG_DAN_MO_HINH)


if __name__ == "__main__":
    print(f"Da huan luyen xong. Do chinh xac tren tap test: {huan_luyen():.2%}")
