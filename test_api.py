
import requests

cerita = """
Pada zaman dahulu, hiduplah seekor kancil di sebuah hutan.
Suatu hari, kancil bertemu dengan seekor buaya yang sedang
berada di tepi sungai. Kancil kemudian mencari cara agar
dapat menyeberangi sungai tersebut.
"""

response = requests.post(
    "http://127.0.0.1:5000/api/predict",
    json={"text": cerita}
)

print("Status:", response.status_code)
print("Hasil:", response.json())
