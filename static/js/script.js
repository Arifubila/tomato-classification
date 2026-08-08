// ============================================================
// 1. PREVIEW IMAGE — dengan efek & reset otomatis
// ============================================================

/**
 * Menampilkan pratinjau gambar saat user memilih file.
 * Jika file dihapus, pratinjau akan direset ke placeholder.
 */
const previewImage = (event) => {
  const input = event.target;
  const preview = document.getElementById("preview");
  const file = input.files?.[0];

  if (file) {
    // Buat URL objek untuk ditampilkan
    const objectURL = URL.createObjectURL(file);

    // Set src, tambahkan efek fade-in
    preview.src = objectURL;
    preview.style.opacity = "0";
    setTimeout(() => {
      preview.style.opacity = "1";
      preview.style.transition = "opacity 0.3s ease";
    }, 50);

    // Bersihkan URL objek setelah gambar dimuat (optional)
    preview.onload = () => URL.revokeObjectURL(objectURL);
  } else {
    // Reset ke placeholder jika tidak ada file
    preview.src = ""; // atau placeholder default
    preview.style.opacity = "1";
  }
};

// ============================================================
// 2. AUTO-HIDE FLASH MESSAGES — dengan efek fade-out
// ============================================================

/**
 * Menyembunyikan semua alert secara otomatis setelah 5 detik
 * dengan efek fade-out yang halus.
 */
const autoHideAlerts = (delay = 5000) => {
  const alerts = document.querySelectorAll(".alert");

  alerts.forEach((alert) => {
    // Tambahkan transisi untuk efek fade-out
    alert.style.transition = "opacity 0.5s ease, transform 0.3s ease";

    setTimeout(() => {
      alert.style.opacity = "0";
      alert.style.transform = "translateY(-10px)";

      // Hapus dari DOM setelah animasi selesai
      setTimeout(() => {
        if (alert.parentNode) {
          alert.remove();
        }
      }, 600);
    }, delay);
  });
};

// Jalankan auto-hide saat halaman dimuat
document.addEventListener("DOMContentLoaded", () => {
  autoHideAlerts(5000);
});

// ============================================================
// 3. CONFIRM DELETE — dengan pesan yang lebih informatif
// ============================================================

/**
 * Menampilkan konfirmasi hapus dengan pesan dinamis.
 * @param {string} item - Nama item yang akan dihapus (opsional)
 * @param {string} customMessage - Pesan kustom (opsional)
 * @returns {boolean} - true jika user mengonfirmasi, false jika batal
 */
const confirmDelete = (item = "data ini", customMessage = null) => {
  const defaultMessage = `Apakah Anda yakin ingin menghapus ${item}?`;
  const message = customMessage || defaultMessage;

  // Tampilkan konfirmasi dengan gaya yang lebih jelas
  return confirm(`⚠️ ${message}`);
};

// Contoh penggunaan dengan event listener (opsional)
// document.querySelectorAll('.btn-delete').forEach((btn) => {
//   btn.addEventListener('click', (e) => {
//     const itemName = btn.dataset.item || 'data';
//     if (!confirmDelete(itemName)) {
//       e.preventDefault();
//     }
//   });
// });

// ============================================================
// 4. UTILITY — Reset form upload (opsional)
// ============================================================

/**
 * Reset input file dan pratinjau gambar.
 * Berguna saat user membatalkan upload.
 */
const resetFileInput = (inputId, previewId) => {
  const input = document.getElementById(inputId);
  const preview = document.getElementById(previewId);

  if (input) {
    input.value = ""; // Reset file input
    // Trigger change event untuk update preview
    const event = new Event("change", { bubbles: true });
    input.dispatchEvent(event);
  }

  if (preview) {
    preview.src = ""; // Kosongkan preview
    preview.style.opacity = "1";
  }
};

// ============================================================
// 5. EVENT BINDING — dengan delegation untuk dinamis
// ============================================================

// Otomatis pasang event listener ke input file dengan class .file-upload
document.addEventListener("DOMContentLoaded", () => {
  // Untuk semua input file yang memiliki class 'file-upload'
  document.querySelectorAll(".file-upload").forEach((input) => {
    input.addEventListener("change", previewImage);
  });

  // (Opsional) Tambahkan tombol reset jika ada
  document.querySelectorAll(".btn-reset-upload").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const inputId = btn.dataset.inputId || "fileInput";
      const previewId = btn.dataset.previewId || "preview";
      resetFileInput(inputId, previewId);
    });
  });
});

// ============================================================
// 6. EXPORT (jika menggunakan module)
// ============================================================

// Jika kode ini digunakan dalam lingkungan modular, ekspor fungsi
// export { previewImage, autoHideAlerts, confirmDelete, resetFileInput };
