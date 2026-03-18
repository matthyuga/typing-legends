# Typing Lab aislado:
# - Fondo negro
# - Secuencia de 10 letras (a-z)
# - 2s por letra
# - Sin pantalla de perder
# - Si aciertas: verde y avanza
# - Si se acaba el tiempo: rojo y avanza

init -850 python:
    import random
    import math
    import renpy.store as S

    TYPING_LAB_BAR_FOLLOW_RATE = 0.975
    TYPING_LAB_BAR_HOLD_ON_RESET = 0.15
    TYPING_LAB_BAR_TIME_CURVE_GAMMA = 0.88
    TYPING_LAB_BAR_OSC_START_AMP = 0.045
    TYPING_LAB_BAR_OSC_FREQ_HZ = 7.0
    TYPING_LAB_BAR_OSC_DAMP = 7.5
    TYPING_LAB_BAR_FOLLOW_MIN = 0.45
    TYPING_LAB_BAR_FOLLOW_MAX = 2.25
    TYPING_LAB_BAR_ACCEL_START_RATIO = 0.50
    TYPING_LAB_BAR_ACCEL_MULT = 1.85

    def _typing_lab_color_lerp(c1, c2, t):
        t = max(0.0, min(1.0, float(t or 0.0)))
        r = int(round(c1[0] + (c2[0] - c1[0]) * t))
        g = int(round(c1[1] + (c2[1] - c1[1]) * t))
        b = int(round(c1[2] + (c2[2] - c1[2]) * t))
        return "#{:02X}{:02X}{:02X}".format(r, g, b)

    def typing_lab_bar_color_from_ratio(ratio):
        """Gradiente suave por tiempo restante.
        100-71 verde, 70-40 amarillo, 39-15 naranja, <=14 rojo (sin cortes bruscos).
        """
        r = max(0.0, min(1.0, float(ratio or 0.0)))
        # colores ancla
        c_green  = (67, 233, 123)   # #43E97B
        c_yellow = (255, 212, 0)    # #FFD400
        c_orange = (255, 154, 61)   # #FF9A3D
        c_red    = (255, 77, 77)    # #FF4D4D

        if r >= 0.71:
            # 0.71 -> 1.00 : amarillo a verde
            t = (r - 0.71) / max(0.0001, 1.00 - 0.71)
            return _typing_lab_color_lerp(c_yellow, c_green, t)
        elif r >= 0.40:
            # 0.40 -> 0.70 : naranja a amarillo
            t = (r - 0.40) / max(0.0001, 0.70 - 0.40)
            return _typing_lab_color_lerp(c_orange, c_yellow, t)
        elif r >= 0.15:
            # 0.15 -> 0.39 : rojo a naranja
            t = (r - 0.15) / max(0.0001, 0.39 - 0.15)
            return _typing_lab_color_lerp(c_red, c_orange, t)
        else:
            return "#FF4D4D"

    def typing_lab_default_state():
        return {
            "mode": "letters",      # letters | words
            "phase": "idle",         # idle | hit | timeout | done
            "sequence": [],
            "total": 10,
            "index": 0,
            "cursor": 0,
            "current_prompt": "",
            "current_letter": "",
            "hits": 0,
            "seconds_per_letter": 2.0,
            "time_left": 2.0,
            "feedback_time_left": 0.0,
            "total_score": 0,
            "score_popups": [],
            "bar_visual_ratio": 1.0,
            "bar_hold_left": float(TYPING_LAB_BAR_HOLD_ON_RESET),
            "bar_osc_amp": float(TYPING_LAB_BAR_OSC_START_AMP),
            "bar_osc_t": 0.0,
        }

    def typing_lab_word_bank():
        return [
            "hollow",
            "shinigami",
            "bleach",
            "bankai",
            "reiatsu",
            "zangetsu",
            "arrancar",
            "espada",
            "captain",
            "soul",
            "society",
            "ichigo",
            "rukia",
            "ulquiorra",
            "aizen",
        ]

    def typing_lab_phrase_bank():
        return [
            "el miedo nace en la oscuridad",
            "la desesperacion rompe el espiritu",
            "la voluntad supera el destino",
            "un corazon firme no se quiebra",
            "el orgullo sostiene la espada",
            "la calma precede al bankai",
            "el reiatsu revela la verdad",
            "la soledad tambien forja fuerza",
            "la batalla define la conviccion",
            "la esperanza no conoce limite",
            "cada cicatriz guarda una leccion",
            "sin riesgo no hay evolucion",
            "la fe protege el alma",
            "el honor pesa mas que el miedo",
            "el silencio anuncia la tormenta",
        ]

    def typing_lab_score_color(score_value=0):
        try:
            val = int(score_value)
        except:
            val = 0
        if val >= 30:
            return "#FF4D4D"
        if val >= 20:
            return "#FF9A3D"
        if val >= 10:
            return "#FFD400"
        return "#66FF99"

    def typing_lab_add_word_score_popup(word_len=0):
        st = getattr(S, "typing_lab_state", None)
        if not isinstance(st, dict):
            st = typing_lab_default_state()

        try:
            letters_score = int(word_len)
        except:
            letters_score = 0
        letters_score = max(0, letters_score)

        time_left = max(0.0, float(st.get("time_left", 0.0) or 0.0))
        points = int(round((letters_score + 10) * time_left))
        if points <= 0 and letters_score > 0:
            points = 1

        popups = list(st.get("score_popups", []) or [])
        popups.append({
            "text": ("+%d" % points),
            "color": str(typing_lab_score_color(points)),
            "xalign": 0.5,
            "yalign": 0.44,
            "vy": -0.12,
            "life": 0.70,
        })
        if len(popups) > 8:
            popups = popups[-8:]

        st["score_popups"] = popups
        st["total_score"] = int(st.get("total_score", 0) or 0) + int(points)
        S.typing_lab_state = st
        return int(points)

    def typing_lab_prepare(mode="letters", total_letters=10, seconds_per_letter=2.0, total_words=10, seconds_per_word=3.0, total_phrases=10, seconds_per_phrase=3.5):
        letters = list("abcdefghijklmnopqrstuvwxyz")
        use_mode = str(mode or "letters").lower().strip()
        if use_mode not in ("letters", "words", "phrases"):
            use_mode = "letters"

        try:
            n = int(total_letters)
        except:
            n = 10
        n = max(1, n)

        try:
            spl = float(seconds_per_letter)
        except:
            spl = 2.0
        spl = max(0.2, spl)

        if use_mode == "words":
            try:
                n_words = int(total_words)
            except:
                n_words = 10
            n_words = max(1, n_words)

            try:
                spw = float(seconds_per_word)
            except:
                spw = 3.0
            spw = max(0.2, spw)

            bank = list(typing_lab_word_bank())
            random.shuffle(bank)
            if len(bank) >= n_words:
                seq = bank[:n_words]
            else:
                seq = [random.choice(bank) for _ in range(n_words)]

            n = n_words
            spl = spw
        elif use_mode == "phrases":
            try:
                n_phrases = int(total_phrases)
            except:
                n_phrases = 10
            n_phrases = max(1, n_phrases)

            try:
                spp = float(seconds_per_phrase)
            except:
                spp = 3.5
            spp = max(0.2, spp)

            bank = list(typing_lab_phrase_bank())
            random.shuffle(bank)
            if len(bank) >= n_phrases:
                seq = bank[:n_phrases]
            else:
                seq = [random.choice(bank) for _ in range(n_phrases)]

            n = n_phrases
            spl = spp
        else:
            seq = [random.choice(letters) for _ in range(n)]

        first_prompt = str(seq[0] if seq else "a")
        first_words = [w for w in first_prompt.split(" ") if w]
        first_word = str(first_words[0] if first_words else "")

        st = {
            "mode": str(use_mode),
            "phase": "idle",
            "sequence": list(seq),
            "total": int(len(seq)),
            "index": 0,
            "cursor": 0,
            "word_cursor": 0,
            "phrase_words": list(first_words),
            "current_prompt": first_prompt,
            "current_letter": (str(first_word[:1] if first_word else "a") if use_mode == "phrases" else str(first_prompt[:1] if first_prompt else "a")),
            "hits": 0,
            "seconds_per_letter": float(spl),
            "time_left": float(spl),
            "feedback_time_left": 0.0,
            "total_score": 0,
            "score_popups": [],
            "bar_visual_ratio": 1.0,
            "bar_hold_left": float(TYPING_LAB_BAR_HOLD_ON_RESET),
            "bar_osc_amp": float(TYPING_LAB_BAR_OSC_START_AMP),
            "bar_osc_t": 0.0,
        }
        S.typing_lab_state = st
        return dict(st)

    def typing_lab_press_key(key_text=""):
        st = getattr(S, "typing_lab_state", None)
        if not isinstance(st, dict):
            st = typing_lab_default_state()

        phase = str(st.get("phase", "idle") or "idle")
        if phase != "idle":
            return dict(st)

        raw = str(key_text or "")
        low = raw.lower()
        got = low.strip()[:1]
        is_space = (low == " " or low == "space")

        if not is_space and not ("a" <= got <= "z"):
            return dict(st)

        mode = str(st.get("mode", "letters") or "letters")
        prompt = str(st.get("current_prompt", "") or "")
        cursor = int(st.get("cursor", 0) or 0)
        if cursor < 0:
            cursor = 0

        expected = ""
        if mode == "phrases":
            words = list(st.get("phrase_words", []) or [])
            word_idx = int(st.get("word_cursor", 0) or 0)
            word_idx = max(0, min(len(words), word_idx))

            if word_idx >= len(words):
                return dict(st)

            current_word = str(words[word_idx] or "")
            if current_word and cursor < len(current_word):
                expected = str(current_word[cursor]).lower()

            if is_space:
                if cursor == len(current_word) and word_idx < (len(words) - 1):
                    st["word_cursor"] = int(word_idx + 1)
                    st["cursor"] = 0
                    next_word = str(words[word_idx + 1] or "")
                    st["current_letter"] = str(next_word[:1] if next_word else "")
                    S.typing_lab_state = st
                return dict(st)
        elif mode == "words":
            if prompt and cursor < len(prompt):
                expected = str(prompt[cursor]).lower()
        else:
            expected = str(st.get("current_letter", "") or "").lower()

        if got != expected:
            return dict(st)

        if mode == "phrases":
            words = list(st.get("phrase_words", []) or [])
            word_idx = int(st.get("word_cursor", 0) or 0)
            current_word = str(words[word_idx] if (0 <= word_idx < len(words)) else "")
            cursor += 1
            st["cursor"] = int(cursor)
            if cursor < len(current_word):
                S.typing_lab_state = st
                return dict(st)
            typing_lab_add_word_score_popup(len(current_word))
            if word_idx < (len(words) - 1):
                S.typing_lab_state = st
                return dict(st)
        elif mode == "words":
            cursor += 1
            st["cursor"] = int(cursor)
            if cursor < len(prompt):
                S.typing_lab_state = st
                return dict(st)

        st["phase"] = "hit"
        st["hits"] = int(st.get("hits", 0) or 0) + 1
        st["feedback_time_left"] = 0.18
        S.typing_lab_state = st
        return dict(st)

    def typing_lab_tick(dt=0.02):
        st = getattr(S, "typing_lab_state", None)
        if not isinstance(st, dict):
            st = typing_lab_default_state()

        try:
            delta = float(dt)
        except:
            delta = 0.02
        if delta <= 0.0:
            delta = 0.02

        phase = str(st.get("phase", "idle") or "idle")

        if phase in ("hit", "timeout"):
            fb = float(st.get("feedback_time_left", 0.0) or 0.0)
            fb = max(0.0, fb - delta)
            st["feedback_time_left"] = fb
            S.typing_lab_state = st
            if fb <= 0.0:
                return typing_lab_advance()
            return dict(st)

        popups = list(st.get("score_popups", []) or [])
        if popups:
            next_popups = []
            for p in popups:
                life = max(0.0, float(p.get("life", 0.0) or 0.0) - delta)
                if life <= 0.0:
                    continue
                p["life"] = life
                p["yalign"] = float(p.get("yalign", 0.44) or 0.44) + (float(p.get("vy", -0.12) or -0.12) * delta)
                next_popups.append(p)
            st["score_popups"] = next_popups

        if phase != "idle":
            S.typing_lab_state = st
            return dict(st)

        left = float(st.get("time_left", 0.0) or 0.0)
        left = max(0.0, left - delta)
        st["time_left"] = left

        spl = max(0.0001, float(st.get("seconds_per_letter", 2.0) or 2.0))
        target_ratio_raw = max(0.0, min(1.0, left / spl))
        # Curva no lineal visual (sin alterar el timing real): sensación más orgánica.
        target_ratio = math.pow(target_ratio_raw, max(0.10, float(TYPING_LAB_BAR_TIME_CURVE_GAMMA)))

        vis_ratio = max(0.0, min(1.0, float(st.get("bar_visual_ratio", target_ratio) or target_ratio)))
        hold_left = max(0.0, float(st.get("bar_hold_left", 0.0) or 0.0))

        # Oscilación amortiguada breve al reset de letra (jelly feel).
        osc_amp = max(0.0, float(st.get("bar_osc_amp", 0.0) or 0.0))
        osc_t = max(0.0, float(st.get("bar_osc_t", 0.0) or 0.0))
        osc_t += delta
        osc_amp *= math.exp(-max(0.1, float(TYPING_LAB_BAR_OSC_DAMP)) * delta)
        st["bar_osc_t"] = osc_t
        st["bar_osc_amp"] = osc_amp

        if hold_left > 0.0:
            hold_left = max(0.0, hold_left - delta)
            st["bar_hold_left"] = hold_left
        else:
            # Velocidad dinámica: inicio lento, medio normal, final rápido.
            progress = max(0.0, min(1.0, 1.0 - target_ratio_raw))
            dyn_follow = float(TYPING_LAB_BAR_FOLLOW_MIN) + (float(TYPING_LAB_BAR_FOLLOW_MAX) - float(TYPING_LAB_BAR_FOLLOW_MIN)) * (progress ** 1.25)

            # Acelerón desde el 50% de barra hacia abajo para que trail alcance al front.
            accel_start = max(0.0, min(1.0, float(TYPING_LAB_BAR_ACCEL_START_RATIO)))
            if target_ratio_raw <= accel_start:
                tail_progress = (accel_start - target_ratio_raw) / max(0.0001, accel_start)
                dyn_follow *= (1.0 + (max(0.0, float(TYPING_LAB_BAR_ACCEL_MULT) - 1.0) * tail_progress))

            alpha = 1.0 - math.exp(-max(0.05, dyn_follow) * delta)
            vis_ratio = vis_ratio + (target_ratio - vis_ratio) * alpha
            st["bar_visual_ratio"] = max(0.0, min(1.0, vis_ratio))

        if left <= 0.0:
            st["phase"] = "timeout"
            st["feedback_time_left"] = 0.20

        S.typing_lab_state = st
        return dict(st)

    def typing_lab_advance():
        st = getattr(S, "typing_lab_state", None)
        if not isinstance(st, dict):
            st = typing_lab_default_state()

        idx = int(st.get("index", 0) or 0) + 1
        seq = list(st.get("sequence", []) or [])
        total = int(st.get("total", len(seq)) or len(seq) or 0)
        spl = float(st.get("seconds_per_letter", 2.0) or 2.0)

        st["index"] = int(idx)

        if idx >= total:
            st["phase"] = "done"
            st["cursor"] = 0
            st["word_cursor"] = 0
            st["phrase_words"] = []
            st["current_prompt"] = ""
            st["current_letter"] = ""
            st["time_left"] = 0.0
            st["feedback_time_left"] = 0.0
            st["score_popups"] = []
            st["bar_visual_ratio"] = 0.0
            st["bar_hold_left"] = 0.0
            st["bar_osc_amp"] = 0.0
            st["bar_osc_t"] = 0.0
        else:
            new_prompt = str(seq[idx])
            st["phase"] = "idle"
            st["cursor"] = 0
            st["word_cursor"] = 0
            st["current_prompt"] = str(new_prompt)
            phrase_words = [w for w in str(new_prompt).split(" ") if w]
            st["phrase_words"] = list(phrase_words)
            if str(st.get("mode", "letters") or "letters") == "phrases":
                first_word = str(phrase_words[0] if phrase_words else "")
                st["current_letter"] = str(first_word[:1] if first_word else "")
            else:
                st["current_letter"] = str(new_prompt[:1] if new_prompt else "")
            st["time_left"] = float(spl)
            st["feedback_time_left"] = 0.0
            st["score_popups"] = []
            st["bar_visual_ratio"] = 1.0
            st["bar_hold_left"] = float(TYPING_LAB_BAR_HOLD_ON_RESET)
            st["bar_osc_amp"] = float(TYPING_LAB_BAR_OSC_START_AMP)
            st["bar_osc_t"] = 0.0

        S.typing_lab_state = st
        return dict(st)

    store.typing_lab_default_state = typing_lab_default_state
    store.typing_lab_prepare = typing_lab_prepare
    store.typing_lab_press_key = typing_lab_press_key
    store.typing_lab_tick = typing_lab_tick
    store.typing_lab_advance = typing_lab_advance
    store.typing_lab_bar_color_from_ratio = typing_lab_bar_color_from_ratio
    store.typing_lab_score_color = typing_lab_score_color


default typing_lab_state = {
    "mode": "letters",
    "phase": "idle",
    "sequence": [],
    "total": 10,
    "index": 0,
    "cursor": 0,
    "word_cursor": 0,
    "phrase_words": [],
    "current_prompt": "",
    "current_letter": "",
    "hits": 0,
    "seconds_per_letter": 2.0,
    "time_left": 2.0,
    "feedback_time_left": 0.0,
    "total_score": 0,
    "score_popups": [],
    "bar_visual_ratio": 1.0,
    "bar_hold_left": 0.0,
    "bar_osc_amp": 0.0,
    "bar_osc_t": 0.0,
}

default typing_lab_selected_mode = "letters"

screen typing_lab_mode_menu():
    modal True
    zorder 265

    add Solid("#000000")

    frame:
        background "#171717"
        xalign 0.5
        yalign 0.5
        padding (34, 28)

        vbox:
            spacing 18
            xalign 0.5

            text "Typing Lab":
                size 56
                bold True
                color "#FFFFFF"
                xalign 0.5

            text "Modo":
                size 34
                color "#D0D0D0"
                xalign 0.5

            hbox:
                spacing 12
                xalign 0.5

                textbutton "Letras":
                    action SetVariable("typing_lab_selected_mode", "letters")
                    background ("#2A8F4A" if typing_lab_selected_mode == "letters" else "#2A2A2A")
                    xpadding 16
                    ypadding 10

                textbutton "Palabras":
                    action SetVariable("typing_lab_selected_mode", "words")
                    background ("#2A8F4A" if typing_lab_selected_mode == "words" else "#2A2A2A")
                    xpadding 16
                    ypadding 10

                textbutton "Frases":
                    action SetVariable("typing_lab_selected_mode", "phrases")
                    background ("#2A8F4A" if typing_lab_selected_mode == "phrases" else "#2A2A2A")
                    xpadding 16
                    ypadding 10

            textbutton "Iniciar":
                xalign 0.5
                action Return("start")


screen typing_lab_qte_simple():
    modal True
    zorder 260

    default _letters = "abcdefghijklmnopqrstuvwxyz"

    python:
        _st = getattr(store, "typing_lab_state", {})
        _phase = str(_st.get("phase", "idle") or "idle")
        _mode = str(_st.get("mode", "letters") or "letters")
        _cur = str(_st.get("current_letter", "") or "")
        _prompt = str(_st.get("current_prompt", _cur) or "")
        _cursor = int(_st.get("cursor", 0) or 0)
        _idx = int(_st.get("index", 0) or 0)
        _tot = int(_st.get("total", 10) or 10)
        _total_score = int(_st.get("total_score", 0) or 0)
        _score_popups = list(_st.get("score_popups", []) or [])
        _spl = float(_st.get("seconds_per_letter", 2.0) or 2.0)
        _left = float(_st.get("time_left", 0.0) or 0.0)
        _ratio = (0.0 if _spl <= 0.0 else max(0.0, min(1.0, _left / _spl)))
        _vis_ratio = float(_st.get("bar_visual_ratio", _ratio) or _ratio)
        _vis_ratio = max(0.0, min(1.0, _vis_ratio))

        # Subpixel feel: borde/brillo con xpos fraccional + oscilación amortiguada.
        _osc_amp = max(0.0, float(_st.get("bar_osc_amp", 0.0) or 0.0))
        _osc_t = max(0.0, float(_st.get("bar_osc_t", 0.0) or 0.0))
        _osc = (_osc_amp * math.sin(2.0 * math.pi * float(TYPING_LAB_BAR_OSC_FREQ_HZ) * _osc_t))

        _bar_max = 520
        _front_ratio = max(0.0, min(1.0, _ratio))
        _lag_ratio = max(_front_ratio, max(0.0, min(1.0, _vis_ratio + _osc)))
        _front_fill = int(max(0, min(_bar_max, int(_bar_max * _front_ratio))))
        _lag_fill = int(max(0, min(_bar_max, int(_bar_max * _lag_ratio))))
        _front_edge_x = (10.0 + (_front_ratio * _bar_max) - 1.0)
        _lag_edge_x = (10.0 + (_lag_ratio * _bar_max) - 1.5)
        _timer_txt = ("%.2f" % float(_left))

        fn_bar_color = getattr(store, "typing_lab_bar_color_from_ratio", None)
        _front_color = fn_bar_color(_front_ratio) if callable(fn_bar_color) else "#43E97B"

        if _phase == "hit":
            _letter_color = "#66FF99"
        elif _phase == "timeout":
            _letter_color = "#FF4D4D"
        else:
            _letter_color = "#FFFFFF"

        _word_markup = _prompt
        if _mode == "words":
            _cursor = max(0, min(len(_prompt), _cursor))
            if _phase == "hit":
                _word_markup = "{color=#66FF99}%s{/color}" % _prompt
            else:
                _typed = _prompt[:_cursor]
                _pending = _prompt[_cursor:]
                _word_markup = "{color=#66FF99}%s{/color}{color=#FFFFFF}%s{/color}" % (_typed, _pending)
        elif _mode == "phrases":
            _words = [w for w in _prompt.split(" ") if w]
            _word_cursor = int(_st.get("word_cursor", 0) or 0)
            _word_cursor = max(0, min(len(_words), _word_cursor))
            _cursor = int(_st.get("cursor", 0) or 0)
            _markup_parts = []
            for _i, _w in enumerate(_words):
                if _phase == "hit" or _i < _word_cursor:
                    _markup_parts.append("{color=#66FF99}%s{/color}" % _w)
                elif _i == _word_cursor:
                    _local_cursor = max(0, min(len(_w), _cursor))
                    _typed = _w[:_local_cursor]
                    _pending = _w[_local_cursor:]
                    _markup_parts.append("{color=#66FF99}%s{/color}{color=#FFFFFF}%s{/color}" % (_typed, _pending))
                else:
                    _markup_parts.append("{color=#FFFFFF}%s{/color}" % _w)
            _word_markup = " ".join(_markup_parts)

    timer 0.02 repeat True action Function(getattr(store, "typing_lab_tick", None), 0.02)

    for _k in _letters:
        key _k action Function(getattr(store, "typing_lab_press_key", None), _k)
    key "K_SPACE" action Function(getattr(store, "typing_lab_press_key", None), "space")


    if _phase == "done":
        timer 0.02 action Return("win")

    add Solid("#000000")


    if _phase != "done":
        text ("Escribe y pulsa ESPACIO para pasar de palabra" if _mode == "phrases" else "Escribe en orden"):
            xalign 0.5
            yalign 0.10
            size 24
            color "#BDBDBD"

        if _mode in ("words", "phrases"):
            text _word_markup:
                xalign 0.5
                yalign 0.40
                size 88
                bold True
                text_align 0.5
                min_width 680
        else:
            text (_cur if _cur else "-"):
                xalign 0.5
                yalign 0.42
                size 140
                bold True
                color _letter_color

        for _p in _score_popups:
            text str(_p.get("text", "+0")):
                xalign float(_p.get("xalign", 0.5) or 0.5)
                yalign float(_p.get("yalign", 0.44) or 0.44)
                size 42
                bold True
                color str(_p.get("color", "#66FF99") or "#66FF99")
                outlines [(2, "#00000099", 0, 0)]

        frame:
            background "#1A1A1A"
            xalign 0.5
            yalign 0.78
            xsize 540
            ysize 30
            padding (0, 0)

            fixed:
                xsize 540
                ysize 30

                # Barra dual: lag (trail) + front (real), para sensación más líquida.
                frame:
                    background "#8A8A8A"
                    xpos 10
                    ypos 6
                    xsize _lag_fill
                    ysize 18
                    padding (0, 0)

                frame:
                    background _front_color
                    xpos 10
                    ypos 6
                    xsize _front_fill
                    ysize 18
                    padding (0, 0)

                # Micro-segmentación visual (overlay semitransparente).
                for _gx in range(10, 531, 13):
                    add Solid("#FFFFFF22") xpos _gx ypos 6 xsize 1 ysize 18

                # Subpixel feel: brillo/borde de avance con xpos fraccional.
                add Solid("#FFFFFF66") xpos _lag_edge_x ypos 6 xsize 2 ysize 18
                add Solid("#FFFFFFAA") xpos _front_edge_x ypos 6 xsize 2 ysize 18

        text ("Tiempo: " + _timer_txt + " s"):
            xalign 0.5
            yalign 0.86
            size 28
            color "#D0D0D0"

        text ((("Frase %d/%d" if _mode == "phrases" else ("Palabra %d/%d" if _mode == "words" else "Letra %d/%d"))) % (int(min(_idx + 1, max(1, _tot))), int(max(1, _tot)))):
            xalign 0.5
            yalign 0.91
            size 30
            color "#D0D0D0"

        text ("Puntos: %d" % _total_score):
            xalign 0.5
            yalign 0.96
            size 26
            color "#F3F3F3"

screen typing_lab_win_popup():
    modal True
    zorder 270

    add Solid("#000000")

    frame:
        background "#0000"
        xalign 0.5
        yalign 0.5
        padding (24, 20)

        vbox:
            spacing 18

            text "GANASTE":
                size 78
                bold True
                color "#66FF99"
                xalign 0.5

            textbutton "Volver al menú":
                xalign 0.5
                action Return("menu")

            textbutton "Volver a intentar":
                xalign 0.5
                action Return("retry")

label typing_lab_start:
    $ typing_lab_state = typing_lab_default_state()
    $ _typing_lab_menu_action = renpy.call_screen("typing_lab_mode_menu")
    if _typing_lab_menu_action != "start":
        return

    if typing_lab_selected_mode == "words":
        $ typing_lab_prepare(mode="words", total_words=10, seconds_per_word=3.0)
    elif typing_lab_selected_mode == "phrases":
        $ typing_lab_prepare(mode="phrases", total_phrases=10, seconds_per_phrase=3.5)
    elif typing_lab_selected_mode == "letters":
        $ typing_lab_prepare(mode="letters", total_letters=10, seconds_per_letter=2.0)
    else:
        jump typing_lab_start

label typing_lab_round:
    $ _typing_lab_simple_result = renpy.call_screen("typing_lab_qte_simple")
    if _typing_lab_simple_result != "win":
        jump typing_lab_round

    $ _typing_lab_popup_action = renpy.call_screen("typing_lab_win_popup")
    if _typing_lab_popup_action == "retry":
        if typing_lab_selected_mode == "words":
            $ typing_lab_prepare(mode="words", total_words=10, seconds_per_word=3.0)
        elif typing_lab_selected_mode == "phrases":
            $ typing_lab_prepare(mode="phrases", total_phrases=10, seconds_per_phrase=3.5)
        else:
            $ typing_lab_prepare(mode="letters", total_letters=10, seconds_per_letter=2.0)
        jump typing_lab_round
    return
