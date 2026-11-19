
import re
import json
import torch
import torch.nn as nn

from pathlib import Path
from flask import Flask, request, jsonify, render_template
from transformers import AutoTokenizer, AutoModel
from torch.nn.utils.rnn import pack_padded_sequence


# ==========================================
# 1. KONFIGURASI
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "model"

with open(MODEL_DIR / "config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

with open(MODEL_DIR / "labels.json", "r", encoding="utf-8") as f:
    labels = json.load(f)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Device:", DEVICE)
print("Konfigurasi:", config)
print("Label:", labels)


# ==========================================
# 2. ARSITEKTUR GRU
# ==========================================

class GRUClassifier(nn.Module):

    def __init__(
        self,
        input_size=768,
        hidden_size=128,
        num_classes=3,
        dropout=0.5
    ):
        super().__init__()

        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            batch_first=True
        )

        self.dropout = nn.Dropout(dropout)

        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x, lengths):

        packed_input = pack_padded_sequence(
            x,
            lengths.cpu(),
            batch_first=True,
            enforce_sorted=False
        )

        _, hidden = self.gru(packed_input)

        last_hidden = hidden[-1]

        last_hidden = self.dropout(last_hidden)

        logits = self.fc(last_hidden)

        probabilities = torch.softmax(logits, dim=1)

        return logits, probabilities


# ==========================================
# 3. MEMUAT TOKENIZER DAN INDOBERT
# ==========================================

print("\nMemuat tokenizer dan IndoBERT...")

tokenizer = AutoTokenizer.from_pretrained(
    config["model_name"]
)

indobert = AutoModel.from_pretrained(
    config["model_name"]
)

indobert.to(DEVICE)
indobert.eval()

# IndoBERT dibekukan, sesuai proses training
for param in indobert.parameters():
    param.requires_grad = False


# ==========================================
# 4. MEMUAT MODEL GRU
# ==========================================

print("\nMemuat model GRU...")

model = GRUClassifier(
    input_size=config["input_size"],
    hidden_size=config["hidden_size"],
    num_classes=config["num_classes"],
    dropout=config["dropout"]
)

checkpoint_path = MODEL_DIR / "model_gru.pth"

try:
    state_dict = torch.load(
        checkpoint_path,
        map_location=DEVICE,
        weights_only=True
    )
except TypeError:
    state_dict = torch.load(
        checkpoint_path,
        map_location=DEVICE
    )

model.load_state_dict(state_dict)

model.to(DEVICE)
model.eval()

print("Model GRU berhasil dimuat!")


# ==========================================
# 5. PREPROCESSING
# ==========================================

normalization_dict = {
    "gak": "tidak",
    "ga": "tidak",
    "nggak": "tidak",
    "ngga": "tidak",
    "yg": "yang",
    "dgn": "dengan",
    "dr": "dari",
    "utk": "untuk",
    "tdk": "tidak",
    "krn": "karena",
    "tak": "tidak"
}


def preprocessing(text):

    text = text.lower()

    words = text.split()

    words = [
        normalization_dict.get(word, word)
        for word in words
    ]

    text = " ".join(words)

    text = re.sub(r"http\S+|www\S+", "", text)

    text = re.sub(r"\d+", "", text)

    text = re.sub(r"[^\w\s]", "", text)

    text = text.replace("_", "")

    text = re.sub(r"\s+", " ", text).strip()

    return text


# ==========================================
# 6. PEMILIHAN BAGIAN CERITA
# ==========================================

def select_story_parts(text):

    words = text.split()

    if len(words) <= 2:
        return text

    first_count = int(len(words) * 0.25)

    last_count = int(len(words) * 0.25)

    if first_count == 0 or last_count == 0:
        return text

    if first_count + last_count >= len(words):
        return text

    selected_words = words[:first_count] + words[-last_count:]

    return " ".join(selected_words)


# ==========================================
# 7. FUNGSI PREDIKSI
# ==========================================

def predict_single_story(text):

    # Preprocessing
    cleaned_text = preprocessing(text)

    if not cleaned_text:
        raise ValueError("Teks cerita tidak boleh kosong.")

    # Memilih bagian awal dan akhir cerita
    selected_text = select_story_parts(cleaned_text)

    # Tokenisasi IndoBERT
    encoded = tokenizer(
        selected_text,
        padding="max_length",
        truncation=True,
        max_length=config["max_length"],
        return_tensors="pt"
    )

    input_ids = encoded["input_ids"].to(DEVICE)

    attention_mask = encoded["attention_mask"].to(DEVICE)

    # Menghitung panjang token valid
    lengths = attention_mask.sum(dim=1)

    if lengths.item() == 0:
        raise ValueError("Tidak ada token yang dapat diproses.")

    # Menghasilkan embedding IndoBERT dan prediksi GRU
    with torch.inference_mode():

        outputs = indobert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )

        embeddings = outputs.last_hidden_state

        logits, probabilities = model(
            embeddings,
            lengths
        )

    # Mengambil kelas dengan probabilitas tertinggi
    predicted_index = torch.argmax(
        probabilities,
        dim=1
    ).item()

    predicted_label = labels[predicted_index]

    # Mengubah probabilitas menjadi persentase
    probability_values = probabilities[0].cpu().tolist()

    probability_result = {
        labels[i]: round(probability_values[i] * 100, 2)
        for i in range(len(labels))
    }

    return {
        "prediksi": predicted_label,
        "probabilitas": probability_result
    }


# ==========================================
# 8. FLASK APPLICATION
# ==========================================

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/tentang", methods=["GET"])
def tentang():
    return render_template("about.html")
    
from flask import Flask, request, jsonify, render_template


@app.route("/api/predict", methods=["POST"])
def predict():

    try:

        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "status": "error",
                "pesan": "Data JSON tidak ditemukan."
            }), 400

        text = data.get("text", "")

        if not isinstance(text, str) or not text.strip():
            return jsonify({
                "status": "error",
                "pesan": "Masukkan teks cerita rakyat terlebih dahulu."
            }), 400

        result = predict_single_story(text)

        return jsonify({
            "status": "success",
            "hasil": result
        })

    except ValueError as e:

        return jsonify({
            "status": "error",
            "pesan": str(e)
        }), 400

    except Exception as e:

        print("Error:", str(e))

        return jsonify({
            "status": "error",
            "pesan": "Terjadi kesalahan saat melakukan klasifikasi."
        }), 500


# ==========================================
# 9. MENJALANKAN SERVER
# ==========================================

if __name__ == "__main__":

    print("\nBackend siap dijalankan!")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
