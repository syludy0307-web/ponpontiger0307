# -*- coding: utf-8 -*-
"""Scene timeline for the JAL123 documentary (1072.09 s).

Documentary grammar: slow deliberate camera, no glitch stingers, no ghost
overlays.  Fog/flicker only where the scene is a night exterior.
"""


def S(id, t0, t1, art, z0=1.0, z1=1.07, cx0=.5, cy0=.5, cx1=.5, cy1=.5,
      wob=.35, kind="kb", fog=0.0, flick=0.04, fin=0.0, fout=0.0, mono=False,
      jolt=None):
    fx = dict(fog=fog, flick=flick)
    if fin:
        fx["fade_in"] = fin
    if fout:
        fx["fade_out"] = fout
    if mono:
        fx["mono"] = True
    if jolt:
        fx["jolt"] = jolt
    return dict(id=id, t0=t0, t1=t1, art=art,
                motion=dict(kind=kind, z0=z0, z1=z1, cx0=cx0, cy0=cy0,
                            cx1=cx1, cy1=cy1, wob=wob),
                fx=fx)


SCENES = [
    # ---------------- 1. 事故の発生 ----------------
    S("j01", 0.00, 4.44, "title_open", 1.10, 1.02, fin=1.0, wob=.5, fog=.10),
    S("j02", 4.44, 9.36, "photo_ja8119_air", 1.00, 1.10, cy0=.55, cy1=.45, fog=.14),
    S("j03", 9.36, 15.22, "photo_ja8119_ramp", 1.02, 1.10, cx0=.56, cy0=.52, cx1=.46, cy1=.44),
    S("j04", 15.22, 19.02, "manifest_grid", 1.00, 1.06),
    S("j05", 19.02, 23.98, "cabin_seats", 1.02, 1.10, cy0=.52, cy1=.47, fog=.08),
    S("j06", 23.98, 30.58, "cruise_alt", 1.00, 1.07, cx0=.44, cx1=.56),
    S("j07", 30.58, 34.55, "bang_abstract", 1.14, 1.02, wob=1.3, jolt=[0.15]),
    S("j08", 34.55, 37.39, "oxygen_masks", 1.00, 1.09, cy0=.42, cy1=.52, wob=.7),
    S("j09", 37.39, 42.19, "tail_loss", 1.02, 1.11, cx0=.56, cx1=.40, wob=.5),
    S("j10", 42.19, 48.39, "hydraulic_diagram", 1.00, 1.09, cx0=.44, cx1=.56),

    # ---------------- 2. 32分間 ----------------
    S("j11", 48.39, 53.99, "cockpit_panel", 1.02, 1.10, cy0=.45, cy1=.55, flick=.12),
    S("j12", 53.99, 60.03, "yoke_unresponsive", 1.00, 1.08, cx0=.45, cx1=.55, wob=.6),
    S("j13", 60.03, 65.08, "dutch_roll", 1.04, 1.00, wob=.5),
    S("j14", 65.08, 70.27, "phugoid_chart", 1.00, 1.07, cx0=.42, cx1=.58),
    S("j15", 70.27, 75.43, "hydraulic_diagram", 1.09, 1.02, cx0=.36, cy0=.46),
    S("j16", 75.43, 83.51, "thrust_control", 1.00, 1.08, cx0=.46, cx1=.56),
    S("j17", 83.51, 88.83, "gear_flaps", 1.00, 1.09, cy0=.55, cy1=.46, wob=.5),
    S("j18", 88.83, 97.03, "clock_32min", 1.06, 1.00, wob=.3),
    S("j19", 97.03, 107.07, "phugoid_chart", 1.06, 1.01, cx0=.56, cx1=.46),
    S("j20", 107.07, 117.11, "photo_flightpath", 1.08, 1.16, cx0=.48, cy0=.44,
      cx1=.38, cy1=.38, wob=.4),
    S("j21", 117.11, 126.00, "descent_gauge", 1.00, 1.10, cx0=.36, cx1=.44, wob=.6),
    S("j22", 126.00, 138.38, "descent_gauge", 1.10, 1.18, cx0=.32, cy0=.5,
      cx1=.34, cy1=.5, wob=.8),
    S("j23", 138.38, 152.10, "ridge_night", 1.00, 1.09, cy0=.44, cy1=.52,
      fog=.32, flick=.06, fout=0.6),

    # ---------------- 3. 犠牲 ----------------
    S("j24", 152.10, 158.42, "casualty_board", 1.00, 1.05, fin=0.5),
    S("j25", 158.42, 163.00, "survivors_card", 1.06, 1.00),
    S("j26", 163.00, 166.13, "worst_ranking", 1.00, 1.06),

    # ---------------- 4. 原因調査 ----------------
    S("j27", 166.13, 170.81, "card_why", 1.08, 1.02, fin=0.4),
    S("j28", 170.81, 179.77, "report_1987", 1.00, 1.07, cy0=.42, cy1=.54),
    S("j29", 179.77, 188.25, "photo_tailstrike", 1.02, 1.11, cx0=.44, cx1=.26,
      cy0=.46, cy1=.62, wob=.5),
    S("j30", 188.25, 194.49, "bulkhead_location", 1.00, 1.09, cx0=.56, cx1=.42),
    S("j31", 194.49, 202.30, "bulkhead_intact", 1.00, 1.08),
    S("j32", 202.30, 211.82, "pressure_load", 1.02, 1.10, cx0=.42, cx1=.56),
    S("j33", 211.82, 217.14, "boeing_repair_scene", 1.00, 1.07),
    S("j34", 217.14, 224.07, "splice_correct", 1.00, 1.08, cy0=.46, cy1=.52),
    S("j35", 224.07, 232.79, "splice_actual", 1.00, 1.09, cx0=.44, cx1=.56),
    S("j36", 232.79, 238.79, "splice_compare", 1.06, 1.00, wob=.3),
    S("j37", 238.79, 246.90, "strength_gauge", 1.00, 1.07, cx0=.44, cx1=.56),

    # ---------------- 5. 7年間 ----------------
    S("j38", 246.90, 253.90, "photo_ja8119_itami", 1.00, 1.07, cy0=.44, cy1=.56),
    S("j39", 253.90, 261.50, "pressure_load", 1.09, 1.01, cx0=.58, cx1=.46),
    S("j40", 261.50, 269.10, "crack_growth", 1.00, 1.10, cx0=.30, cx1=.70, wob=.4),
    S("j41", 269.10, 279.30, "hidden_crack", 1.00, 1.08, cx0=.48, cx1=.56),
    S("j42", 279.30, 288.20, "bulkhead_cracked", 1.02, 1.11, cx0=.52, cy0=.46),

    # ---------------- 6. 破壊の瞬間 ----------------
    S("j43", 288.20, 297.20, "bulkhead_burst", 1.14, 1.02, wob=1.0, jolt=[0.2]),
    S("j44", 297.20, 307.20, "air_blast", 1.00, 1.10, cx0=.56, cx1=.40, wob=.5),
    S("j45", 307.20, 313.00, "hydraulic_diagram", 1.02, 1.12, cx0=.56, cx1=.34,
      cy0=.48, cy1=.48),
    S("j46", 313.00, 322.00, "chain_diagram", 1.00, 1.06, cx0=.30, cx1=.70, wob=.3),
    S("j47", 322.00, 330.60, "evidence_bulkhead", 1.00, 1.08, cy0=.44, cy1=.54),
    S("j48", 330.60, 340.00, "ntsb_doc", 1.00, 1.07, cy0=.42, cy1=.54),
    S("j49", 340.00, 350.10, "chain_diagram", 1.06, 1.01, cx0=.70, cx1=.30),

    # ---------------- 7. 陰謀論 ----------------
    S("j50", 350.10, 358.20, "card_conspiracy", 1.09, 1.02, fin=0.4),
    S("j51", 358.20, 366.00, "claim_missile", 1.00, 1.07),
    S("j52", 366.00, 371.30, "claim_drone", 1.00, 1.07),
    S("j53", 371.30, 377.90, "claim_f4", 1.00, 1.07),
    S("j54", 377.90, 385.20, "claim_coverup", 1.00, 1.07),
    S("j55", 385.20, 394.80, "news_chaos", 1.02, 1.10, cx0=.44, cx1=.56, wob=.5),
    S("j56", 394.80, 404.60, "location_confusion", 1.00, 1.08, cx0=.42, cx1=.58),
    S("j57", 404.60, 415.60, "night_search", 1.00, 1.09, cy0=.42, cy1=.54,
      fog=.28, flick=.10),
    S("j58", 415.60, 424.20, "night_search", 1.09, 1.02, cx0=.60, cx1=.44,
      fog=.30, flick=.08),
    S("j59", 424.20, 434.30, "photo_osutaka_mt", 1.00, 1.08, cy0=.46, cy1=.54, fog=.24),
    S("j60", 434.30, 447.00, "survivors_card", 1.00, 1.07, wob=.3),
    S("j61", 447.00, 458.00, "photo_ridge_stairs", 1.02, 1.09, cy0=.52, cy1=.44, fog=.26),
    S("j62", 458.00, 470.00, "us_testimony", 1.00, 1.07, cy0=.44, cy1=.54),
    S("j63", 470.00, 480.00, "distrust_diagram", 1.00, 1.07, cx0=.40, cx1=.60),

    # ---------------- 8. 断片の列挙 ----------------
    S("j64", 480.00, 490.00, "orange_object", 1.00, 1.09, cx0=.46, cx1=.60,
      cy0=.48, cy1=.42),
    S("j65", 490.00, 496.20, "abnormal_force_doc", 1.00, 1.08, cy0=.46, cy1=.54),
    S("j66", 496.20, 502.30, "fuel_fire", 1.02, 1.10, cy0=.52, cy1=.46, fog=.30),
    S("j67", 502.30, 511.00, "gap_diagram", 1.00, 1.06, cx0=.30, cx1=.70),
    S("j68", 511.00, 522.00, "card_verify", 1.08, 1.02, fin=0.4),

    # ---------------- 9. ミサイル説の検証 ----------------
    S("j69", 522.00, 530.10, "claim_missile", 1.06, 1.00),
    S("j70", 530.10, 542.10, "evidence_bulkhead", 1.00, 1.09, cx0=.44, cx1=.56),
    S("j71", 542.10, 550.78, "crack_growth", 1.08, 1.00, cx0=.62, cx1=.38),
    S("j72", 550.78, 570.90, "splice_actual", 1.00, 1.08, cy0=.46, cy1=.54),
    S("j73", 570.90, 585.00, "fdr_device", 1.00, 1.08, cx0=.44, cx1=.56),
    S("j74", 585.00, 598.40, "fdr_bits", 1.00, 1.10, cx0=.40, cy0=.40,
      cx1=.56, cy1=.60),
    S("j75", 598.40, 609.70, "fdr_bits", 1.10, 1.02, cx0=.50, cy0=.74,
      cx1=.50, cy1=.72),
    S("j76", 609.70, 625.40, "fdr_trace", 1.00, 1.09, cx0=.40, cx1=.58),
    S("j77", 625.40, 636.90, "reaction_physics", 1.00, 1.08, cx0=.44, cx1=.58),
    S("j78", 636.90, 644.54, "chain_diagram", 1.02, 1.09, cx0=.44, cx1=.60),
    S("j79", 644.54, 659.20, "fdr_trace", 1.09, 1.01, cx0=.58, cx1=.42),

    # ---------------- 10. 各説の検証 ----------------
    S("j80", 659.20, 669.10, "orange_object", 1.08, 1.00, cx0=.60, cx1=.48),
    S("j81", 669.10, 682.50, "abnormal_force_doc", 1.08, 1.00, cy0=.54, cy1=.46),
    S("j82", 682.50, 692.75, "abnormal_force_doc", 1.00, 1.07, cx0=.44, cx1=.56),
    S("j83", 692.75, 702.66, "diet_2025", 1.00, 1.08, cy0=.52, cy1=.44),
    S("j84", 702.66, 714.30, "diet_2025", 1.08, 1.01, cx0=.56, cx1=.46),
    S("j85", 714.30, 728.90, "evidence_convergence", 1.00, 1.07, cx0=.42, cx1=.58),
    S("j86", 728.90, 742.30, "evidence_convergence", 1.07, 1.12, cx0=.66, cy0=.50,
      cx1=.70, cy1=.50),

    # ---------------- 11. 救助の遅れ ----------------
    S("j87", 742.30, 754.30, "rescue_critique", 1.00, 1.07, cy0=.42, cy1=.58),
    S("j88", 754.30, 767.20, "rescue_critique", 1.07, 1.01, cy0=.58, cy1=.44),
    S("j89", 767.20, 781.00, "gap_diagram", 1.00, 1.08, cx0=.28, cx1=.72, wob=.4),
    S("j90", 781.00, 805.80, "gap_diagram", 1.08, 1.02, cx0=.72, cx1=.50),
    S("j91", 805.80, 827.00, "fuel_fire", 1.00, 1.09, cx0=.44, cx1=.56, fog=.30),

    # ---------------- 12. 結論 ----------------
    S("j92", 827.00, 838.50, "card_conclusion", 1.08, 1.02, fin=0.4),
    S("j93", 838.50, 858.60, "chain_diagram", 1.00, 1.06, cx0=.24, cx1=.76, wob=.3),
    S("j94", 858.60, 872.00, "splice_compare", 1.00, 1.07, cy0=.44, cy1=.56),
    S("j95", 872.00, 882.90, "distrust_diagram", 1.00, 1.07, cx0=.38, cx1=.62),
    S("j96", 882.90, 890.10, "photo_ridge_trail", 1.06, 1.00, fog=.28),

    # ---------------- 13. 残された謎 ----------------
    S("j97", 890.10, 899.30, "card_hole", 1.09, 1.02, fin=0.4),
    S("j98", 899.30, 908.60, "splice_actual", 1.00, 1.10, cx0=.50, cy0=.50,
      cx1=.50, cy1=.50, wob=.5),
    S("j99", 908.60, 919.74, "splice_compare", 1.08, 1.01, cy0=.72, cy1=.70),
    S("j100", 919.74, 930.70, "report_1987", 1.00, 1.07, cy0=.46, cy1=.54),
    S("j101", 930.70, 943.03, "boeing_doc", 1.00, 1.08, cy0=.42, cy1=.56),
    S("j102", 943.03, 956.63, "deleted_doc", 1.10, 1.02, wob=.5),
    S("j103", 956.63, 966.62, "boeing_doc", 1.06, 1.00, cx0=.56, cx1=.44),
    S("j104", 966.62, 981.20, "faa_doc", 1.00, 1.08, cy0=.44, cy1=.56),
    S("j105", 981.20, 995.00, "deleted_doc", 1.00, 1.08, cx0=.44, cx1=.56),
    S("j106", 995.00, 1006.20, "doc_timeline", 1.00, 1.07, cx0=.30, cx1=.70, wob=.3),
    S("j107", 1006.20, 1018.30, "doc_timeline", 1.07, 1.12, cx0=.80, cx1=.86),

    # ---------------- 14. 結び ----------------
    S("j108", 1018.30, 1032.00, "chain_diagram", 1.06, 1.00, cx0=.62, cx1=.38),
    S("j109", 1032.00, 1046.00, "photo_cenotaph", 1.00, 1.07, cy0=.52, cy1=.44, fog=.28),
    S("j110", 1046.00, 1060.00, "final_page", 1.00, 1.07, cy0=.46, cy1=.54),
    S("j111", 1060.00, 1072.09, "title_open", 1.02, 1.10, cy0=.50, cy1=.44,
      fog=.14, fout=2.4),
]


def scene_check():
    prev = 0.0
    for s in SCENES:
        assert abs(s["t0"] - prev) < 1e-6, f"gap at {s['id']}: {prev} -> {s['t0']}"
        assert s["t1"] > s["t0"], s["id"]
        prev = s["t1"]
    return prev


if __name__ == "__main__":
    print(f"{len(SCENES)} scenes, contiguous 0 → {scene_check():.2f}s")
    arts = sorted({s['art'] for s in SCENES})
    print(f"{len(arts)} distinct arts")
