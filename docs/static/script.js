async function classifyStory() {
    const storyText = document.getElementById("story-text").value.trim();
    const button = document.getElementById("classify-button");
    const errorMessage = document.getElementById("error-message");
    const resultSection = document.getElementById("result-section");

    // Menghapus pesan dan hasil sebelumnya
    errorMessage.textContent = "";
    resultSection.hidden = true;

    // Memeriksa input cerita
    if (!storyText) {
        errorMessage.textContent = "Silakan masukkan teks cerita rakyat terlebih dahulu.";
        return;
    }

    // Mengubah tombol selama proses klasifikasi
    button.disabled = true;
    button.textContent = "Sedang mengklasifikasikan...";

    try {
        // Mengirim teks ke Flask API
        const response = await fetch("/api/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                text: storyText
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.pesan || "Terjadi kesalahan.");
        }

        // Menampilkan hasil prediksi
        const hasil = data.hasil;

        document.getElementById("prediction-label").textContent =
            hasil.prediksi;

        // Menampilkan probabilitas setiap kelas
        const probabilityList = document.getElementById("probability-list");
        probabilityList.innerHTML = "";

        for (const [label, probability] of Object.entries(hasil.probabilitas)) {
            const item = document.createElement("div");
            item.className = "probability-item";

            const labelRow = document.createElement("div");
            labelRow.className = "probability-label";

            const labelName = document.createElement("span");
            labelName.textContent = label.charAt(0).toUpperCase() + label.slice(1);

            const percentage = document.createElement("span");
            percentage.textContent = probability + "%";

            labelRow.appendChild(labelName);
            labelRow.appendChild(percentage);

            const bar = document.createElement("div");
            bar.className = "progress-bar";

            const fill = document.createElement("div");
            fill.className = "progress-fill";
            fill.style.width = probability + "%";

            bar.appendChild(fill);
            item.appendChild(labelRow);
            item.appendChild(bar);

            probabilityList.appendChild(item);
        }

        // Menampilkan bagian hasil
        resultSection.hidden = false;

        // Mengarahkan tampilan ke hasil
        resultSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    } catch (error) {
        errorMessage.textContent = error.message;
    } finally {
        button.disabled = false;
        button.textContent = "✨ Klasifikasikan";
    }
}


// Mendaftarkan Service Worker
if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register("./service-worker.js") 
            .then((registration) => {
                console.log("Service Worker berhasil didaftarkan:", registration.scope);
            })
            .catch((error) => {
                console.error("Service Worker gagal didaftarkan:", error);
            });
    });
}
