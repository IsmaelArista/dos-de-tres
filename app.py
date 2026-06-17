"""
Dos de Tres - Sistema web para la evaluación efectiva del aprendizaje
Proyecto final - Administración de Proyectos de TI
ESCOM-IPN | 7AV1 | Junio 2026

Integrantes:
    - Mérida Sandoval Alana Daniela
    - Arista Romero Juan Ismael
    - Torres Flores César Fernando
"""

import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import json

# =============================================================================
# CONFIGURACIÓN DE PÁGINA
# =============================================================================
st.set_page_config(
    page_title="Dos de Tres | Plataforma educativa",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta de colores institucional (guinda IPN + acentos)
COLOR_PRIMARIO = "#600070"
COLOR_SECUNDARIO = "#9C27B0"
COLOR_EXITO = "#2E7D32"
COLOR_ADVERTENCIA = "#F57C00"
COLOR_PELIGRO = "#C62828"
COLOR_FONDO = "#FAFAFA"

DB_PATH = Path(__file__).parent / "database.db"
CSV_PATH = Path(__file__).parent / "preguntas.csv"


# =============================================================================
# ESTILOS PERSONALIZADOS (CSS)
# =============================================================================
def cargar_estilos():
    """Inyecta CSS personalizado para que la app no parezca un Streamlit genérico."""
    st.markdown("""
    <style>
        /* Tipografía y fondo */
        .main { background-color: #FAFAFA; }
        html, body, [class*="css"] {
            font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
        }

        /* Botones primarios */
        .stButton > button {
            background: linear-gradient(135deg, #600070 0%, #9C27B0 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.55rem 1.2rem;
            font-weight: 600;
            transition: all 0.25s ease;
            box-shadow: 0 2px 5px rgba(96, 0, 112, 0.2);
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(96, 0, 112, 0.35);
            background: linear-gradient(135deg, #4A0058 0%, #7B1FA2 100%);
            color: white;
        }

        /* Tarjetas/contenedores */
        .tarjeta {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border-left: 4px solid #600070;
            margin-bottom: 1rem;
        }
        .tarjeta-exito { border-left-color: #2E7D32; }
        .tarjeta-warn  { border-left-color: #F57C00; }
        .tarjeta-rojo  { border-left-color: #C62828; }

        /* KPIs / Métricas grandes */
        .kpi {
            background: white;
            padding: 1.25rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
        .kpi-valor {
            font-size: 2.2rem;
            font-weight: 700;
            color: #600070;
            margin: 0;
        }
        .kpi-etiqueta {
            font-size: 0.85rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 0;
        }

        /* Encabezado principal */
        .header-principal {
            background: linear-gradient(135deg, #600070 0%, #9C27B0 100%);
            padding: 1.5rem 2rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(96, 0, 112, 0.25);
        }
        .header-principal h1 {
            color: white;
            margin: 0;
            font-size: 1.8rem;
        }
        .header-principal p {
            color: rgba(255,255,255,0.9);
            margin: 0.25rem 0 0 0;
            font-size: 0.95rem;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #FAFAFA 0%, #F0F0F5 100%);
        }
        [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: #600070;
        }

        /* Etiquetas de estado */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .badge-exito  { background: #E8F5E9; color: #2E7D32; }
        .badge-warn   { background: #FFF3E0; color: #F57C00; }
        .badge-rojo   { background: #FFEBEE; color: #C62828; }

        /* Pregunta de examen */
        .pregunta-card {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border-top: 4px solid #600070;
        }
        .pregunta-texto {
            font-size: 1.15rem;
            color: #222;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }

        /* Ocultar elementos por defecto de Streamlit */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        .stDeployButton { display: none; }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# BASE DE DATOS
# =============================================================================
def hash_password(password: str) -> str:
    """Hash SHA-256 de la contraseña (suficiente para prototipo académico)."""
    return hashlib.sha256(password.encode()).hexdigest()


def get_conn():
    """Conexión a SQLite con row_factory para acceso por nombre de columna."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_bd():
    """Crea las tablas si no existen y carga datos semilla."""
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol TEXT NOT NULL CHECK(rol IN ('docente','estudiante','admin')),
            grupo TEXT,
            fecha_registro TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS preguntas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            materia TEXT NOT NULL,
            tema TEXT NOT NULL,
            enunciado TEXT NOT NULL,
            opcion_a TEXT NOT NULL,
            opcion_b TEXT NOT NULL,
            opcion_c TEXT NOT NULL,
            opcion_d TEXT NOT NULL,
            respuesta_correcta TEXT NOT NULL CHECK(respuesta_correcta IN ('A','B','C','D')),
            dificultad TEXT NOT NULL CHECK(dificultad IN ('Baja','Media','Alta')),
            explicacion TEXT
        );

        CREATE TABLE IF NOT EXISTS evaluaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_docente INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            materia TEXT NOT NULL,
            descripcion TEXT,
            preguntas_ids TEXT NOT NULL,
            fecha_creacion TEXT DEFAULT (datetime('now','localtime')),
            activa INTEGER DEFAULT 1,
            FOREIGN KEY (id_docente) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_evaluacion INTEGER NOT NULL,
            id_estudiante INTEGER NOT NULL,
            id_pregunta INTEGER NOT NULL,
            respuesta_dada TEXT,
            es_correcta INTEGER NOT NULL,
            fecha TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (id_evaluacion) REFERENCES evaluaciones(id),
            FOREIGN KEY (id_estudiante) REFERENCES usuarios(id),
            FOREIGN KEY (id_pregunta) REFERENCES preguntas(id)
        );

        CREATE TABLE IF NOT EXISTS evaluaciones_completadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_evaluacion INTEGER NOT NULL,
            id_estudiante INTEGER NOT NULL,
            puntaje REAL NOT NULL,
            total_preguntas INTEGER NOT NULL,
            aciertos INTEGER NOT NULL,
            fecha TEXT DEFAULT (datetime('now','localtime')),
            UNIQUE(id_evaluacion, id_estudiante)
        );
    """)
    conn.commit()

    # Usuarios semilla
    cur.execute("SELECT COUNT(*) as c FROM usuarios")
    if cur.fetchone()["c"] == 0:
        usuarios_semilla = [
            ("Profesora Rocío Palacios",  "rocio@escom.ipn.mx",    hash_password("docente123"),    "docente",    "7AV1"),
            ("Prof. Carlos Hernández",     "carlos@escom.ipn.mx",   hash_password("docente123"),    "docente",    "7AV1"),
            ("Ismael Arista",              "ismael@alumno.ipn.mx",  hash_password("alumno123"),     "estudiante", "7AV1"),
            ("Alana Mérida",               "alana@alumno.ipn.mx",   hash_password("alumno123"),     "estudiante", "7AV1"),
            ("Fernando Torres",            "fernando@alumno.ipn.mx",hash_password("alumno123"),     "estudiante", "7AV1"),
            ("María González",             "maria@alumno.ipn.mx",   hash_password("alumno123"),     "estudiante", "7AV1"),
            ("Luis Ramírez",               "luis@alumno.ipn.mx",    hash_password("alumno123"),     "estudiante", "7AV1"),
            ("Sofía Martínez",             "sofia@alumno.ipn.mx",   hash_password("alumno123"),     "estudiante", "7AV1"),
            ("Diego Vázquez",              "diego@alumno.ipn.mx",   hash_password("alumno123"),     "estudiante", "7AV1"),
            ("Andrea López",               "andrea@alumno.ipn.mx",  hash_password("alumno123"),     "estudiante", "7AV1"),
            ("Administrador",              "admin@escom.ipn.mx",    hash_password("admin123"),      "admin",      None),
        ]
        cur.executemany(
            "INSERT INTO usuarios (nombre, correo, password_hash, rol, grupo) VALUES (?,?,?,?,?)",
            usuarios_semilla
        )
        conn.commit()

    # Preguntas semilla
    cur.execute("SELECT COUNT(*) as c FROM preguntas")
    if cur.fetchone()["c"] == 0 and CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH, keep_default_na=False)
        for _, r in df.iterrows():
            cur.execute("""
                INSERT INTO preguntas (materia, tema, enunciado, opcion_a, opcion_b, opcion_c, opcion_d,
                                       respuesta_correcta, dificultad, explicacion)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (r["materia"], r["tema"], r["enunciado"], r["opcion_a"], r["opcion_b"],
                  r["opcion_c"], r["opcion_d"], r["respuesta_correcta"], r["dificultad"],
                  r.get("explicacion", "")))
        conn.commit()

    # Evaluaciones de muestra
    cur.execute("SELECT COUNT(*) as c FROM evaluaciones")
    if cur.fetchone()["c"] == 0:
        cur.execute("SELECT id FROM usuarios WHERE rol='docente' LIMIT 1")
        docente = cur.fetchone()
        if docente:
            cur.execute("SELECT id FROM preguntas WHERE materia='Matemáticas' LIMIT 10")
            ids = [str(r["id"]) for r in cur.fetchall()]
            if ids:
                cur.execute("""
                    INSERT INTO evaluaciones (id_docente, titulo, materia, descripcion, preguntas_ids)
                    VALUES (?,?,?,?,?)
                """, (docente["id"], "Diagnóstico de Matemáticas - Unidad 1",
                      "Matemáticas",
                      "Evaluación inicial para identificar vacíos en álgebra, geometría y aritmética.",
                      json.dumps([int(i) for i in ids])))

            cur.execute("SELECT id FROM preguntas WHERE materia='Programación' LIMIT 8")
            ids = [str(r["id"]) for r in cur.fetchall()]
            if ids:
                cur.execute("""
                    INSERT INTO evaluaciones (id_docente, titulo, materia, descripcion, preguntas_ids)
                    VALUES (?,?,?,?,?)
                """, (docente["id"], "Fundamentos de Programación",
                      "Programación",
                      "Evaluación de conceptos básicos: variables, ciclos, condicionales y funciones.",
                      json.dumps([int(i) for i in ids])))

            cur.execute("SELECT id FROM preguntas WHERE materia='Física' LIMIT 10")
            ids = [str(r["id"]) for r in cur.fetchall()]
            if ids:
                cur.execute("""
                    INSERT INTO evaluaciones (id_docente, titulo, materia, descripcion, preguntas_ids)
                    VALUES (?,?,?,?,?)
                """, (docente["id"], "Diagnóstico de Física - Unidad 1",
                      "Física",
                      "Evaluación inicial de cinemática, dinámica, energía y ondas.",
                      json.dumps([int(i) for i in ids])))

            cur.execute("SELECT id FROM preguntas WHERE materia='Química' LIMIT 10")
            ids = [str(r["id"]) for r in cur.fetchall()]
            if ids:
                cur.execute("""
                    INSERT INTO evaluaciones (id_docente, titulo, materia, descripcion, preguntas_ids)
                    VALUES (?,?,?,?,?)
                """, (docente["id"], "Diagnóstico de Química - Unidad 1",
                      "Química",
                      "Evaluación de tabla periódica, enlace químico, reacciones y ácidos/bases.",
                      json.dumps([int(i) for i in ids])))

            conn.commit()

    conn.close()


# =============================================================================
# AUTENTICACIÓN
# =============================================================================
def login(correo: str, password: str):
    conn = get_conn()
    user = conn.execute(
        "SELECT * FROM usuarios WHERE correo=? AND password_hash=?",
        (correo, hash_password(password))
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]


# =============================================================================
# COMPONENTES UI REUTILIZABLES
# =============================================================================
def header(titulo: str, subtitulo: str = ""):
    st.markdown(f"""
        <div class="header-principal">
            <h1>{titulo}</h1>
            <p>{subtitulo}</p>
        </div>
    """, unsafe_allow_html=True)


def kpi(valor, etiqueta, color=COLOR_PRIMARIO):
    st.markdown(f"""
        <div class="kpi">
            <p class="kpi-valor" style="color:{color};">{valor}</p>
            <p class="kpi-etiqueta">{etiqueta}</p>
        </div>
    """, unsafe_allow_html=True)


def badge(texto, tipo="exito"):
    return f'<span class="badge badge-{tipo}">{texto}</span>'


# =============================================================================
# PANTALLA DE LOGIN
# =============================================================================
def pantalla_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(f"""
            <div style="text-align:center; padding: 2rem 0 1rem 0;">
                <h1 style="color:{COLOR_PRIMARIO}; font-size: 3rem; margin: 0;">🎯 Dos de Tres</h1>
                <p style="color:#666; font-size: 1.1rem; margin-top: 0.5rem;">
                    Plataforma de evaluación efectiva del aprendizaje
                </p>
                <p style="color:#999; font-size: 0.85rem; margin-top: 0.25rem;">
                    Escuela Superior de Cómputo · IPN
                </p>
            </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("### Iniciar sesión")
            correo = st.text_input("Correo electrónico", placeholder="usuario@escom.ipn.mx")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")

            if st.button("Ingresar", use_container_width=True, type="primary"):
                user = login(correo, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas. Verifica tu correo y contraseña.")

        with st.expander("🔑 Credenciales de demostración"):
            st.markdown("""
            | Rol | Correo | Contraseña |
            |---|---|---|
            | 👨‍🏫 Docente | `rocio@escom.ipn.mx` | `docente123` |
            | 👨‍🎓 Estudiante | `ismael@alumno.ipn.mx` | `alumno123` |
            | ⚙️ Admin | `admin@escom.ipn.mx` | `admin123` |
            """)


# =============================================================================
# DASHBOARD DEL ESTUDIANTE
# =============================================================================
def vista_estudiante():
    user = st.session_state.user
    header(f"Hola, {user['nombre'].split()[0]} 👋",
           f"Aquí podrás realizar tus evaluaciones y consultar tu progreso académico.")

    conn = get_conn()

    # Sub-navegación dentro del rol estudiante
    seccion = st.sidebar.radio(
        "📚 Menú",
        ["🏠 Inicio", "📝 Evaluaciones disponibles", "📊 Mi diagnóstico", "📈 Mi historial"],
        label_visibility="collapsed"
    )

    # -------- INICIO --------
    if seccion == "🏠 Inicio":
        # KPIs del estudiante
        completadas = conn.execute(
            "SELECT COUNT(*) as c FROM evaluaciones_completadas WHERE id_estudiante=?",
            (user["id"],)
        ).fetchone()["c"]

        disponibles = conn.execute("""
            SELECT COUNT(*) as c FROM evaluaciones e
            WHERE e.activa=1 AND e.id NOT IN (
                SELECT id_evaluacion FROM evaluaciones_completadas WHERE id_estudiante=?
            )
        """, (user["id"],)).fetchone()["c"]

        promedio = conn.execute(
            "SELECT AVG(puntaje) as p FROM evaluaciones_completadas WHERE id_estudiante=?",
            (user["id"],)
        ).fetchone()["p"] or 0

        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi(disponibles, "Evaluaciones pendientes", COLOR_ADVERTENCIA)
        with c2: kpi(completadas, "Evaluaciones completadas", COLOR_EXITO)
        with c3: kpi(f"{promedio:.0f}%", "Promedio general", COLOR_PRIMARIO)
        with c4:
            # Temas dominados
            dominados = conn.execute("""
                SELECT COUNT(DISTINCT p.tema) as c
                FROM resultados r
                JOIN preguntas p ON p.id = r.id_pregunta
                WHERE r.id_estudiante=? AND r.es_correcta=1
            """, (user["id"],)).fetchone()["c"]
            kpi(dominados, "Temas trabajados", COLOR_SECUNDARIO)

        st.markdown("### 📌 Próximas acciones recomendadas")
        if disponibles > 0:
            st.markdown(f"""
                <div class="tarjeta tarjeta-warn">
                    <strong>Tienes {disponibles} evaluación(es) pendiente(s).</strong><br>
                    Dirígete a <em>Evaluaciones disponibles</em> en el menú lateral para comenzar.
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="tarjeta tarjeta-exito">
                    <strong>¡Excelente!</strong> Has completado todas las evaluaciones disponibles.
                    Revisa tu diagnóstico para identificar áreas de mejora.
                </div>
            """, unsafe_allow_html=True)

    # -------- EVALUACIONES DISPONIBLES --------
    elif seccion == "📝 Evaluaciones disponibles":
        st.markdown("### Evaluaciones por realizar")

        # Si hay una evaluación en curso, mostrar el formulario
        if "evaluacion_actual" in st.session_state:
            realizar_evaluacion(conn)
            return

        evals = conn.execute("""
            SELECT e.*, u.nombre as docente
            FROM evaluaciones e
            JOIN usuarios u ON u.id = e.id_docente
            WHERE e.activa=1 AND e.id NOT IN (
                SELECT id_evaluacion FROM evaluaciones_completadas WHERE id_estudiante=?
            )
            ORDER BY e.fecha_creacion DESC
        """, (user["id"],)).fetchall()

        if not evals:
            st.info("🎉 No tienes evaluaciones pendientes en este momento.")
        else:
            for e in evals:
                ids = json.loads(e["preguntas_ids"])
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"#### {e['titulo']}")
                        st.caption(f"{e['materia']}  ·  {e['docente']}  ·  {len(ids)} preguntas")
                        st.write(e["descripcion"] or "")
                    with c2:
                        if st.button("Comenzar", key=f"start_{e['id']}", use_container_width=True):
                            st.session_state.evaluacion_actual = {
                                "id": e["id"],
                                "titulo": e["titulo"],
                                "preguntas_ids": ids,
                                "respuestas": {},
                                "pregunta_actual": 0
                            }
                            st.rerun()

    # -------- DIAGNÓSTICO --------
    elif seccion == "📊 Mi diagnóstico":
        st.markdown("### 🎯 Diagnóstico personalizado")
        st.caption("Identificación de tus fortalezas y áreas de oportunidad por tema.")

        df = pd.read_sql("""
            SELECT p.materia, p.tema, p.dificultad,
                   COUNT(*) as intentos,
                   SUM(r.es_correcta) as aciertos
            FROM resultados r
            JOIN preguntas p ON p.id = r.id_pregunta
            WHERE r.id_estudiante=?
            GROUP BY p.materia, p.tema
            ORDER BY p.materia, p.tema
        """, conn, params=(user["id"],))

        if df.empty:
            st.info("Aún no has realizado evaluaciones. Completa al menos una para ver tu diagnóstico.")
        else:
            df["dominio_pct"] = (df["aciertos"] / df["intentos"] * 100).round(0)
            df["estado"] = df["dominio_pct"].apply(
                lambda x: "Dominado" if x >= 80 else ("En proceso" if x >= 50 else "Requiere refuerzo")
            )

            # Resumen visual
            c1, c2, c3 = st.columns(3)
            with c1: kpi(int((df["estado"]=="Dominado").sum()),       "Temas dominados",     COLOR_EXITO)
            with c2: kpi(int((df["estado"]=="En proceso").sum()),     "En proceso",          COLOR_ADVERTENCIA)
            with c3: kpi(int((df["estado"]=="Requiere refuerzo").sum()), "Requieren refuerzo", COLOR_PELIGRO)

            st.markdown("#### Desempeño por tema")
            fig = px.bar(
                df.sort_values("dominio_pct"),
                x="dominio_pct", y="tema", color="materia",
                orientation="h",
                color_discrete_sequence=[COLOR_PRIMARIO, COLOR_SECUNDARIO, "#E91E63", "#FF9800"],
                labels={"dominio_pct": "% de dominio", "tema": "Tema"},
                text=df.sort_values("dominio_pct")["dominio_pct"].astype(str) + "%"
            )
            fig.update_layout(
                plot_bgcolor="white",
                height=max(300, 40 * len(df)),
                margin=dict(l=10, r=10, t=20, b=10),
                xaxis=dict(range=[0,105], gridcolor="#EEE"),
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

            # Recomendaciones específicas
            st.markdown("#### 💡 Recomendaciones para reforzar")
            criticos = df[df["estado"]=="Requiere refuerzo"]
            if criticos.empty:
                st.success("¡Buen trabajo! No tienes temas en estado crítico.")
            else:
                for _, row in criticos.iterrows():
                    st.markdown(f"""
                        <div class="tarjeta tarjeta-rojo">
                            <strong>📕 {row['tema']}</strong> ({row['materia']})<br>
                            Dominio actual: <strong>{row['dominio_pct']:.0f}%</strong>
                            ({row['aciertos']} de {row['intentos']} respuestas correctas)<br>
                            <em>Recomendación: dedica tiempo extra a este tema antes de avanzar a contenidos relacionados.</em>
                        </div>
                    """, unsafe_allow_html=True)

    # -------- HISTORIAL --------
    elif seccion == "📈 Mi historial":
        st.markdown("### 📜 Historial de evaluaciones")

        hist = pd.read_sql("""
            SELECT ec.fecha, e.titulo, e.materia, ec.puntaje, ec.aciertos, ec.total_preguntas
            FROM evaluaciones_completadas ec
            JOIN evaluaciones e ON e.id = ec.id_evaluacion
            WHERE ec.id_estudiante=?
            ORDER BY ec.fecha DESC
        """, conn, params=(user["id"],))

        if hist.empty:
            st.info("Aún no has completado ninguna evaluación.")
        else:
            hist["fecha"] = pd.to_datetime(hist["fecha"]).dt.strftime("%d/%m/%Y %H:%M")
            hist["resultado"] = hist["aciertos"].astype(str) + " / " + hist["total_preguntas"].astype(str)
            hist["puntaje"] = hist["puntaje"].round(0).astype(int).astype(str) + "%"

            st.dataframe(
                hist[["fecha", "titulo", "materia", "resultado", "puntaje"]],
                column_config={
                    "fecha":    "Fecha",
                    "titulo":   "Evaluación",
                    "materia":  "Materia",
                    "resultado":"Resultado",
                    "puntaje":  "Calificación",
                },
                hide_index=True,
                use_container_width=True
            )

            # Evolución del aprendizaje
            if len(hist) > 1:
                st.markdown("#### Evolución de tu puntaje")
                hist_g = hist.copy()
                hist_g["puntaje_num"] = hist_g["puntaje"].str.replace("%","").astype(int)
                hist_g = hist_g.iloc[::-1].reset_index(drop=True)
                hist_g["intento"] = range(1, len(hist_g)+1)
                fig = px.line(hist_g, x="intento", y="puntaje_num", markers=True,
                              labels={"intento":"Intento","puntaje_num":"Puntaje (%)"})
                fig.update_traces(line_color=COLOR_PRIMARIO, line_width=3, marker=dict(size=10))
                fig.update_layout(plot_bgcolor="white", yaxis=dict(range=[0,105], gridcolor="#EEE"),
                                  xaxis=dict(gridcolor="#EEE"))
                st.plotly_chart(fig, use_container_width=True)

    conn.close()


def realizar_evaluacion(conn):
    """Pantalla para responder las preguntas de una evaluación."""
    ev = st.session_state.evaluacion_actual
    user = st.session_state.user
    total = len(ev["preguntas_ids"])
    idx = ev["pregunta_actual"]

    # Barra de progreso
    progreso = (idx) / total
    st.progress(progreso, text=f"Pregunta {idx+1} de {total}")

    if idx >= total:
        # Calcular resultado
        aciertos = sum(1 for v in ev["respuestas"].values() if v["es_correcta"])
        puntaje = (aciertos / total) * 100

        # Guardar en BD
        conn.execute("""
            INSERT OR REPLACE INTO evaluaciones_completadas
            (id_evaluacion, id_estudiante, puntaje, total_preguntas, aciertos)
            VALUES (?,?,?,?,?)
        """, (ev["id"], user["id"], puntaje, total, aciertos))

        for pid, info in ev["respuestas"].items():
            conn.execute("""
                INSERT INTO resultados (id_evaluacion, id_estudiante, id_pregunta, respuesta_dada, es_correcta)
                VALUES (?,?,?,?,?)
            """, (ev["id"], user["id"], pid, info["respuesta"], 1 if info["es_correcta"] else 0))

        conn.commit()

        # Pantalla de resultados
        st.balloons()
        st.markdown(f"""
            <div class="tarjeta tarjeta-exito" style="text-align:center; padding:2rem;">
                <h2 style="color:#2E7D32; margin-top:0;">✅ Evaluación completada</h2>
                <h1 style="font-size:3rem; color:#600070; margin: 1rem 0;">{puntaje:.0f}%</h1>
                <p>Respondiste correctamente <strong>{aciertos} de {total}</strong> preguntas.</p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("Volver al inicio", use_container_width=True):
            del st.session_state.evaluacion_actual
            st.rerun()
        return

    # Mostrar pregunta actual
    pid = ev["preguntas_ids"][idx]
    p = conn.execute("SELECT * FROM preguntas WHERE id=?", (pid,)).fetchone()

    st.markdown(f"""
        <div class="pregunta-card">
            <p style="color:#999; font-size:0.85rem; margin:0;">
                {p['materia']} · {p['tema']} · Dificultad: {p['dificultad']}
            </p>
            <p class="pregunta-texto">{p['enunciado']}</p>
        </div>
    """, unsafe_allow_html=True)

    opciones = {
        "A": p["opcion_a"],
        "B": p["opcion_b"],
        "C": p["opcion_c"],
        "D": p["opcion_d"]
    }

    seleccion = st.radio(
        "Selecciona tu respuesta:",
        options=list(opciones.keys()),
        format_func=lambda x: f"{x}.  {opciones[x]}",
        key=f"q_{pid}",
        index=None
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅️ Cancelar evaluación", use_container_width=True):
            del st.session_state.evaluacion_actual
            st.rerun()
    with col2:
        if st.button("Siguiente ➡️", use_container_width=True, type="primary", disabled=(seleccion is None)):
            ev["respuestas"][pid] = {
                "respuesta": seleccion,
                "es_correcta": seleccion == p["respuesta_correcta"]
            }
            ev["pregunta_actual"] += 1
            st.rerun()


# =============================================================================
# DASHBOARD DEL DOCENTE
# =============================================================================
def vista_docente():
    user = st.session_state.user
    header(f"Panel docente",
           f"Bienvenido/a, {user['nombre']}. Gestiona tus evaluaciones y consulta el progreso de tu grupo.")

    conn = get_conn()

    seccion = st.sidebar.radio(
        "👨‍🏫 Menú",
        ["📊 Dashboard del grupo", "📝 Mis evaluaciones", "➕ Crear evaluación", "🎯 Análisis por tema"],
        label_visibility="collapsed"
    )

    # -------- DASHBOARD DEL GRUPO --------
    if seccion == "📊 Dashboard del grupo":
        # KPIs generales
        total_alumnos = conn.execute("SELECT COUNT(*) as c FROM usuarios WHERE rol='estudiante'").fetchone()["c"]
        total_evals   = conn.execute("SELECT COUNT(*) as c FROM evaluaciones WHERE id_docente=?", (user["id"],)).fetchone()["c"]
        total_respuestas = conn.execute("SELECT COUNT(*) as c FROM resultados").fetchone()["c"]
        promedio_grupo = conn.execute("SELECT AVG(puntaje) as p FROM evaluaciones_completadas").fetchone()["p"] or 0

        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi(total_alumnos, "Estudiantes activos")
        with c2: kpi(total_evals, "Evaluaciones creadas", COLOR_SECUNDARIO)
        with c3: kpi(total_respuestas, "Respuestas registradas", COLOR_ADVERTENCIA)
        with c4: kpi(f"{promedio_grupo:.0f}%", "Promedio del grupo", COLOR_EXITO)

        st.markdown("### 📈 Desempeño general por estudiante")

        df_alumnos = pd.read_sql("""
            SELECT u.id, u.nombre,
                   COUNT(DISTINCT ec.id_evaluacion) as evaluaciones,
                   COALESCE(AVG(ec.puntaje), 0) as promedio
            FROM usuarios u
            LEFT JOIN evaluaciones_completadas ec ON ec.id_estudiante = u.id
            WHERE u.rol='estudiante'
            GROUP BY u.id, u.nombre
            ORDER BY promedio DESC
        """, conn)

        if df_alumnos.empty or df_alumnos["evaluaciones"].sum() == 0:
            st.info("Los estudiantes aún no han completado evaluaciones.")
        else:
            df_alumnos["estado"] = df_alumnos["promedio"].apply(
                lambda x: "🟢 Excelente" if x >= 80 else ("🟡 Regular" if x >= 60 else "🔴 En riesgo")
            )
            df_alumnos["promedio_pct"] = df_alumnos["promedio"].round(0).astype(int).astype(str) + "%"

            st.dataframe(
                df_alumnos[["nombre", "evaluaciones", "promedio_pct", "estado"]],
                column_config={
                    "nombre":       "Estudiante",
                    "evaluaciones": "Evaluaciones realizadas",
                    "promedio_pct": "Promedio",
                    "estado":       "Estado",
                },
                hide_index=True,
                use_container_width=True
            )

            # Distribución de calificaciones
            st.markdown("### 📊 Distribución de calificaciones del grupo")
            df_dist = df_alumnos[df_alumnos["evaluaciones"] > 0]
            if not df_dist.empty:
                fig = px.histogram(df_dist, x="promedio", nbins=10,
                                   labels={"promedio":"Promedio (%)"},
                                   color_discrete_sequence=[COLOR_PRIMARIO])
                fig.update_layout(plot_bgcolor="white", yaxis_title="Estudiantes",
                                  xaxis=dict(gridcolor="#EEE"), yaxis=dict(gridcolor="#EEE"))
                st.plotly_chart(fig, use_container_width=True)

    # -------- MIS EVALUACIONES --------
    elif seccion == "📝 Mis evaluaciones":
        st.markdown("### Mis evaluaciones creadas")

        evals = conn.execute("""
            SELECT e.*,
                   (SELECT COUNT(*) FROM evaluaciones_completadas WHERE id_evaluacion=e.id) as completadas,
                   (SELECT AVG(puntaje) FROM evaluaciones_completadas WHERE id_evaluacion=e.id) as promedio
            FROM evaluaciones e
            WHERE e.id_docente=?
            ORDER BY e.fecha_creacion DESC
        """, (user["id"],)).fetchall()

        if not evals:
            st.info("Aún no has creado evaluaciones. Ve a 'Crear evaluación' para comenzar.")
        else:
            for e in evals:
                ids = json.loads(e["preguntas_ids"])
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.markdown(f"#### {e['titulo']}")
                        st.caption(f"{e['materia']}  ·  {len(ids)} preguntas  ·  {e['fecha_creacion'][:10]}")
                        st.write(e["descripcion"] or "")
                    with c2:
                        kpi(e["completadas"], "Completadas", COLOR_PRIMARIO)
                    with c3:
                        prom = e["promedio"] or 0
                        kpi(f"{prom:.0f}%", "Promedio", COLOR_EXITO)

    # -------- CREAR EVALUACIÓN --------
    elif seccion == "➕ Crear evaluación":
        st.markdown("### Crear nueva evaluación")

        with st.form("nueva_eval", clear_on_submit=True):
            titulo = st.text_input("Título de la evaluación *", placeholder="Ej: Diagnóstico de Álgebra")
            materias = [r["materia"] for r in conn.execute(
                "SELECT DISTINCT materia FROM preguntas ORDER BY materia"
            ).fetchall()]
            materia = st.selectbox("Materia *", materias)
            descripcion = st.text_area("Descripción", placeholder="Breve descripción del propósito de la evaluación")

            # Mostrar preguntas disponibles
            preguntas_disp = conn.execute(
                "SELECT * FROM preguntas WHERE materia=? ORDER BY tema, dificultad",
                (materia,)
            ).fetchall()

            st.markdown(f"**{len(preguntas_disp)} preguntas disponibles para esta materia.**")
            st.caption("Selecciona las preguntas que formarán parte de la evaluación:")

            seleccionadas = []
            for p in preguntas_disp:
                if st.checkbox(
                    f"**{p['tema']}** ({p['dificultad']}) — {p['enunciado'][:80]}...",
                    key=f"ck_{p['id']}"
                ):
                    seleccionadas.append(p["id"])

            submit = st.form_submit_button("✅ Crear evaluación", type="primary", use_container_width=True)

            if submit:
                if not titulo:
                    st.error("Debes ingresar un título.")
                elif len(seleccionadas) < 3:
                    st.error("Selecciona al menos 3 preguntas.")
                else:
                    conn.execute("""
                        INSERT INTO evaluaciones (id_docente, titulo, materia, descripcion, preguntas_ids)
                        VALUES (?,?,?,?,?)
                    """, (user["id"], titulo, materia, descripcion, json.dumps(seleccionadas)))
                    conn.commit()
                    st.success(f"✅ Evaluación '{titulo}' creada con {len(seleccionadas)} preguntas.")

    # -------- ANÁLISIS POR TEMA --------
    elif seccion == "🎯 Análisis por tema":
        st.markdown("### Identificación de vacíos de aprendizaje del grupo")
        st.caption("Detecta qué temas presentan mayores dificultades a nivel grupal.")

        df = pd.read_sql("""
            SELECT p.materia, p.tema,
                   COUNT(*) as total_respuestas,
                   SUM(r.es_correcta) as aciertos,
                   COUNT(DISTINCT r.id_estudiante) as alumnos
            FROM resultados r
            JOIN preguntas p ON p.id = r.id_pregunta
            GROUP BY p.materia, p.tema
        """, conn)

        if df.empty:
            st.info("Aún no hay datos suficientes para análisis. Espera a que los estudiantes completen evaluaciones.")
        else:
            df["dominio_grupal"] = (df["aciertos"] / df["total_respuestas"] * 100).round(0)
            df["estado"] = df["dominio_grupal"].apply(
                lambda x: "✅ Dominado" if x >= 75 else ("⚠️ En proceso" if x >= 50 else "🚨 Vacío crítico")
            )

            # Heatmap visual
            df_sorted = df.sort_values("dominio_grupal")
            fig = go.Figure(go.Bar(
                x=df_sorted["dominio_grupal"],
                y=df_sorted["tema"] + " (" + df_sorted["materia"] + ")",
                orientation="h",
                marker=dict(
                    color=df_sorted["dominio_grupal"],
                    colorscale=[[0, "#C62828"], [0.5, "#F57C00"], [1, "#2E7D32"]],
                    cmin=0, cmax=100,
                    showscale=True,
                    colorbar=dict(title="% Dominio")
                ),
                text=df_sorted["dominio_grupal"].astype(str) + "%",
                textposition="outside"
            ))
            fig.update_layout(
                title="Dominio grupal por tema",
                xaxis=dict(range=[0, 115], title="% de respuestas correctas", gridcolor="#EEE"),
                yaxis=dict(title=""),
                plot_bgcolor="white",
                height=max(300, 40 * len(df))
            )
            st.plotly_chart(fig, use_container_width=True)

            # Alertas
            criticos = df[df["dominio_grupal"] < 50]
            if not criticos.empty:
                st.markdown("### 🚨 Temas que requieren intervención inmediata")
                for _, row in criticos.iterrows():
                    st.markdown(f"""
                        <div class="tarjeta tarjeta-rojo">
                            <strong>{row['tema']}</strong> ({row['materia']})<br>
                            Solo el <strong>{row['dominio_grupal']:.0f}%</strong> de las respuestas fueron correctas
                            ({row['alumnos']} estudiantes evaluados).<br>
                            <em>Sugerencia: dedicar una sesión de refuerzo grupal antes de avanzar.</em>
                        </div>
                    """, unsafe_allow_html=True)

    conn.close()


# =============================================================================
# DASHBOARD DEL ADMIN
# =============================================================================
def vista_admin():
    user = st.session_state.user
    header("Panel de administración",
           "Gestión de usuarios, preguntas y configuración general del sistema.")

    conn = get_conn()

    seccion = st.sidebar.radio(
        "⚙️ Menú",
        ["📊 Resumen del sistema", "👥 Gestión de usuarios", "📚 Banco de preguntas"],
        label_visibility="collapsed"
    )

    if seccion == "📊 Resumen del sistema":
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            n = conn.execute("SELECT COUNT(*) as c FROM usuarios").fetchone()["c"]
            kpi(n, "Usuarios totales")
        with c2:
            n = conn.execute("SELECT COUNT(*) as c FROM preguntas").fetchone()["c"]
            kpi(n, "Preguntas en banco", COLOR_SECUNDARIO)
        with c3:
            n = conn.execute("SELECT COUNT(*) as c FROM evaluaciones").fetchone()["c"]
            kpi(n, "Evaluaciones", COLOR_ADVERTENCIA)
        with c4:
            n = conn.execute("SELECT COUNT(*) as c FROM resultados").fetchone()["c"]
            kpi(n, "Respuestas registradas", COLOR_EXITO)

        # Distribución por rol
        st.markdown("### 👥 Distribución de usuarios por rol")
        df_roles = pd.read_sql("""
            SELECT rol, COUNT(*) as cantidad FROM usuarios GROUP BY rol
        """, conn)
        fig = px.pie(df_roles, values="cantidad", names="rol",
                     color_discrete_sequence=[COLOR_PRIMARIO, COLOR_SECUNDARIO, COLOR_ADVERTENCIA])
        fig.update_traces(textinfo="label+percent", textfont_size=14)
        st.plotly_chart(fig, use_container_width=True)

        # Distribución por materia
        st.markdown("### 📚 Preguntas por materia")
        df_mat = pd.read_sql("""
            SELECT materia, COUNT(*) as cantidad FROM preguntas GROUP BY materia
        """, conn)
        fig = px.bar(df_mat, x="materia", y="cantidad",
                     color_discrete_sequence=[COLOR_PRIMARIO])
        fig.update_layout(plot_bgcolor="white", yaxis=dict(gridcolor="#EEE"))
        st.plotly_chart(fig, use_container_width=True)

    elif seccion == "👥 Gestión de usuarios":
        st.markdown("### Usuarios del sistema")

        df = pd.read_sql("""
            SELECT id, nombre, correo, rol, grupo, fecha_registro
            FROM usuarios ORDER BY rol, nombre
        """, conn)
        st.dataframe(df, hide_index=True, use_container_width=True)

        st.markdown("### ➕ Registrar nuevo usuario")
        with st.form("nuevo_usuario", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nombre = st.text_input("Nombre completo *")
                correo = st.text_input("Correo electrónico *")
            with c2:
                rol = st.selectbox("Rol *", ["estudiante", "docente", "admin"])
                grupo = st.text_input("Grupo (opcional)")
            password = st.text_input("Contraseña inicial *", type="password")

            if st.form_submit_button("Crear usuario", type="primary"):
                if not all([nombre, correo, password]):
                    st.error("Completa todos los campos obligatorios.")
                else:
                    try:
                        conn.execute("""
                            INSERT INTO usuarios (nombre, correo, password_hash, rol, grupo)
                            VALUES (?,?,?,?,?)
                        """, (nombre, correo, hash_password(password), rol, grupo or None))
                        conn.commit()
                        st.success(f"Usuario {nombre} creado correctamente.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Ese correo ya está registrado.")

    elif seccion == "📚 Banco de preguntas":
        st.markdown("### Banco de preguntas")

        df = pd.read_sql("""
            SELECT id, materia, tema, dificultad, enunciado, respuesta_correcta
            FROM preguntas ORDER BY materia, tema
        """, conn)

        # Filtros
        c1, c2 = st.columns(2)
        with c1:
            materias = ["Todas"] + sorted(df["materia"].unique().tolist())
            f_materia = st.selectbox("Filtrar por materia", materias)
        with c2:
            f_dif = st.selectbox("Filtrar por dificultad", ["Todas", "Baja", "Media", "Alta"])

        df_f = df.copy()
        if f_materia != "Todas":
            df_f = df_f[df_f["materia"] == f_materia]
        if f_dif != "Todas":
            df_f = df_f[df_f["dificultad"] == f_dif]

        st.caption(f"Mostrando {len(df_f)} de {len(df)} preguntas.")
        st.dataframe(df_f, hide_index=True, use_container_width=True)

    conn.close()


# =============================================================================
# MAIN
# =============================================================================
def main():
    cargar_estilos()
    inicializar_bd()

    if "user" not in st.session_state:
        pantalla_login()
        return

    user = st.session_state.user

    # Barra lateral con info del usuario
    with st.sidebar:
        st.markdown(f"""
            <div style="text-align:center; padding:1rem 0; border-bottom: 1px solid #DDD; margin-bottom: 1rem;">
                <div style="font-size:3rem;">{'👨‍🏫' if user['rol']=='docente' else '👨‍🎓' if user['rol']=='estudiante' else '⚙️'}</div>
                <div style="font-weight:600; color:#600070; margin-top:0.5rem;">{user['nombre']}</div>
                <div style="font-size:0.85rem; color:#666; text-transform:capitalize;">
                    {user['rol']} {'· ' + user['grupo'] if user.get('grupo') else ''}
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Enrutamiento por rol
    if user["rol"] == "estudiante":
        vista_estudiante()
    elif user["rol"] == "docente":
        vista_admin() if False else vista_docente()
    elif user["rol"] == "admin":
        vista_admin()

    # Botón de logout al final del sidebar
    with st.sidebar:
        st.markdown("---")
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            logout()
            st.rerun()
        st.caption("Dos de Tres · ESCOM-IPN · 2026")


if __name__ == "__main__":
    main()
