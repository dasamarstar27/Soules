import threading
import json
import os
import math
import random
import time

# =========================
# REGION THEMES
# =========================

REGION_THEMES = {
    "Whispering Woods":   {"bg": (18, 45, 18),  "accent": (60, 160, 60),   "sky": (30, 60, 30)},
    "Ashen Wastes":       {"bg": (55, 35, 20),  "accent": (180, 100, 40),  "sky": (70, 45, 25)},
    "Crimson Forge":      {"bg": (80, 15, 10),  "accent": (220, 60, 20),   "sky": (100, 20, 10)},
    "crimson Forge":      {"bg": (80, 15, 10),  "accent": (220, 60, 20),   "sky": (100, 20, 10)},
    "Frostbound Tundra":  {"bg": (30, 60, 90),  "accent": (160, 210, 240), "sky": (50, 90, 130)},
    "Sunken Coast":       {"bg": (10, 45, 90),  "accent": (40, 140, 200),  "sky": (15, 60, 110)},
    "Ironpeak Mountains": {"bg": (50, 50, 60),  "accent": (140, 140, 160), "sky": (65, 65, 80)},
    "Blight Swamp":       {"bg": (20, 45, 20),  "accent": (80, 160, 40),   "sky": (25, 55, 25)},
    "Shadow Vale":        {"bg": (15, 10, 35),  "accent": (100, 60, 180),  "sky": (20, 15, 45)},
    "Infernal Depths":    {"bg": (90, 20, 5),   "accent": (230, 80, 10),   "sky": (110, 30, 5)},
    "Celestial Expanse":  {"bg": (5, 5, 50),    "accent": (100, 150, 255), "sky": (10, 10, 70)},
    "Riftlands":          {"bg": (35, 5, 55),   "accent": (160, 60, 220),  "sky": (45, 10, 70)},
    "Abyss of Souls":     {"bg": (5, 5, 15),    "accent": (80, 0, 120),    "sky": (8, 5, 20)},
    "Creator's Realm":    {"bg": (50, 40, 10),  "accent": (255, 215, 0),   "sky": (70, 55, 15)},
}

DEFAULT_THEME = {"bg": (20, 20, 30), "accent": (100, 100, 140), "sky": (25, 25, 40)}

STATUS_COLORS = {
    "burn":      (255, 100, 30),
    "poison":    (90,  200, 50),
    "bleed":     (200, 30,  30),
    "freeze":    (140, 210, 255),
    "void":      (160, 50,  220),
    "curse":     (130, 0,   130),
    "fear":      (160, 110, 0),
    "shock":     (255, 230, 50),
    "sleep":     (100, 100, 210),
    "magma":     (210, 80,  20),
    "regen":     (50,  210, 100),
    "heal_tick": (80,  255, 140),
    "creation":  (255, 215, 0),
    "stun":      (255, 200, 0),
    "root":      (120, 180, 40),
    "slow_time": (100, 160, 220),
}

BUFF_COLORS = {
    "giant_strength":    (220, 80,  20),
    "defense_up":        (60,  120, 220),
    "speed_up":          (100, 220, 255),
    "crit_up":           (255, 200, 30),
    "heal_tick":         (80,  255, 140),
    "rebirth":           (255, 100, 180),
    "warp":              (160, 60,  220),
    "moon_guard":        (180, 180, 255),
    "fortress":          (80,  130, 200),
    "stability":         (140, 200, 140),
    "divine_luck":       (255, 215, 0),
    "double_cast":       (255, 140, 0),
    "reflect":           (200, 200, 255),
    "barrier":           (60,  180, 255),
    "supercharge":       (255, 80,  0),
    "elemental_balance": (120, 255, 180),
    "fusion_boost":      (200, 100, 255),
}

POPUP_REGION_BG = {
    "Whispering Woods":   (20, 60, 20),
    "Ashen Wastes":       (70, 45, 20),
    "Crimson Forge":      (90, 20, 10),
    "crimson Forge":      (90, 20, 10),
    "Frostbound Tundra":  (40, 80, 120),
    "Sunken Coast":       (15, 55, 110),
    "Ironpeak Mountains": (55, 55, 70),
    "Blight Swamp":       (25, 55, 25),
    "Shadow Vale":        (20, 10, 45),
    "Infernal Depths":    (100, 25, 5),
    "Celestial Expanse":  (10, 10, 65),
    "Riftlands":          (40, 8,  65),
    "Abyss of Souls":     (8,  5,  18),
    "Creator's Realm":    (60, 50, 10),
}

W, H = 380, 640
FPS  = 30


def _rgb(t):
    return f"rgb({t[0]},{t[1]},{t[2]})"


class GameUI:
    def __init__(self, player_ref):
        self.player        = player_ref
        self.current_enemy = None
        self._popup        = None
        self._lock         = threading.Lock()
        self._running      = False
        self._thread       = None
        self._boss_burst   = []
        self._web_mode     = bool(os.environ.get("SOULCRYPT_WEB"))
        self._state_file   = os.environ.get("SOULCRYPT_STATE_FILE", "/tmp/soulcrypt_state.json")

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def set_enemy(self, enemy):
        with self._lock:
            self.current_enemy = enemy

    def clear_enemy(self):
        with self._lock:
            self.current_enemy = None

    def show_loot_popup(self, item_name, region=""):
        with self._lock:
            self._popup = {
                "text":   item_name,
                "color":  [180, 220, 255],
                "timer":  FPS * 4,
                "boss":   False,
                "region": region,
            }

    def show_boss_drop_popup(self, item_name, region=""):
        with self._lock:
            self._popup = {
                "text":   item_name,
                "color":  [255, 215, 0],
                "timer":  FPS * 5,
                "boss":   True,
                "region": region,
            }

    def _run(self):
        if self._web_mode:
            self._run_web()
        else:
            self._run_pygame()

    # ------------------------------------------------------------------
    # WEB MODE — write JSON state file for Flask to serve
    # ------------------------------------------------------------------

    def _run_web(self):
        while self._running:
            try:
                with self._lock:
                    enemy = self.current_enemy
                    popup = self._popup
                    if popup and popup.get("timer", 0) > 0:
                        self._popup["timer"] -= 1

                p      = self.player
                region = p.get("region", "")
                theme  = REGION_THEMES.get(region, DEFAULT_THEME)

                state = {
                    "player": {
                        "name":            p.get("name", "Hero"),
                        "level":           p.get("level", 1),
                        "hp":              p.get("hp", 0),
                        "max_hp":          p.get("max_hp", 1),
                        "mana":            p.get("mana", 0),
                        "xp":              p.get("xp", 0),
                        "gold":            p.get("gold", 0),
                        "base_def":        p.get("def", 0),
                        "arm_def":         p["armour"]["def"]  if p.get("armour") else 0,
                        "arm_name":        p["armour"]["name"] if p.get("armour") else "None",
                        "region":          region,
                        "status":          {k: v for k, v in p.get("status", {}).items()},
                        "active_buffs":    {k: v for k, v in p.get("active_buffs", {}).items()},
                        "companions":      [
                            {"name": c.get("name",""), "stage": c.get("stage",0), "element": c.get("element","")}
                            for c in p.get("companions", [])
                        ],
                        "inventory_count":     len(p.get("inventory", [])),
                        "weapons_count":       len(p.get("weapons", [])),
                        "armours_count":       len(p.get("armours", [])),
                        "runes_count":         len(p.get("runes", [])),
                        "forge_cores_count":   len(p.get("forge_cores", [])),
                    },
                    "enemy": {
                        "name":   enemy.get("name", "Enemy"),
                        "hp":     enemy.get("hp", 0),
                        "max_hp": enemy.get("max_hp", enemy.get("hp", 1)),
                        "status": {k: v for k, v in enemy.get("status", {}).items()},
                    } if enemy and enemy.get("hp", 0) > 0 else None,
                    "popup": {
                        "text":   popup["text"],
                        "boss":   popup["boss"],
                        "region": popup.get("region", ""),
                        "timer":  popup["timer"],
                    } if popup and popup.get("timer", 0) > 0 else None,
                    "theme": {
                        "bg":     list(theme["bg"]),
                        "accent": list(theme["accent"]),
                        "sky":    list(theme["sky"]),
                    },
                }

                with open(self._state_file, "w") as f:
                    json.dump(state, f)

            except Exception:
                pass

            time.sleep(0.5)

    # ------------------------------------------------------------------
    # LOCAL PYGAME MODE — original rendering
    # ------------------------------------------------------------------

    def _run_pygame(self):
        try:
            import pygame
        except ImportError:
            return

        os.environ.setdefault("SDL_VIDEODRIVER", "x11")
        pygame.init()
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("SoulCrypt — Status")
        clock  = pygame.time.Clock()

        font_xl = pygame.font.SysFont("monospace", 28, bold=True)
        font_lg = pygame.font.SysFont("monospace", 22, bold=True)
        font_md = pygame.font.SysFont("monospace", 16)
        font_sm = pygame.font.SysFont("monospace", 13)

        tick = 0

        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    pygame.quit()
                    return

            tick += 1
            p      = self.player
            region = p.get("region", "")
            theme  = REGION_THEMES.get(region, DEFAULT_THEME)

            _draw_gradient(screen, theme["sky"], theme["bg"], W, H)
            _draw_particles(screen, tick, theme["accent"])

            name = p.get("name", "Hero")
            lvl  = p.get("level", 1)
            _draw_text_shadow(screen, font_lg, f"{name}  •  Lv.{lvl}", (W // 2, 28), theme["accent"])

            reg_surf = font_sm.render(f"[ {region} ]", True, _blend(theme["accent"], (255, 255, 255), 0.55))
            screen.blit(reg_surf, reg_surf.get_rect(center=(W // 2, 52)))

            y = 74

            y = _draw_bar(screen, font_sm,
                          label="HP", value=p.get("hp", 0), max_val=p.get("max_hp", 1),
                          x=20, y=y, w=W - 40,
                          filled=(30, 200, 80), empty=(60, 30, 30))

            y = _draw_bar(screen, font_sm,
                          label="MP", value=p.get("mana", 0), max_val=20,
                          x=20, y=y + 5, w=W - 40,
                          filled=(60, 100, 230), empty=(20, 20, 60))

            y += 4
            base_def = p.get("def", 0)
            arm_def  = p["armour"]["def"]  if p.get("armour") else 0
            arm_name = p["armour"]["name"] if p.get("armour") else "None"
            def_str  = f"DEF {base_def}+{arm_def}  Shield {arm_name}"
            def_surf = font_sm.render(def_str, True, (120, 180, 255))
            screen.blit(def_surf, def_surf.get_rect(center=(W // 2, y + 8)))
            y += 20

            y += 6
            gold_s = font_md.render(f"Souls: {p.get('gold', 0)}", True, (220, 200, 80))
            xp_s   = font_md.render(f"XP: {p.get('xp', 0)}/{p.get('level', 1) * 50}", True, (180, 180, 255))
            screen.blit(gold_s, (20, y))
            screen.blit(xp_s,   (W - xp_s.get_width() - 20, y))
            y += 26

            y = _divider(screen, y, theme["accent"])

            with self._lock:
                enemy = self.current_enemy

            if enemy and enemy.get("hp", 0) > 0:
                ename = enemy.get("name", "Enemy")
                _draw_text_shadow(screen, font_md, f"vs  {ename}", (W // 2, y + 10), (220, 80, 60))
                y += 26
                y = _draw_bar(screen, font_sm,
                              label="HP", value=enemy.get("hp", 0),
                              max_val=enemy.get("max_hp", enemy.get("hp", 1)),
                              x=20, y=y, w=W - 40,
                              filled=(210, 50, 50), empty=(60, 20, 20))
                e_st = enemy.get("status", {})
                if e_st:
                    y += 4
                    y = _draw_tags(screen, font_sm, e_st, {}, x=20, y=y, label="Enemy:")
                y = _divider(screen, y + 4, theme["accent"])

            p_status = p.get("status", {})
            p_buffs  = p.get("active_buffs", {})
            if p_status or p_buffs:
                y = _draw_tags(screen, font_sm, p_status, p_buffs, x=20, y=y, label="Effects:")
                y = _divider(screen, y + 4, theme["accent"])

            companions = p.get("companions", [])
            if companions:
                lbl = font_sm.render("Companions", True, (160, 160, 200))
                screen.blit(lbl, (20, y))
                y += 20
                for c in companions:
                    stage = c.get("stage", 0)
                    stars = "★" * stage + "☆" * (2 - stage)
                    line  = font_sm.render(f"  {c['name']}  {stars}  [{c['element']}]", True, (200, 200, 240))
                    screen.blit(line, (20, y))
                    y += 18
                y = _divider(screen, y + 2, theme["accent"])

            counts = (f"Inv:{len(p.get('inventory',[]))}  "
                      f"Wpn:{len(p.get('weapons',[]))}  "
                      f"Arm:{len(p.get('armours',[]))}  "
                      f"Rune:{len(p.get('runes',[]))}  "
                      f"Core:{len(p.get('forge_cores',[]))}")
            ct = font_sm.render(counts, True, (140, 140, 160))
            screen.blit(ct, ct.get_rect(center=(W // 2, y + 10)))

            with self._lock:
                burst = list(self._boss_burst)

            alive = []
            for pt in burst:
                pt["x"] += pt["vx"]
                pt["y"] += pt["vy"]
                pt["life"] -= 1
                if pt["life"] > 0:
                    alpha_r = pt["life"] / pt["max_life"]
                    c = tuple(int(v * alpha_r) for v in pt["color"])
                    pygame.draw.circle(screen, c, (int(pt["x"]), int(pt["y"])), pt["r"])
                    alive.append(pt)

            with self._lock:
                self._boss_burst = alive

            with self._lock:
                popup = self._popup
                if popup and popup["timer"] > 0:
                    self._popup["timer"] -= 1

            if popup and popup["timer"] > 0:
                _draw_popup(screen, font_xl, font_md, font_sm, popup, tick, W, H)

            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()


# =========================
# DRAWING HELPERS (pygame local mode)
# =========================

def _draw_gradient(surface, top, bot, w, h):
    import pygame
    for y in range(h):
        t = y / h
        color = (
            int(top[0] + (bot[0] - top[0]) * t),
            int(top[1] + (bot[1] - top[1]) * t),
            int(top[2] + (bot[2] - top[2]) * t),
        )
        pygame.draw.line(surface, color, (0, y), (w, y))


def _draw_particles(surface, tick, color):
    import pygame
    for i in range(8):
        x = (i * 53 + tick * (1 + i % 3)) % W
        y = (i * 79 + tick * (2 - i % 2)) % H
        c = tuple(max(0, min(255, v)) for v in color)
        pygame.draw.circle(surface, c, (int(x), int(y)), 2)


def _draw_text_shadow(surface, font, text, center, color):
    shadow = font.render(text, True, (0, 0, 0))
    main   = font.render(text, True, color)
    cx, cy = center
    surface.blit(shadow, shadow.get_rect(center=(cx + 1, cy + 1)))
    surface.blit(main,   main.get_rect(center=(cx, cy)))


def _draw_bar(surface, font_sm, label, value, max_val, x, y, w, filled, empty):
    import pygame
    bar_h   = 22
    value   = max(0, value)
    max_val = max(1, max_val)
    lbl = font_sm.render(label, True, (200, 200, 200))
    surface.blit(lbl, (x, y + 3))
    bx = x + 30
    pygame.draw.rect(surface, (20, 20, 20), (bx, y, w - 30, bar_h), border_radius=4)
    pygame.draw.rect(surface, empty,        (bx, y, w - 30, bar_h), border_radius=4)
    fill_w = int((w - 30) * min(value, max_val) / max_val)
    if fill_w > 0:
        pygame.draw.rect(surface, filled, (bx, y, fill_w, bar_h), border_radius=4)
    pygame.draw.rect(surface, (80, 80, 80), (bx, y, w - 30, bar_h), 1, border_radius=4)
    val_txt = font_sm.render(f"{int(value)}/{int(max_val)}", True, (230, 230, 230))
    surface.blit(val_txt, val_txt.get_rect(center=(bx + (w - 30) // 2, y + bar_h // 2)))
    return y + bar_h


def _divider(surface, y, color):
    import pygame
    c = tuple(max(0, v // 2) for v in color)
    pygame.draw.line(surface, c, (20, y), (W - 20, y))
    return y + 6


def _draw_tags(surface, font_sm, statuses, buffs, x, y, label=""):
    import pygame
    if label:
        lbl = font_sm.render(label, True, (160, 160, 200))
        surface.blit(lbl, (x, y))
        y += 18
    cx = x
    for name, turns in {**statuses, **buffs}.items():
        color = STATUS_COLORS.get(name) or BUFF_COLORS.get(name) or (180, 180, 180)
        tag   = font_sm.render(f"{name[:8]} {turns}", True, color)
        tw    = tag.get_width() + 6
        if cx + tw > W - 20:
            cx  = x
            y  += 20
        pygame.draw.rect(surface, (30, 30, 40), (cx, y, tw, 17), border_radius=3)
        pygame.draw.rect(surface, color,        (cx, y, tw, 17), 1, border_radius=3)
        surface.blit(tag, (cx + 3, y + 2))
        cx += tw + 4
    return y + 22


def _blend(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _make_burst_particles(cx, cy, count=40):
    particles = []
    colors = [(255, 215, 0), (255, 180, 50), (255, 120, 0), (255, 255, 150), (255, 80, 80)]
    for i in range(count):
        angle  = (i / count) * math.pi * 2 + random.uniform(-0.2, 0.2)
        speed  = random.uniform(2.5, 7.0)
        life   = random.randint(20, 45)
        particles.append({
            "x": cx, "y": cy,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "color": random.choice(colors),
            "r": random.randint(2, 5),
            "life": life,
            "max_life": life,
        })
    return particles


def _draw_popup(surface, font_xl, font_md, font_sm, popup, tick, W, H):
    import pygame
    timer   = popup["timer"]
    is_boss = popup["boss"]
    region  = popup.get("region", "")
    text    = popup["text"]
    fade    = min(1.0, timer / (FPS * 0.5))
    alpha   = int(255 * fade)
    pw = 340
    ph = 160 if is_boss else 120
    px = (W - pw) // 2
    py = H - ph - 30
    bg_base = POPUP_REGION_BG.get(region, (20, 20, 40))
    overlay = pygame.Surface((pw, ph), pygame.SRCALPHA)
    overlay.fill((*bg_base, min(220, alpha)))
    if is_boss:
        glow_t   = 0.5 + 0.5 * math.sin(tick * 0.15)
        glow_col = (int(255 * glow_t), int(180 * glow_t), 0)
        pygame.draw.rect(overlay, (*glow_col, min(200, alpha)), (0, 0, pw, ph), 3, border_radius=10)
    else:
        pygame.draw.rect(overlay, (100, 160, 220, min(180, alpha)), (0, 0, pw, ph), 2, border_radius=8)
    surface.blit(overlay, (px, py))
    if is_boss:
        for ring_w, ring_alpha_frac in ((5, 0.7), (3, 1.0), (2, 0.5)):
            glow_t = 0.5 + 0.5 * math.sin(tick * 0.2)
            col    = (int(255 * glow_t), int(180 * glow_t), 0)
            pygame.draw.rect(surface, (*col, min(200, int(alpha * ring_alpha_frac))),
                             (px - ring_w, py - ring_w, pw + ring_w * 2, ph + ring_w * 2),
                             ring_w, border_radius=12)
        flash_alpha = int(80 * (0.5 + 0.5 * math.sin(tick * 0.25)))
        flash_surf  = pygame.Surface((W, 6), pygame.SRCALPHA)
        flash_surf.fill((255, 200, 0, flash_alpha))
        surface.blit(flash_surf, (0, 0))
        surface.blit(flash_surf, (0, H - 6))
        title = font_md.render("  BOSS DROP  ", True, (255, 215, 0))
        surface.blit(title, title.get_rect(center=(W // 2, py + 28)))
        item  = font_xl.render(text, True, (255, 240, 150))
        surface.blit(item,  item.get_rect(center=(W // 2, py + 70)))
        sub   = font_sm.render("Added to forge cores", True, (180, 160, 100))
        surface.blit(sub,   sub.get_rect(center=(W // 2, py + 105)))
    else:
        title = font_md.render("LOOT", True, (180, 220, 255))
        surface.blit(title, title.get_rect(center=(W // 2, py + 22)))
        item  = font_md.render(text, True, (230, 230, 255))
        surface.blit(item,  item.get_rect(center=(W // 2, py + 55)))
        sub   = font_sm.render("Added to inventory", True, (140, 140, 180))
        surface.blit(sub,   sub.get_rect(center=(W // 2, py + 80)))


# =========================
# MODULE-LEVEL SINGLETON
# =========================

_ui_instance = None


def init_ui(player):
    global _ui_instance
    _ui_instance = GameUI(player)
    _ui_instance.start()
    return _ui_instance


def get_ui():
    return _ui_instance
