"""Denge21: 21 günlük alışkanlık ve günlük takip uygulaması (Streamlit).

Çalıştırma:  streamlit run app.py
Demo modu:   DENGE21_DEMO=1 streamlit run app.py
             (her ziyaretçiye örnek veriyle dolu, ayrı ve geçici bir veritabanı)
"""

import os
import random
from datetime import date, datetime, time, timedelta

import pandas as pd
import streamlit as st

import config
import db

DB_PATH = os.environ.get(
    "DENGE21_DB",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "denge21_plus_complete.db"),
)
DEMO_MODE = os.environ.get("DENGE21_DEMO", "").lower() in ("1", "true", "yes")
TASK_NAMES = [name for name, _ in config.TASKS]
DAYS = config.PROGRAM_DAYS

st.set_page_config(page_title=config.APP_TITLE, page_icon="🌿", layout="wide")


# --- Bağlantı ---------------------------------------------------------------
def _seed_demo(conn) -> None:
    """Demo için gerçekçi görünen örnek veri: ilk 9 gün kısmen dolu."""
    rng = random.Random(21)
    wins = [
        "10 dakika yürüdüm, kahvemi sakin içtim.",
        "Telefonu yatak odasının dışında bıraktım.",
        "Annemi aradım, uzun uzun konuştuk.",
        "Öğle yemeğini ekran karşısında yemedim.",
        "Sabah namazından sonra 1 sayfa okudum.",
    ]
    for day in range(1, 10):
        for task in TASK_NAMES:
            if rng.random() < 0.55 + day * 0.04:
                db.set_completed(conn, day, task, True)
        db.save_daily_notes(
            conn, day, rng.choice(wins),
            rng.randint(2, 4), rng.randint(2, 5), rng.randint(1, 4),
        )
    today = date.today()
    for back in range(7, 0, -1):
        d = today - timedelta(days=back)
        start = time(rng.choice([23, 0, 1]), rng.choice([0, 15, 30]))
        end = time(rng.choice([7, 8]), rng.choice([0, 30]))
        db.save_daily_entry(
            conn, d.isoformat(),
            sleep_start=str(start), sleep_end=str(end),
            sleep_quality=rng.randint(2, 5), sleep_notes="",
            morning_routine=int(rng.random() < 0.7), evening_routine=int(rng.random() < 0.5),
            mini_goals="Yürüyüş, 20 sayfa kitap", reflection="",
            gratitude="Sağlığım için", intention="Sakin kalmak",
        )


@st.cache_resource
def _file_connection(path: str):
    return db.connect(path, DAYS, TASK_NAMES)


def get_conn():
    if not DEMO_MODE:
        return _file_connection(DB_PATH)
    if "demo_conn" not in st.session_state:
        conn = db.connect(":memory:", DAYS, TASK_NAMES)
        _seed_demo(conn)
        st.session_state.demo_conn = conn
    return st.session_state.demo_conn


conn = get_conn()


def _parse_time(value, default: str) -> time:
    try:
        return datetime.strptime(str(value)[:5], "%H:%M").time()
    except (TypeError, ValueError):
        return datetime.strptime(default, "%H:%M").time()


def _int_or(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# --- Başlık -----------------------------------------------------------------
st.title(f"🌿 {config.APP_TITLE}")
st.caption(config.APP_SUBTITLE)
if DEMO_MODE:
    st.info(
        "**Demo modu:** örnek verilerle dolu, sana özel geçici bir oturum. "
        "Girdiklerin kimseyle paylaşılmaz ve sayfayı kapatınca silinir."
    )

# --- Kenar çubuğu -----------------------------------------------------------
progress_df = db.get_progress(conn)
progress_df = progress_df[progress_df["task"].isin(TASK_NAMES)]

with st.sidebar:
    st.header("🎯 Program")
    with st.expander(f"{DAYS} günlük planın özeti"):
        st.markdown("\n".join(f"- **{rng}**: {focus}" for rng, focus in config.PHASES))

    st.divider()
    st.header("📊 Toplam ilerleme")
    total = DAYS * len(TASK_NAMES)
    done = int(progress_df["completed"].sum())
    pct = round(done / total * 100) if total else 0
    st.metric("Tamamlanan görev", f"{done} / {total}", delta=f"%{pct}")
    st.progress(pct / 100)

    st.divider()
    st.header("💫 Günün hatırlatması")
    if "daily_focus" not in st.session_state:
        st.session_state.daily_focus = random.choice(config.FOCUS_CARDS)
    st.info(st.session_state.daily_focus)
    if st.button("🔄 Yeni kart"):
        st.session_state.daily_focus = random.choice(config.FOCUS_CARDS)
        st.rerun()

    st.divider()
    with st.popover("⚠️ Tüm ilerlemeyi sıfırla"):
        st.write("Görev işaretleri ve günlük notlar silinir. Detaylı günlük kalır.")
        if st.button("Evet, sıfırla", type="primary"):
            db.reset_all(conn)
            st.rerun()

# --- Sekmeler ---------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["📋 Günlük takip", "📊 İlerleme analizi", "📖 Detaylı günlük", "🧘 Manevi merkezlenme"]
)

with tab1:
    sel_day = st.slider(f"Gün seç (1-{DAYS})", 1, DAYS, 1, key="day_slider")
    day_df = progress_df[progress_df["day"] == sel_day].set_index("task")["completed"]

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Gün {sel_day} görevleri")
        for task, desc in config.TASKS:
            checked = bool(day_df.get(task, 0))
            new_val = st.checkbox(f"**{task}** · {desc}", value=checked, key=f"c_{sel_day}_{task}")
            if new_val != checked:
                db.set_completed(conn, sel_day, task, new_val)
                st.rerun()
    with col2:
        day_done = int(day_df.sum())
        st.metric("Bugünün durumu", f"{day_done} / {len(TASK_NAMES)}")
        st.progress(day_done / len(TASK_NAMES))
        b1, b2 = st.columns(2)
        if b1.button("✅ Hepsi", key=f"all_{sel_day}", width="stretch"):
            for task in TASK_NAMES:
                db.set_completed(conn, sel_day, task, True)
            st.rerun()
        if b2.button("↺ Temizle", key=f"none_{sel_day}", width="stretch"):
            for task in TASK_NAMES:
                db.set_completed(conn, sel_day, task, False)
            st.rerun()

    st.divider()
    st.subheader(f"Gün {sel_day} notları")
    notes = db.get_daily_notes(conn, sel_day)
    with st.form(key=f"notes_{sel_day}"):
        small_win = st.text_area(
            "🌸 Günün küçük kazanımı",
            value=notes.get("small_win") or "",
            placeholder="Örneğin: Bugün 10 dakika yürüdüm, kahvemi sakin içtim.",
        )
        st.markdown("**🔋 Enerji seviyesi (1-5)**")
        e1, e2, e3 = st.columns(3)
        morning = e1.slider("Sabah", 1, 5, _int_or(notes.get("energy_morning"), 3))
        noon = e2.slider("Öğle", 1, 5, _int_or(notes.get("energy_noon"), 3))
        evening = e3.slider("Akşam", 1, 5, _int_or(notes.get("energy_evening"), 3))
        if st.form_submit_button(f"💾 Gün {sel_day} notlarını kaydet"):
            db.save_daily_notes(conn, sel_day, small_win, morning, noon, evening)
            st.success("Kaydedildi 🌿")

with tab2:
    pivot = progress_df.pivot_table(
        index="day", columns="task", values="completed", aggfunc="first"
    ).fillna(0).astype(int)[TASK_NAMES]

    st.subheader("Günlük tamamlama oranı (%)")
    rate = (pivot.sum(axis=1) / len(TASK_NAMES) * 100).rename("Tamamlama %")
    st.bar_chart(rate, height=260, color="#3a7d5c")

    st.subheader("Görev tablosu")
    st.dataframe(
        pivot.replace({1: "✅", 0: "·"}).rename_axis("Gün"),
        width="stretch", height=420,
    )

    st.subheader("Enerji seyri")
    energy = db.get_all_notes(conn)
    if energy.empty:
        st.info("Henüz enerji verisi yok. Günlük takip sekmesinden not kaydet.")
    else:
        energy = energy.set_index("day")[["energy_morning", "energy_noon", "energy_evening"]]
        energy.columns = ["Sabah", "Öğle", "Akşam"]
        energy["Ortalama"] = energy.mean(axis=1).round(2)
        st.line_chart(energy, height=260)

with tab3:
    today = date.today()
    st.subheader(f"📅 {today.strftime('%d.%m.%Y')} kaydı")
    entry = db.get_daily_entry(conn, today.isoformat())

    with st.form("detailed_daily_form"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**💤 Uyku**")
            sleep_start = st.time_input("Yatış", _parse_time(entry.get("sleep_start"), "23:00"))
            sleep_end = st.time_input("Kalkış", _parse_time(entry.get("sleep_end"), "07:00"))
            sleep_quality = st.slider("Uyku kalitesi (1-5)", 1, 5, _int_or(entry.get("sleep_quality"), 3))
            sleep_notes = st.text_area("Uyku notları", value=entry.get("sleep_notes") or "")
        with c2:
            st.markdown("**🌅 Rutinler**")
            morning_routine = st.checkbox("Sabah rutini tamam", value=bool(entry.get("morning_routine")))
            evening_routine = st.checkbox("Akşam rutini tamam", value=bool(entry.get("evening_routine")))
            mini_goals = st.text_area("🎯 Küçük hedefler", value=entry.get("mini_goals") or "")
        intention = st.text_input("🤲 Bugünün niyeti", value=entry.get("intention") or "")
        gratitude = st.text_input("🙏 Bugünün şükrü", value=entry.get("gratitude") or "")
        reflection = st.text_area("🪞 Gün sonu notu", value=entry.get("reflection") or "")

        if st.form_submit_button("💾 Günlüğü kaydet"):
            db.save_daily_entry(
                conn, today.isoformat(),
                sleep_start=str(sleep_start), sleep_end=str(sleep_end),
                sleep_quality=sleep_quality, sleep_notes=sleep_notes,
                morning_routine=int(morning_routine), evening_routine=int(evening_routine),
                mini_goals=mini_goals, reflection=reflection,
                gratitude=gratitude, intention=intention,
            )
            st.success(f"Kaydedildi. Uyku süresi: {db.sleep_hours(str(sleep_start), str(sleep_end))} saat 🌟")

    entries = db.get_all_entries(conn)
    st.divider()
    st.subheader("📊 Geçmiş")
    if entries.empty:
        st.info("Henüz detaylı günlük kaydı yok.")
    else:
        hist = entries.assign(day=pd.to_datetime(entries["day"])).set_index("day")
        m1, m2 = st.columns(2)
        m1.metric("Ortalama uyku", f"{hist['sleep_hours'].mean():.1f} saat")
        m2.metric("Ortalama kalite", f"{hist['sleep_quality'].mean():.1f} / 5")
        g1, g2 = st.columns(2)
        g1.caption("🕒 Uyku süresi (saat)")
        g1.line_chart(hist["sleep_hours"], height=200)
        g2.caption("🌙 Uyku kalitesi")
        g2.line_chart(hist["sleep_quality"], height=200)
        with st.expander("🗂️ Tüm kayıtlar"):
            st.dataframe(
                entries[["day", "sleep_hours", "intention", "gratitude", "mini_goals"]]
                .sort_values("day", ascending=False),
                width="stretch", hide_index=True,
            )

with tab4:
    st.subheader("🕊️ Günün hatırlatması")
    if "spiritual_card" not in st.session_state:
        st.session_state.spiritual_card = random.choice(config.SPIRITUAL_CARDS)
    st.info(f"**{st.session_state.spiritual_card}**")
    k1, k2 = st.columns(2)
    if k1.button("🎴 Yeni kart çek"):
        st.session_state.spiritual_card = random.choice(config.SPIRITUAL_CARDS)
        st.rerun()
    if k2.button("📖 Ayet kartı çek"):
        st.session_state.spiritual_card = random.choice(config.AYAH_CARDS)
        st.rerun()

    st.divider()
    st.subheader("📝 Haftalık refleksiyon")
    st.caption(
        "Önerilen günler: " + ", ".join(f"{d}." for d in config.REFLECTION_DAYS) + " gün"
    )
    with st.form("weekly_reflection_form", clear_on_submit=True):
        draining = st.text_area("Bu hafta seni en çok yoran şey neydi?")
        strengthening = st.text_area("Bu hafta seni en çok güçlendiren şey neydi?")
        learned = st.text_area("Bu hafta kendin hakkında ne öğrendin?")
        if st.form_submit_button("💾 Refleksiyonu kaydet"):
            db.save_weekly_reflection(conn, draining, strengthening, learned)
            st.success("Kaydedildi 📝")
    past = db.get_weekly_reflections(conn)
    if not past.empty:
        with st.expander(f"Geçmiş refleksiyonlar ({len(past)})"):
            st.dataframe(past, width="stretch", hide_index=True)

# --- Dışa aktarma -----------------------------------------------------------
st.divider()
st.subheader("📤 Verilerini indir")
x1, x2, x3, x4 = st.columns(4)
exports = [
    (x1, "Görevler", db.get_progress(conn), "denge21_gorevler.csv"),
    (x2, "Günlük notlar", db.get_all_notes(conn), "denge21_notlar.csv"),
    (x3, "Detaylı günlük", db.get_all_entries(conn), "denge21_gunluk.csv"),
    (x4, "Haftalık refleksiyon", db.get_weekly_reflections(conn), "denge21_refleksiyon.csv"),
]
for col, label, df, fname in exports:
    col.download_button(
        f"📥 {label} (CSV)",
        df.to_csv(index=False).encode("utf-8-sig"),
        file_name=fname, mime="text/csv", width="stretch",
    )

st.caption("✨ Denge bir varış değil, bir yaşam biçimidir.")
