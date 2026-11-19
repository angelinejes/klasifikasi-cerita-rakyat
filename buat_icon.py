
from PIL import Image
from pathlib import Path

# Lokasi logo Canva
folder = Path(__file__).resolve().parent
logo_path = folder / "docs" / "static" / "images" / "logo.png"

# Lokasi penyimpanan ikon
output_folder = folder / "docs" / "static" / "images"
output_folder.mkdir(parents=True, exist_ok=True)

# Buka logo asli
logo = Image.open(logo_path).convert("RGBA")

# Buat dua ukuran ikon
for ukuran in [192, 512]:
    kanvas = Image.new("RGBA", (ukuran, ukuran), (0, 0, 0, 0))

    # Sesuaikan ukuran tanpa mengubah proporsi logo
    logo_salinan = logo.copy()
    logo_salinan.thumbnail(
        (int(ukuran * 0.86), int(ukuran * 0.86)),
        Image.Resampling.LANCZOS
    )

    # Letakkan logo di tengah
    posisi = (
        (ukuran - logo_salinan.width) // 2,
        (ukuran - logo_salinan.height) // 2
    )

    kanvas.alpha_composite(logo_salinan, posisi)

    # Simpan ikon
    kanvas.save(output_folder / f"icon-{ukuran}.png")

print("Ikon berhasil dibuat!")