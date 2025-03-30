# Final Code: Uniswap V4 Hooks Aesthetics with Original Game Logic (Light Theme)

import streamlit as st
from collections import deque, Counter
import time
import random
import datetime
import pandas as pd
import math

# ============================================================
# Helper Classes (Original Game Logic & V4 Themed UI)
# ============================================================

class OriginalGameLogic:
    """Handles core game logic based on the original 5-type rules."""

    # --- Use Original Game Names Internally for Logic Mapping ---
    PAYOUTS = {
        "Royal Single": 10.0,
        "Golden Jodi": 90.0,
        "Triple Crown": 150.0,
        "Double Fortune": 300.0,
        "Royal Flush": 500.0,
    }

    # --- Map Original Names to V4 Theme Names for UI Display ---
    THEME_NAME_MAP = {
        "Royal Single": "Signal Prediction",           # Renamed for V4 theme
        "Golden Jodi": "Combined Signal",             # Renamed for V4 theme
        "Triple Crown": "Unique Oracle Pattern",      # Renamed for V4 theme
        "Double Fortune": "Repeating Oracle Pattern", # Renamed for V4 theme
        "Royal Flush": "Consensus Oracle Pattern",    # Renamed for V4 theme
    }
    # Reverse map for looking up internal name from UI selection
    INTERNAL_NAME_MAP = {v: k for k, v in THEME_NAME_MAP.items()}


    # --- Market Timing (UTC) ---
    MARKET_OPEN_HOUR_UTC = 9
    MARKET_CLOSE_HOUR_UTC = 21
    DRAW_INTERVAL_MINUTES = 5 # Conceptual interval

    # --- Streak Bonuses & Jackpot ---
    STREAK_BONUSES = {3: 0.10, 5: 0.20, 10: 0.50} # Bonus multipliers
    JACKPOT_CONTRIBUTION_RATE = 0.01 # 1% of each bet contributes
    JACKPOT_WIN_CHANCE_ON_FLUSH = 0.05 # 5% chance to win jackpot *if* Royal Flush/Consensus Pattern hits

    @staticmethod
    def get_payout_multiplier(internal_game_type: str) -> float:
        """Returns the fixed payout multiplier using the internal name."""
        # Uses the original game names (Royal Single etc.) as keys
        return OriginalGameLogic.PAYOUTS.get(internal_game_type, 0.0)

    @staticmethod
    def is_market_open() -> tuple[bool, str, int]:
        """Checks market status based on UTC time."""
        now_utc = datetime.datetime.utcnow()
        open_time = datetime.time(OriginalGameLogic.MARKET_OPEN_HOUR_UTC, 0)
        close_time = datetime.time(OriginalGameLogic.MARKET_CLOSE_HOUR_UTC, 0)
        is_open_today = open_time <= now_utc.time() < close_time
        if is_open_today:
            message_prefix = "Market Open | Closes in:"
            close_dt = datetime.datetime.combine(now_utc.date(), close_time, tzinfo=datetime.timezone.utc)
            time_diff = close_dt - now_utc.replace(tzinfo=datetime.timezone.utc)
        else:
            message_prefix = "Market Monitoring | Opens in:"
            open_dt_today = datetime.datetime.combine(now_utc.date(), open_time, tzinfo=datetime.timezone.utc)
            next_open_dt = open_dt_today if now_utc.time() < open_time else open_dt_today + datetime.timedelta(days=1)
            time_diff = next_open_dt - now_utc.replace(tzinfo=datetime.timezone.utc)
        time_until_change = max(0, int(time_diff.total_seconds()))
        return is_open_today, message_prefix, time_until_change

    @staticmethod
    def get_time_to_next_draw() -> int:
        """Calculates seconds until the next conceptual draw interval."""
        now = datetime.datetime.utcnow(); interval = OriginalGameLogic.DRAW_INTERVAL_MINUTES
        minutes_past_hour = now.minute
        next_draw_minute = (math.floor(minutes_past_hour / interval) + 1) * interval
        next_draw_dt = (now + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0) if next_draw_minute >= 60 else now.replace(minute=next_draw_minute, second=0, microsecond=0)
        return max(0, int((next_draw_dt - now).total_seconds()))

    @staticmethod
    def generate_draw() -> tuple[list[int], int, list[int], int]:
        """Generates the two draws and their sums (using internal terminology)."""
        draw1_digits = [random.randint(0, 9) for _ in range(3)]
        sum1 = sum(draw1_digits) % 10 # Represents "First Sum" or "Signal 1"
        draw2_digits = [random.randint(0, 9) for _ in range(3)]
        sum2 = sum(draw2_digits) % 10 # Represents "Second Sum" or "Signal 2"
        return draw1_digits, sum1, draw2_digits, sum2

    @staticmethod
    def check_win(internal_game_type: str, user_choice, draw1_digits: list[int], sum1: int, draw2_digits: list[int], sum2: int) -> bool:
        """Checks win condition based on the 5 original game types using internal names."""
        try:
            # Logic uses internal names like "Royal Single"
            if internal_game_type == "Royal Single":
                user_num = int(user_choice); return user_num == sum1 or user_num == sum2
            elif internal_game_type == "Golden Jodi":
                user_jodi_str = str(user_choice).zfill(2); actual_jodi_str = str(sum1) + str(sum2); return user_jodi_str == actual_jodi_str
            elif internal_game_type in ["Triple Crown", "Double Fortune", "Royal Flush"]:
                user_digits_str = str(user_choice).zfill(3); user_digits_list_sorted = sorted([int(d) for d in user_digits_str])
                match1 = (user_digits_list_sorted == sorted(draw1_digits)); match2 = (user_digits_list_sorted == sorted(draw2_digits))
                user_counts = Counter(user_digits_list_sorted); draw1_counts = Counter(draw1_digits); draw2_counts = Counter(draw2_digits)
                is_user_valid, is_draw1_pattern_match, is_draw2_pattern_match = False, False, False
                if internal_game_type == "Triple Crown":
                    is_user_valid = len(user_counts) == 3; is_draw1_pattern_match = len(draw1_counts) == 3; is_draw2_pattern_match = len(draw2_counts) == 3
                elif internal_game_type == "Double Fortune":
                    is_user_valid = len(user_counts) == 2 and 2 in user_counts.values(); is_draw1_pattern_match = len(draw1_counts) == 2 and 2 in draw1_counts.values(); is_draw2_pattern_match = len(draw2_counts) == 2 and 2 in draw2_counts.values()
                elif internal_game_type == "Royal Flush":
                    is_user_valid = len(user_counts) == 1; is_draw1_pattern_match = len(draw1_counts) == 1; is_draw2_pattern_match = len(draw2_counts) == 1
                return is_user_valid and ((match1 and is_draw1_pattern_match) or (match2 and is_draw2_pattern_match))
            else: return False
        except Exception as e: st.error(f"Check Win Error: {e}", icon="⚠️"); return False

    @staticmethod
    def get_streak_bonus_multiplier(streak_count: int) -> float:
        """Gets the bonus multiplier based on the current win streak count."""
        bonus = 0.0; bonus_levels = OriginalGameLogic.STREAK_BONUSES
        for streak, rate in sorted(bonus_levels.items(), reverse=True):
            if streak_count >= streak: bonus = rate; break
        return bonus

    @staticmethod
    def calculate_jackpot(current_jackpot: float, bet_amount: float) -> float:
        """Calculates the new jackpot amount after a contribution."""
        return current_jackpot + (bet_amount * OriginalGameLogic.JACKPOT_CONTRIBUTION_RATE)

    @staticmethod
    def format_currency(amount: float, currency_symbol: str = "Tokens") -> str:
        """Formats a number as currency/tokens."""
        return f"{amount:,.2f} {currency_symbol}"

    @staticmethod
    def format_seconds(seconds: int) -> str:
        """Formats seconds into a more readable H:M:S or M:S string."""
        if seconds < 0: seconds = 0
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours > 0: return f"{hours:01d}h {minutes:02d}m {secs:02d}s"
        else: return f"{minutes:02d}m {secs:02d}s"


class V4ThemedUI: # Re-using the V4 UI Class Name
    """Provides UI rendering functions with V4 Hooks Aesthetics."""

    @staticmethod
    def render_stats_cards(balance: float, total_bets: int, win_rate: float, jackpot: float):
        """Renders the 4 main statistics cards with V4 theme."""
        cols = st.columns(4)
        cards_data = [
            ("💰 Balance", OriginalGameLogic.format_currency(balance)),
            ("📊 Predictions", f"{total_bets}"), # Changed Bets to Predictions
            ("🎯 Accuracy", f"{win_rate:.2f}%"), # Changed Win Rate to Accuracy
            ("🏆 V4 Jackpot", OriginalGameLogic.format_currency(jackpot)) # Changed label
        ]
        jackpot_class = ""
        for i, col in enumerate(cols):
            title, value = cards_data[i]
            if "Jackpot" in title: jackpot_class = "jackpot"
            col.markdown(f"""<div class="stat-card {jackpot_class}"><h4>{title}</h4><p>{value}</p></div>""", unsafe_allow_html=True)
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    @staticmethod
    def render_market_status(is_open: bool, message: str, time_until_change_sec: int, time_to_next_draw_sec: int):
         """Renders the market status bar and next draw timer with V4 theme."""
         status_color = "#28a745" if is_open else "#ffc107"; status_icon = "✅" if is_open else "⏳"
         time_str = OriginalGameLogic.format_seconds(time_until_change_sec)
         next_draw_time_str = OriginalGameLogic.format_seconds(time_to_next_draw_sec)
         col1, col2 = st.columns([2,1])
         with col1: st.markdown(f"""<div class="timer-display" style="background-color: {status_color};">{status_icon} {message} <strong>{time_str}</strong></div>""", unsafe_allow_html=True)
         with col2: st.markdown(f"""<div class="timer-display next-draw">⚡ Next Signal In: <strong>{next_draw_time_str}</strong></div>""", unsafe_allow_html=True) # V4 themed text/icon

    @staticmethod
    def render_signal_trends(last_jodis: list): # Changed name back to signal_trends
        """Displays recent 'Combined Signal' (Jodi) results with V4 theme."""
        if not last_jodis: return
        st.markdown("---")
        st.markdown("<h4>📈 Recent Combined Signals</h4>", unsafe_allow_html=True) # V4 themed title
        trend_html = "<div class='trend-container'>"
        for jodi in reversed(last_jodis): trend_html += f"<span class='trend-item signal-jodi'>{jodi}</span>" # V4 themed class name
        trend_html += "</div>"
        st.markdown(trend_html, unsafe_allow_html=True)

    @staticmethod
    def render_game_history(history: list):
        """Renders the game history using V4 themed labels."""
        if not history: st.info("No prediction history yet."); return
        df = pd.DataFrame(history)
        # Map internal game type names to themed names for display
        df['themed_game_type'] = df['game_type'].map(OriginalGameLogic.THEME_NAME_MAP).fillna(df['game_type'])

        display_cols = ['timestamp','themed_game_type','user_choice','draw1_result','draw2_result',
                         'bet_amount','payout','won']
        cols_to_use = [col for col in display_cols if col in df.columns]
        df_display = df[cols_to_use].copy()
        # Rename columns using V4 themed labels
        rename_map = {
            'timestamp': 'Time', 'themed_game_type': 'Prediction Type', 'user_choice': 'Prediction',
            'draw1_result': 'Feed 1 (Digits*Signal)', # V4 themed label
            'draw2_result': 'Feed 2 (Digits*Signal)', # V4 themed label
            'bet_amount': 'Bet', 'payout': 'Payout', 'won': 'Correct?' }
        df_display.rename(columns={k:v for k,v in rename_map.items() if k in df_display.columns}, inplace=True)
        def fmt_curr(val): return f"{val:,.2f}"
        def style_pay(payout): return f'color: {"#007bff" if payout > 0 else "#6c757d"};' # Using blue/grey styling
        st.markdown("<h4>📜 Prediction History Log</h4>", unsafe_allow_html=True) # V4 themed title
        st.dataframe(df_display.style.format({'Bet': fmt_curr,'Payout': fmt_curr,'Correct?': lambda x: "✅ Yes" if x else "❌ No"}, na_rep="-")
                           .applymap(style_pay, subset=['Payout'] if 'Payout' in df_display else None))

# ============================================================
# Main Streamlit Application Setup
# ============================================================

# --- Page Configuration (V4 Theme) ---
st.set_page_config(
    page_title="V4 Oracle Predict | Hook Sim",
    page_icon="🔗", # Chain Link Icon
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://docs.uniswap.org/concepts/protocol/uniswap-v4/hooks', # Valid URL
        'Report a bug': "https://github.com/yourusername/v4-oracle-predict-sim/issues", # Replace with your repo URL
        'About': "# V4 Oracle Predict Simulation\nPredicting Oracle Signals using V4 Hook concepts. Core mechanics for entertainment."
    }
)

# --- Session State Initialization (Using 'v4_' prefix) ---
if 'v4_balance' not in st.session_state: st.session_state.v4_balance = 10000.0
if 'v4_history' not in st.session_state: st.session_state.v4_history = []
if 'v4_last_signals' not in st.session_state: st.session_state.v4_last_signals = deque(maxlen=10) # Renamed from og_last_jodis
if 'v4_jackpot' not in st.session_state: st.session_state.v4_jackpot = 5000.0
if 'v4_streak' not in st.session_state: st.session_state.v4_streak = 0
if 'v4_quick_pick_holder' not in st.session_state: st.session_state.v4_quick_pick_holder = None

# --- Load Embedded CSS (V4 Light Theme) ---
# (CSS here is the Pink/Purple light theme from previous V4 examples)
embedded_css = """<style>
    body { background-color: #f0f2f5; color: #333; font-family: sans-serif;} .stApp { background-color: #f0f2f5; }
    .stButton>button { background-color: #FF007A; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; transition: background-color 0.3s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
    .stButton>button:hover { background-color: #d40067; } .stButton>button:active { background-color: #a50050; }
    .stExpander { border: 1px solid #dee2e6; border-radius: 8px; background-color: #ffffff; margin-bottom: 15px;} .stExpander header {color: #6a0dad;} /* Purple header */
    .stSelectbox > div > div { background-color: #ffffff; border: 1px solid #ced4da; border-radius: 6px; color: #495057;}
    .stNumberInput input, .stTextInput input { background-color: #ffffff; border: 1px solid #ced4da; border-radius: 6px; color: #495057;}
    h1, h2, h3, h4, h5, h6 { color: #343a40; } label, .stMarkdown p { color: #495057; }
    code { background-color: #e9ecef; color: #FF007A; padding: 2px 5px; border-radius: 3px;} hr { border-top: 1px solid #dee2e6; }
    .header-container { background: linear-gradient(135deg, #f8f0ff, #ffffff); border: 1px solid #e0cffc; padding: 20px; border-radius: 10px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; color: #333; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);} /* Light Purple Gradient */
    .logo-section { display: flex; align-items: center; } .logo-box svg { width: 50px; height: 50px; fill: #FF007A; margin-right: 15px; } /* Pink logo */
    .game-title { font-size: 2.5em; margin: 0; color: #6a0dad; /* Purple */ text-shadow: none; } .subtitle { font-size: 1.1em; text-align: right; color: #6c757d; }
    .timer-display { text-align: center; font-weight: bold; padding: 8px 15px; border-radius: 8px; color: white; margin-bottom: 10px; box-shadow: inset 0 1px 3px rgba(0,0,0,0.1); font-size: 0.95em;}
    .timer-display.next-draw { background-color: #a06cd5; } /* Lighter Purple timer */
    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
    .stat-card { background-color: #ffffff; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #dee2e6; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);}
    .stat-card h4 { margin-top: 0; margin-bottom: 8px; color: #6c757d; font-size: 1em; } .stat-card p { margin-bottom: 0; font-size: 1.4em; font-weight: bold; color: #6a0dad; } /* Purple numbers */
    .stat-card.jackpot p { color: #FF007A; font-weight: bolder; } /* Pink Jackpot */
    .trend-container { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 5px; margin-bottom: 15px; justify-content: center; }
    .trend-item.signal-jodi { color: #FF007A; background-color: #fdf0f7; border: 1px solid #ffc7e3; padding: 5px 12px; border-radius: 15px; font-weight: bold; font-size: 1.1em; min-width: 40px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05);} /* Pink trends */
    .result-animation { border: 1px solid #ffc107; padding: 15px; margin-top: 15px; margin-bottom: 15px; border-radius: 8px; background-color: #fffbeb;}
    .draw-display { font-size: 1.2em; font-weight: bold; margin-bottom: 5px; text-align: center; color: #495057;}
    .draw-display .feed-label { font-size: 0.85em; color: #6c757d; text-transform: uppercase; margin-right: 5px;}
    .draw-display .digits { color: #6c757d; font-style: italic; font-size: 0.9em;} .draw-display .signal { color: #6a0dad; } /* Purple signal */
    .draw-display .jodi-result { display: inline-block; font-size:1.4em; margin-top: 10px; color: #FF007A; background-color: #fdf0f7; border: 1px solid #ffc7e3; padding: 5px 12px; border-radius: 15px; font-weight: bold;} /* Pink combined signal */
    .win-animation { border: 1px solid #28a745; padding: 10px; margin-top: 10px; border-radius: 8px; background-color: #eafaf1;}
    .bet-option-card { background-color: #ffffff; padding: 20px; border-radius: 8px; margin-top: 10px; border: 1px solid #dee2e6; box-shadow: 0 1px 3px rgba(0,0,0,0.08);}
    .bet-option-card .odds-display { text-align: right; font-size: 0.9em; color: #6a0dad; font-weight: bold;} /* Purple odds */
    .quick-pick-container { margin-top: 10px; text-align: right; }
    .quick-pick-container button { background-color: #f8f0ff; /* Light purple */ color: #6a0dad; padding: 5px 10px; font-size: 0.9em; border: 1px solid #e0cffc; margin-left: 5px; border-radius: 5px;}
    .quick-pick-container button:hover { background-color: #e0cffc;}
</style>"""
st.markdown(embedded_css, unsafe_allow_html=True)

# ============================================================
# Streamlit UI Layout and Logic
# ============================================================

# --- Header ---
# (Using Uniswap-like SVG and V4 Themed Title)
st.markdown("""<div class="header-container">
    <div class="logo-section"><div class="logo-box">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <path d="M50 0 A50 50 0 0 1 93.3 25 L75 25 A25 25 0 0 0 50 25 Z" /> <path d="M50 0 A50 50 0 0 0 6.7 25 L25 25 A25 25 0 0 1 50 25 Z" />
                <path d="M50 100 A50 50 0 0 1 6.7 75 L25 75 A25 25 0 0 0 50 75 Z" /> <path d="M50 100 A50 50 0 0 0 93.3 75 L75 75 A25 25 0 0 1 50 75 Z" />
                <circle cx="50" cy="50" r="15"/> </svg></div>
        <div class="title-box"><h1 class="game-title">V4 ORACLE PREDICT</h1></div></div>
    <div class="subtitle">Simulated Hook Signal Prediction</div></div>""", unsafe_allow_html=True)

# --- Market Status Display ---
try:
    is_open, status_msg, time_change_sec = OriginalGameLogic.is_market_open()
    next_draw_sec = OriginalGameLogic.get_time_to_next_draw()
    V4ThemedUI.render_market_status(is_open, status_msg, time_change_sec, next_draw_sec) # Using V4 UI
except Exception as e: st.error(f"Status Error: {e}", icon="🚨")

# --- Stats Display ---
try:
    total_bets_made = len(st.session_state.v4_history)
    wins_count = sum(1 for x in st.session_state.v4_history if x['won'])
    win_rate_stat = (wins_count / total_bets_made * 100) if total_bets_made > 0 else 0.0
    V4ThemedUI.render_stats_cards( # Using V4 UI
        st.session_state.v4_balance, total_bets_made, win_rate_stat, st.session_state.v4_jackpot
    )
except Exception as e: st.error(f"Stats Error: {e}", icon="📊")

# --- Signal Trends Display ---
try:
    V4ThemedUI.render_signal_trends(list(st.session_state.v4_last_signals)) # Using V4 UI & state key
except Exception as e: st.error(f"Trend Display Error: {e}", icon="📈")

# --- Game Interface Section ---
st.markdown("---"); st.subheader("🔮 Predict the Oracle Signals") # V4 Themed title

# --- How to Play Expander (V4 Themed Text, Original Logic Explanation) ---
with st.expander("📖 How to Play V4 Oracle Predict", expanded=False):
     # Mapping original game logic to V4 theme explanation
     st.markdown(f"""
    Welcome! Predict outcomes based on simulated Oracle signals processed by a V4 Hook concept.

    **The Process (Simulated):**
    1.  **Feed 1:** Hook reads 3 Oracle values (e.g., `[2,5,8]`). Calculates **Pressure Signal** (sum%10 ➜ `5`).
    2.  **Feed 2:** Hook reads 3 more values (e.g., `[3,6,9]`). Calculates **Momentum Signal** (sum%10 ➜ `8`).
    3.  The **Combined Signal** is `Pressure` + `Momentum` (e.g., `58`).

    **Prediction Types (Core Game Logic):**
    *   **Signal Prediction ({OriginalGameLogic.PAYOUTS['Royal Single']}x):** Predict the `Pressure` **OR** `Momentum` signal digit (0-9).
    *   **Combined Signal ({OriginalGameLogic.PAYOUTS['Golden Jodi']}x):** Predict the final two-digit combined signal (00-99).
    *   **Unique Oracle Pattern ({OriginalGameLogic.PAYOUTS['Triple Crown']}x):** Predict a `XYZ` pattern (3 unique digits) in either Feed 1 **OR** Feed 2 raw data.
    *   **Repeating Oracle Pattern ({OriginalGameLogic.PAYOUTS['Double Fortune']}x):** Predict a `XXY`/`XYY` pattern (2 same digits) in either Feed 1 **OR** Feed 2.
    *   **Consensus Oracle Pattern ({OriginalGameLogic.PAYOUTS['Royal Flush']}x + Jackpot):** Predict a `XXX` pattern (3 same digits) in either Feed 1 **OR** Feed 2. Win gives Jackpot chance!

    **Features:** Win Streaks (3/5/10 wins = +10%/+20%/+50% bonus) & Progressive V4 Jackpot.
    **Disclaimer:** Simulation for entertainment. Not real financial advice. Play Responsibly.
    """)


# --- Bet Selection Card ---
st.markdown('<div class="bet-option-card">', unsafe_allow_html=True)

# Use THEMED names for display, map back to internal names for logic
themed_game_types = list(OriginalGameLogic.THEME_NAME_MAP.values())
selected_theme_name = st.selectbox(
    "Select Prediction Type",
    themed_game_types,
    key="v4_game_type_selector" # Use v4 state prefix
)
# Get the internal name for logic
internal_game_type = OriginalGameLogic.INTERNAL_NAME_MAP[selected_theme_name]

# Display Payout
payout = OriginalGameLogic.get_payout_multiplier(internal_game_type)
st.markdown(f"<div class='odds-display'>Payout: {payout}x</div>", unsafe_allow_html=True)

# Input for User's Bet Choice
user_choice_input = None
input_key = f"v4_input_{selected_theme_name.replace(' ', '_')}" # Unique key

# --- Conditional Input Widget Logic (using internal_game_type) ---
if internal_game_type == "Royal Single": # Logic check uses internal name
    user_choice_input = st.number_input("Predict Signal Digit (0-9)", min_value=0, max_value=9, step=1, key=input_key)
elif internal_game_type == "Golden Jodi": # Logic check uses internal name
    user_choice_input_str = st.text_input("Predict Combined Signal (00-99)", max_chars=2, key=input_key, placeholder="e.g., 58")
    if user_choice_input_str and user_choice_input_str.isdigit() and len(user_choice_input_str) == 2: user_choice_input = user_choice_input_str
    elif user_choice_input_str: st.warning("Enter 2 digits.", icon="⚠️"); user_choice_input = None
    else: user_choice_input = None
elif internal_game_type in ["Triple Crown", "Double Fortune", "Royal Flush"]: # Logic check uses internal name
    # Use the THEMED name for the prompt
    prompt = f"Predict Oracle Pattern ({selected_theme_name} - 000-999)"
    placeholder="e.g., 123 (Unique), 112 (Repeating), 777 (Consensus)"
    user_choice_input_str = st.text_input(prompt, max_chars=3, key=input_key, placeholder=placeholder)
    if user_choice_input_str and user_choice_input_str.isdigit() and len(user_choice_input_str) == 3:
         user_choice_input = user_choice_input_str
    elif user_choice_input_str: st.warning("Enter 3 digits.", icon="⚠️"); user_choice_input = None
    else: user_choice_input = None

# --- Bet Amount Input & Quick Picks ---
st.markdown("<br>", unsafe_allow_html=True)
col_bet, col_quick = st.columns([2, 1])
# Quick Pick Logic (using v4_ keys)
current_bet_value = 100.0
if st.session_state.v4_quick_pick_holder is not None:
    current_bet_value = max(10.0, min(5000.0, st.session_state.v4_quick_pick_holder))
    st.session_state.v4_quick_pick_holder = None
with col_bet:
    bet_amount = st.number_input(
        "Bet Amount (Tokens)", min_value=10.0, max_value=5000.0,
        value=float(current_bet_value), step=10.0, key="v4_bet_amount_widget", # Use v4 state prefix
        help=f"Min: 10, Max: 5000 | Bal: {st.session_state.v4_balance:,.2f}" # Use v4 state prefix
    )
with col_quick:
    st.markdown("<div style='height: 29px;'></div>", unsafe_allow_html=True)
    quick_picks = [100, 500, 1000, 5000]
    q_cols = st.columns(len(quick_picks))
    for i, qp in enumerate(quick_picks):
        if q_cols[i].button(f"{int(qp)}", key=f"v4_quick_{qp}", help=f"Set bet to {qp} Tokens"): # Use v4 state prefix
            st.session_state.v4_quick_pick_holder = float(qp); st.info(f"Bet set to {qp}. Click Predict!"); time.sleep(0.1); st.rerun() # Use v4 state prefix

st.markdown('</div>', unsafe_allow_html=True) # End bet-option-card

# --- Play Button ---
st.markdown("<br>", unsafe_allow_html=True)
# Use themed name and icon in button text
if st.button(f"🔗 Predict Now! ({selected_theme_name})", use_container_width=True):
    # --- Input Validation ---
    valid_input = True
    if user_choice_input is None : st.error("Invalid prediction input.", icon="⚠️"); valid_input = False
    elif not (10.0 <= bet_amount <= 5000.0): st.error(f"Bet must be 10-5000 Tokens.", icon="💰"); valid_input = False
    elif bet_amount > st.session_state.v4_balance: st.error(f"Insufficient balance!", icon="💸"); valid_input = False # Use v4 state prefix

    if valid_input:
        try:
            # --- Update Balance & Jackpot ---
            st.session_state.v4_balance -= bet_amount # Use v4 state prefix
            st.session_state.v4_jackpot = OriginalGameLogic.calculate_jackpot(st.session_state.v4_jackpot, bet_amount) # Use v4 state prefix

            # --- Generate Draw ---
            draw1_digits, sum1, draw2_digits, sum2 = (None, -1, None, -1)
            with st.spinner("Reading Oracle Feeds..."):
                time.sleep(random.uniform(2.0, 3.5)) # Increased Duration
                draw1_digits, sum1, draw2_digits, sum2 = OriginalGameLogic.generate_draw()

                        # --- Display Draw Results (using V4 Theme labels and CORRECT variables) ---
            jodi_result = str(sum1) + str(sum2)
            st.markdown('<div class="result-animation">', unsafe_allow_html=True)
            # --- CORRECTED VARIABLES USED BELOW ---
            st.markdown(f'<div class="draw-display"><span class="feed-label">Feed 1:</span> <span class="digits">[{",".join(map(str, draw1_digits))}]</span> ➜ Signal 1: <span class="signal">{sum1}</span></div>', unsafe_allow_html=True) # Use draw1_digits
            st.markdown(f'<div class="draw-display"><span class="feed-label">Feed 2:</span> <span class="digits">[{",".join(map(str, draw2_digits))}]</span> ➜ Signal 2: <span class="signal">{sum2}</span></div>', unsafe_allow_html=True) # Use draw2_digits
            # --- END CORRECTED SECTION ---
            st.markdown(f'<div class="draw-display">Combined Signal: <span class="jodi-result">{jodi_result}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.session_state.v4_last_signals.append(jodi_result) # Use v4 state prefix

            # --- Check Win (using internal game type name) ---
            fixed_payout_multiplier = OriginalGameLogic.get_payout_multiplier(internal_game_type)
            won = OriginalGameLogic.check_win(internal_game_type, user_choice_input, draw1_digits, sum1, draw2_digits, sum2)
            winnings, jackpot_win, jackpot_win_amount = 0, False, 0

            if won:
                winnings = bet_amount * fixed_payout_multiplier
                st.session_state.v4_balance += winnings; st.session_state.v4_streak += 1 # Use v4 state prefix
                st.markdown('<div class="win-animation">', unsafe_allow_html=True)
                # Use themed name in success message
                st.success(f"✅ Prediction Correct! ('{selected_theme_name}': {user_choice_input}). Won {OriginalGameLogic.format_currency(winnings)}!", icon="🎉")

                # --- Jackpot & Streak ---
                # Logic checks internal name 'Royal Flush'
                if internal_game_type == "Royal Flush" and random.random() < OriginalGameLogic.JACKPOT_WIN_CHANCE_ON_FLUSH:
                      jackpot_win_amount = st.session_state.v4_jackpot; st.session_state.v4_balance += jackpot_win_amount # Use v4 state prefix
                      st.success(f"🏆🏆🏆 JACKPOT! Strong Signal Consensus! +{OriginalGameLogic.format_currency(jackpot_win_amount)}!", icon="🥳")
                      st.session_state.v4_jackpot = 5000.0; jackpot_win = True; st.balloons() # Use v4 state prefix

                if not jackpot_win:
                    streak_bonus_mult = OriginalGameLogic.get_streak_bonus_multiplier(st.session_state.v4_streak) # Use v4 state prefix
                    if streak_bonus_mult > 0:
                        bonus = bet_amount * streak_bonus_mult; st.session_state.v4_balance += bonus # Use v4 state prefix
                        st.success(f"🔥 Prediction Streak ({st.session_state.v4_streak}x)! +{OriginalGameLogic.format_currency(bonus)} ({streak_bonus_mult:.0%})!", icon="💫") # Use v4 state prefix
                    st.balloons()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                # Use themed name in error message
                st.error(f"❌ Prediction Incorrect ('{selected_theme_name}': {user_choice_input}).", icon="😢")
                st.session_state.v4_streak = 0 # Use v4 state prefix

            # --- Update History (store internal game type name, use v4 state key) ---
            st.session_state.v4_history.append({
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'game_type': internal_game_type, # Store internal name for logic consistency
                'user_choice': user_choice_input,
                'draw1_result': f"{''.join(map(str, draw1_digits))}*{sum1}",
                'draw2_result': f"{''.join(map(str, draw2_digits))}*{sum2}",
                'jodi': jodi_result, 'bet_amount': bet_amount, 'won': won,
                'payout': winnings + jackpot_win_amount, 'balance_after': st.session_state.v4_balance }) # Use v4 state prefix

            time.sleep(0.5); 
        except Exception as e: st.error(f"Prediction Error: {str(e)}", icon="🚨"); import traceback; st.error(traceback.format_exc())

# ============================================================
# History and Reset Sections
# ============================================================

# --- Game History Display ---
if st.session_state.v4_history: # Use v4 state prefix
    with st.expander("📊 Prediction History Log", expanded=False):
        try: V4ThemedUI.render_game_history(st.session_state.v4_history) # Use V4 UI & state key
        except Exception as e: st.error(f"History Error: {str(e)}", icon="💾")

# --- Reset Button ---
st.markdown("---")
if st.button("🔄 Reset Simulation"):
    # Use unique session state keys for reset
    keys_to_reset = ['v4_balance', 'v4_history', 'v4_last_signals', 'v4_jackpot', 'v4_streak', 'v4_quick_pick_holder'] # Use v4 state prefix
    for key in keys_to_reset:
        if key in st.session_state: del st.session_state[key]
    st.success("Simulation reset!", icon="✅"); time.sleep(1); st.rerun()