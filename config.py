"""Program içeriği.

Kendi programını kurmak için yalnızca bu dosyayı düzenle: gün sayısı,
görevler, evreler ve kartlar. Uygulama kodunu değiştirmene gerek yok.
"""

APP_TITLE = "Denge21"
APP_SUBTITLE = "21 günlük ruh, beden ve zihin dengesi programı"

PROGRAM_DAYS = 21

# (görev adı, açıklama)
TASKS = [
    ("Uyku", "En geç 02:30'da yat / sabah 08:30-09:00'da kalk"),
    ("Beslenme", "Günde 3 dengeli öğün, 2L su"),
    ("Hareket", "Günde 20 dakika yürüyüş veya 10 dakika esneme"),
    ("Maneviyat", "Sabah 5 dk dua/şükür + 1 sayfa kısa okuma"),
    ("Ekransız Zaman", "Gün içinde toplam en az 4 saat ekran dışı"),
    ("Zihin Günlüğü", "Gece 1 soru: Huzur anım neydi? (5 dk)"),
]

# (gün aralığı, odak)
PHASES = [
    ("1-7. gün", "Bedenin şarj olması (uyku, beslenme, hafif hareket)"),
    ("8-14. gün", "Maneviyatı güçlendirme (dua, okuma, durma noktası)"),
    ("15-21. gün", "Zihinsel detoks (ekranı azaltma, hedefleri netleştirme)"),
]

# Haftalık refleksiyonun önerildiği günler
REFLECTION_DAYS = [7, 14, 21]

FOCUS_CARDS = [
    "Bugün sadece kontrol edebildiğin şeylere odaklan.",
    "Zorluklar, seni eğiten dostlardır.",
    "Az ama sürekli yapılan her şey, bereket getirir.",
    "Sabır, acıyı dondurup huzura çeviren bir ateştir.",
    "Bugün kendine şefkatle yaklaşmayı unutma.",
]

SPIRITUAL_CARDS = [
    "“Sabır, acının ilacıdır.” — Hz. Muhammed (s.a.v)",
    "“Bir kapıyı Allah kapatırsa, elbet daha hayırlısını açar.”",
    "“Allah kuluna zulmetmez, bazen geciktirir, bazen dönüştürür.”",
    "“Zorlukla beraber kolaylık vardır.” — (İnşirah, 6)",
    "“Kim Allah'a tevekkül ederse, O ona yeter.” — (Talak, 3)",
    "“Kalpler ancak Allah'ı anmakla huzur bulur.” — (Ra'd, 28)",
    "“Niyetin neyse, eline geçecek olan odur.”",
]

AYAH_CARDS = [
    "“Şüphesiz zorlukla beraber bir kolaylık vardır.” (İnşirah 94:6)",
    "“Allah sabredenlerle beraberdir.” (Bakara 2:153)",
    "“Kim Allah'a tevekkül ederse, O ona yeter.” (Talak 65:3)",
    "“Gerçek huzur, kalplerin Allah'ı anmasıyladır.” (Ra'd 13:28)",
]
