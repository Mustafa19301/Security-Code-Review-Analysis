import streamlit as st
import streamlit.components.v1 as components
import html
import json


def inject_theme():
    """Shared CodeReview Sentinel styling and lightweight motion."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

        :root {
            --cr-bg: #08111f;
            --cr-panel: #101d30;
            --cr-panel-2: #14243a;
            --cr-border: rgba(148, 163, 184, .16);
            --cr-blue: #60a5fa;
            --cr-cyan: #22d3ee;
            --cr-muted: #94a3b8;
        }

        html, body, [class*="css"] {
            font-family: 'DM Sans', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 8% 0%, rgba(37, 99, 235, .13), transparent 27rem),
                radial-gradient(circle at 95% 8%, rgba(8, 145, 178, .09), transparent 24rem),
                var(--cr-bg);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0d192b 0%, #091321 100%);
            border-right: 1px solid var(--cr-border);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #cbd5e1;
        }

        h1, h2, h3 {
            font-family: 'Space Grotesk', sans-serif !important;
            letter-spacing: -.035em;
        }

        h1 {
            font-weight: 700 !important;
        }

        h2, h3 {
            font-weight: 600 !important;
        }

        p, li {
            line-height: 1.65;
        }

        .cr-eyebrow {
            color: var(--cr-cyan);
            font-size: .73rem;
            font-weight: 800;
            letter-spacing: .16em;
            text-transform: uppercase;
            margin-bottom: .35rem;
        }

        .cr-hero {
            padding: 1.55rem 1.7rem;
            border: 1px solid rgba(96,165,250,.22);
            border-radius: 20px;
            background: linear-gradient(
                120deg,
                rgba(30,64,115,.42),
                rgba(15,29,48,.78)
            );
            box-shadow: 0 18px 55px rgba(0,0,0,.18);
            animation: crFadeUp .55s ease both;
        }

        .cr-hero-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: clamp(2rem, 4vw, 3.25rem);
            font-weight: 700;
            letter-spacing: -.055em;
            line-height: 1.08;
            margin: .25rem 0 .7rem;
        }

        .cr-hero-copy {
            color: #b7c6d9;
            max-width: 850px;
            font-size: 1.02rem;
        }

        .cr-card {
            border: 1px solid var(--cr-border);
            border-radius: 16px;
            padding: 1.05rem 1.15rem;
            background: linear-gradient(
                145deg,
                rgba(20,36,58,.94),
                rgba(13,26,43,.94)
            );
            box-shadow: 0 10px 30px rgba(0,0,0,.12);
            transition:
                transform .2s ease,
                border-color .2s ease,
                box-shadow .2s ease;
            animation: crFadeUp .45s ease both;
        }

        .cr-card:hover {
            transform: translateY(-3px);
            border-color: rgba(96,165,250,.45);
            box-shadow: 0 15px 35px rgba(0,0,0,.22);
        }

        .cr-card-label {
            color: var(--cr-muted);
            font-size: .78rem;
            font-weight: 600;
        }

        .cr-card-value {
            color: #eaf2ff;
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.65rem;
            font-weight: 700;
            margin-top: .25rem;
            font-variant-numeric: tabular-nums;
        }

        .cr-card-note {
            color: #91a4bd;
            font-size: .76rem;
            margin-top: .25rem;
        }

        .cr-section-note {
            color: var(--cr-muted);
            margin-top: -.45rem;
            margin-bottom: 1rem;
        }

        .cr-pill {
            display: inline-block;
            padding: .28rem .65rem;
            border-radius: 999px;
            border: 1px solid rgba(96,165,250,.3);
            background: rgba(37,99,235,.12);
            color: #bfdbfe;
            font-size: .75rem;
            font-weight: 700;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(
                145deg,
                rgba(20,36,58,.95),
                rgba(13,26,43,.95)
            );
            border: 1px solid var(--cr-border);
            padding: 1rem 1.1rem;
            border-radius: 15px;
            transition: transform .2s ease, border-color .2s ease;
            animation: crFadeUp .45s ease both;
        }

        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            border-color: rgba(96,165,250,.4);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--cr-muted);
        }

        div[data-testid="stMetricValue"] {
            color: #eaf2ff;
            font-family: 'Space Grotesk', sans-serif;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 10px;
            font-weight: 700;
            min-height: 2.65rem;
            transition: transform .18s ease, box-shadow .18s ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 22px rgba(37,99,235,.2);
        }

        div[data-baseweb="select"] > div,
        .stTextInput input,
        .stTextArea textarea {
            border-radius: 10px !important;
        }

        [data-testid="stDataFrame"],
        [data-testid="stPlotlyChart"] {
            border: 1px solid var(--cr-border);
            border-radius: 14px;
            overflow: hidden;
            animation: crChartEnter .7s ease both;
        }

        hr {
            border-color: rgba(148,163,184,.15);
        }

        @keyframes crFadeUp {
            from {
                opacity: 0;
                transform: translateY(9px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes crChartEnter {
            from {
                opacity: 0;
                transform: translateY(12px) scale(.99);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: .01ms !important;
                transition-duration: .01ms !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def sidebar_brand():
    with st.sidebar:
        st.markdown(
            """
            <div style="padding:.4rem 0 .8rem">
              <div style="font-size:1.5rem;font-weight:800;
                          font-family:'Space Grotesk',sans-serif">
                CodeReview
              </div>
              <div style="font-size:.75rem;letter-spacing:.22em;
                          color:#60a5fa;font-weight:800">
                SENTINEL
              </div>
              <div style="font-size:.78rem;color:#94a3b8;margin-top:.5rem">
                Security code review research
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()
        st.caption("RESEARCH WORKSPACE")
        st.caption(
            "Use the page navigation above to explore datasets, "
            "model results, predictions, and errors."
        )
        st.divider()
        st.caption("University Research Prototype")
        st.caption("GitHub + Gerrit")


def page_header(eyebrow, title, description):
    st.markdown(
        f"""
        <div class="cr-eyebrow">{html.escape(str(eyebrow))}</div>
        <div class="cr-hero">
          <div class="cr-hero-title">{html.escape(str(title))}</div>
          <div class="cr-hero-copy">{html.escape(str(description))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")


def metric_card(label, value, note=""):
    """Display a regular styled metric card."""
    st.markdown(
        f"""
        <div class="cr-card">
          <div class="cr-card-label">{html.escape(str(label))}</div>
          <div class="cr-card-value">{html.escape(str(value))}</div>
          <div class="cr-card-note">{html.escape(str(note))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def animated_metric_card(
    label,
    value,
    note="",
    prefix="",
    suffix="",
    decimals=0,
    duration=1200,
):
    """Display a metric card with a JavaScript count-up animation."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        metric_card(label, value, note)
        return

    decimals = max(0, min(int(decimals), 6))
    duration = max(200, min(int(duration), 5000))

    counter_index = st.session_state.get("_cr_counter_index", 0)
    st.session_state["_cr_counter_index"] = counter_index + 1

    card_id = f"cr-counter-{counter_index}"

    safe_label = html.escape(str(label))
    safe_note = html.escape(str(note))
    safe_prefix = str(prefix)
    safe_suffix = str(suffix)

    components.html(
        f"""
        <div class="cr-counter-card" id="{card_id}">
            <div class="cr-counter-label">{safe_label}</div>
            <div class="cr-counter-value">
                <span class="cr-counter-number">0</span>
            </div>
            <div class="cr-counter-note">{safe_note}</div>
        </div>

        <style>
            body {{
                margin: 0;
                background: transparent;
                font-family: Arial, sans-serif;
            }}

            .cr-counter-card {{
                box-sizing: border-box;
                padding: 1.05rem 1.15rem;
                border: 1px solid rgba(148, 163, 184, .16);
                border-radius: 16px;
                background: linear-gradient(
                    145deg,
                    rgba(20,36,58,.98),
                    rgba(13,26,43,.98)
                );
                box-shadow: 0 10px 30px rgba(0,0,0,.12);
                animation: crCounterEnter .55s ease both;
                transition: transform .2s ease, border-color .2s ease;
            }}

            .cr-counter-card:hover {{
                transform: translateY(-3px);
                border-color: rgba(96,165,250,.45);
            }}

            .cr-counter-label {{
                color: #94a3b8;
                font-size: .78rem;
                font-weight: 600;
            }}

            .cr-counter-value {{
                color: #eaf2ff;
                font-size: 1.65rem;
                font-weight: 700;
                margin-top: .25rem;
                font-variant-numeric: tabular-nums;
            }}

            .cr-counter-note {{
                color: #91a4bd;
                font-size: .76rem;
                margin-top: .25rem;
            }}

            @keyframes crCounterEnter {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}

            @media (prefers-reduced-motion: reduce) {{
                .cr-counter-card {{
                    animation: none;
                    transition: none;
                }}
            }}
        </style>

        <script>
        (function() {{
            const root = document.getElementById("{card_id}");
            if (!root) return;

            const numberElement = root.querySelector(".cr-counter-number");
            const target = {json.dumps(numeric_value)};
            const decimals = {decimals};
            const duration = {duration};
            const prefix = {json.dumps(safe_prefix)};
            const suffix = {json.dumps(safe_suffix)};

            const reduceMotion = window.matchMedia(
                "(prefers-reduced-motion: reduce)"
            ).matches;

            function formatNumber(number) {{
                return prefix + number.toLocaleString(
                    "en-US",
                    {{
                        minimumFractionDigits: decimals,
                        maximumFractionDigits: decimals
                    }}
                ) + suffix;
            }}

            if (reduceMotion) {{
                numberElement.textContent = formatNumber(target);
                return;
            }}

            const startTime = performance.now();

            function animate(currentTime) {{
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3);
                const currentValue = target * eased;

                numberElement.textContent = formatNumber(currentValue);

                if (progress < 1) {{
                    requestAnimationFrame(animate);
                }} else {{
                    numberElement.textContent = formatNumber(target);
                }}
            }}

            requestAnimationFrame(animate);
        }})();
        </script>
        """,
        height=112,
        scrolling=False,
    )


def section_heading(title, note=None):
    st.markdown(f"## {title}")

    if note:
        st.markdown(
            f'<div class="cr-section-note">{html.escape(str(note))}</div>',
            unsafe_allow_html=True,
        )