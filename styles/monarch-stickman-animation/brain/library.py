"""MONARCH EDITOR BRAIN — idea libraries (the editor's long-term memory of *options*).

Every item: id · name · how (how it is built on THIS engine: v9 grid, SHADE rig, hybrid look,
cinematic layer, 19 gates) · tags (controlled vocabulary, used for coherence scoring).

Identity constants are NOT in here (palette, type, hero, grid, gates never change).
What varies per video = the eight Concept-DNA slots + one Signature Move + the transition set
+ the SFX palette.  `concept.py` samples from these lists, excludes what the registry says was
used recently, scores the combination and prints a brief.

Tag vocabulary (keep it small so coherence means something):
  mood   : dark warm tense calm fast slow playful epic
  theme  : social inner physical mind money status time fear
  energy : hi mid lo
"""

HOOK_ARCHETYPES = [
 ("cold_question",      "Cold question",            "Word one is the question, hero already mid-gesture; hot word lands on the question mark.", ["mid","mind","social"]),
 ("social_sting",       "Social sting / scene contradiction", "A room that ignores the hero; the camera finds him last. The sting is the silence before the question.", ["dark","tense","social","status"]),
 ("mid_action",         "Mid-action (in medias res)", "Frame 1 is already a fall, a sprint, a shatter; VO explains after 0.8 s.", ["fast","hi","physical"]),
 ("countdown",          "Countdown / timer",         "A 3-D numeral counts down in the dark while the hero does the thing; the promise is 'before zero'.", ["tense","fast","time","hi"]),
 ("wrong_answer_first", "The wrong answer first",    "'Sab kehte hain X.' — a stamp GALAT slams over the crowd's answer, then the real one.", ["playful","mind","mid"]),
 ("mirror_accusation",  "Mirror accusation",         "The hero turns to the lens: 'tum bhi yahi karte ho' — eyes ignite, the rest of the frame dims.", ["dark","tense","inner","social"]),
 ("forbidden_secret",   "Forbidden / secret framing", "'Jo koi nahi batata' — a locked box / a torn page; the wedge opens like a lid.", ["dark","calm","mind","lo"]),
 ("number_shock",       "Number shock",              "One giant extruded numeral turns in the dark (90 %, 3650, 0); the hero is small beside it.", ["epic","mind","numbers","mid"]),
 ("before_after_split", "Before / after split frame", "Two heroes on the seam: slumped left, risen right; the seam slides to erase one.", ["warm","status","mid"]),
 ("silent_slam",        "Silent slam",               "0.9 s of bed-only stillness, then one impact + one word; the only quiet hook allowed.", ["dark","tense","hi"]),
 ("object_mystery",     "Object mystery (ECU)",      "Extreme close-up of a prop (a cracked plate, a key) — the pull-back reveals the scene.", ["calm","slow","mind","lo"]),
 ("reverse_reveal",     "Reverse reveal",            "Open on the last frame (the room turned), 'yahan tak kaise?' — then rewind glitch to the start.", ["epic","story","mid"]),
 ("dare_pov",           "Dare / POV challenge",      "'Agar tum yeh teen cheezein kar sako…' — three slots appear empty, to be filled by the chapters.", ["playful","fast","physical","hi"]),
 ("confession",         "Confession",                "'Main paanch saal yeh galat karta raha' — hero sits, light from one side, caption in lower case.", ["warm","calm","inner","lo"]),
 ("villain_named",      "The villain named",         "The habit personified: a second silhouette (the Shadow) steps out of the hero's own shadow.", ["dark","tense","inner","mid"]),
 ("pattern_break",      "Pattern break",             "Two black frames + one word in paper type, then the light arrives (tint-not-flood still holds).", ["dark","fast","hi"]),
 ("prediction",         "Prediction",                "'Agle tees second mein tumhara X badlega' — a progress ring starts and really completes at the CTA.", ["playful","time","mid"]),
 ("list_twist",         "List bait with a twist",    "'Chaar nahi — sirf ek aadat' — four cards fly in, three burn, one stays.", ["playful","fast","list","mid"]),
 ("micro_story",        "Micro-story in one line",   "'Kal raat do baje…' — a clock, one lamp, the hero at a desk; the story starts, not the lesson.", ["warm","slow","story","lo"]),
 ("question_returned",  "The question returned",     "'Tumse aakhri baar kab kisi ne izzat se baat ki?' — the hero waits one breath for the answer.", ["dark","calm","social","inner"]),

 # ── added turn 13 from the reference study (Day One Films · DISCIPLINE) ──
 ("literary_line_black", "Literary first line on black", "One past-tense sentence on black, no hero yet ('Har din aise hi shuru hota tha.'); the first picture arrives on the full stop. Ref: DISCIPLINE 0:00–0:03.", ["dark","calm","slow","inner","lo","ref_dayone"]),
 ("loop_shown",          "The loop shown (counter jumps)", "Same room, same pose, the HUD counter jumps DAY 1 → 45 → 88 → 365 while nothing else changes — the problem is repetition, shown not told.", ["dark","time","inner","mid","ref_dayone"]),
]

NARRATIVE_DEVICES = [
 # id, name, how, tags, (min_s, max_s), chapter template
 ("list_n",        "List of N habits/rules",     "HOOK → N numbered chapters → CTA; a numeral card per chapter.", ["list","mid"], (25, 60),  "hook,items,cta"),
 ("mini_story",    "Mini-story",                 "SETUP → VILLAIN → TURN → RULES → PAYOFF (+CTA); the same room opens and closes it.", ["story","mid"], (55, 120), "setup,villain,turn,rules,payoff,cta"),
 ("day_in_life",   "One day, one timeline",      "A clock drives the chapters (05:00 … 23:00); the hero ages one shade of light per hour.", ["time","calm"], (40, 90),  "dawn,morning,noon,evening,night,cta"),
 ("trial",         "The trial",                  "The viewer's habit is on trial: charge, evidence (chapters), verdict, sentence (the fix).", ["tense","social"], (45, 100), "charge,evidence,verdict,sentence,cta"),
 ("ladder",        "The ladder / levels",        "Level 1…5 stacked in depth; the camera climbs; each level is a harder rule.", ["epic","status"], (35, 80),  "level1,level2,level3,level4,level5,cta"),
 ("two_doors",     "Two doors",                  "Every chapter is a choice: door A (easy, grey) vs door B (hard, lit); the hero walks B.", ["tense","inner"], (35, 75),  "choice1,choice2,choice3,choice4,cta"),
 ("myth_truth",    "Myth vs truth",              "Three myths stamped GALAT, each replaced by its truth; split frame per chapter.", ["playful","mind"], (30, 70),  "myth1,myth2,myth3,truth,cta"),
 ("letter",        "Letter to the younger self", "Handwritten lines appear as the VO speaks; the hero at two ages on the seam.", ["warm","inner"], (40, 90),  "then,lesson1,lesson2,lesson3,now,cta"),
 ("countdown_dev", "Countdown",                  "60 → 0: the chapters are time slices; the last second is the payoff.", ["fast","time"], (30, 60),  "t60,t40,t20,t5,zero,cta"),
 ("recipe",        "The recipe",                 "Ingredients (traits) → method (steps) → the plate (result); props assemble on a table.", ["warm","playful"], (30, 60),  "ingredients,step1,step2,step3,plate,cta"),
 ("journey_map",   "The map / journey",          "A drawn map; the hero walks node to node; each node a chapter; the route is the lesson.", ["epic","calm"], (45, 100), "start,node1,node2,node3,arrival,cta"),
 ("machine",       "The machine",                "Inputs → gears (habits) → output; one gear jams per chapter until it turns.", ["playful","mind"], (35, 70),  "input,gear1,gear2,gear3,output,cta"),
 ("autopsy",       "The autopsy",                "What went wrong, cause by cause, on a blueprint of the failed day.", ["dark","mind"], (40, 90),  "body,cause1,cause2,cause3,fix,cta"),
 ("duel",          "Hero vs Shadow",             "The hero's shadow detaches and argues; each chapter the hero wins one exchange.", ["dark","tense","inner"], (45, 100), "shadow,round1,round2,round3,win,cta"),
 ("heist",         "The heist",                  "Plan (chapters) → execution (payoff): the thing stolen back is the viewer's time/respect.", ["fast","epic"], (45, 90),  "target,plan1,plan2,plan3,execute,cta"),
 ("loop_replay",   "The loop replay",            "One 6-s scene replayed 3–4 times, each time with one habit changed; the last replay works.", ["playful","story"], (35, 70),  "take1,take2,take3,take4,cta"),

 # ── added turn 13 from the reference study (Day One Films · DISCIPLINE) ──
 ("counter_spine",     "Counter spine (DAY n HUD)",          "A small counter in the corner is the clock of the film: a false Day 1, a year of nothing, a true Day 1, then the grind counted upward; the counter is the only narration the montage needs.", ["time","inner","mid","dark"], (45, 300), "loop,false_day1,bottom,true_day1,grind,fight,summit,title"),
 ("silent_film_text",  "Silent film + text narration",       "No continuous VO: ≈ 20 on-screen lines in two colours carry the script; the voice is kept for one leitmotif line that returns changed; music and SFX do the rest.", ["calm","dark","inner","lo"], (60, 300), "open,problem,bottom,turn,grind,fight,payoff,title"),
 ("shadow_antagonist", "The shadow double as antagonist",    "The habit/voice gets a body: a dark double that whispers in text, lives in the mirror, blocks the path — and is left small in the room at the end.", ["dark","tense","inner","mid"], (40, 300), "whisper,mirror,bottom,turn,grind,blocker,left_behind"),
 ("callback_ladder",   "Callback ladder",                    "Three or four motifs planted early (alarm, mirror, room, villain) each return once, changed; the ending is the first scene replayed with the change.", ["inner","time","mid"], (40, 300), "plant1,plant2,plant3,turn,return1,return2,return3,end"),
]

VISUAL_WORLDS = [
 ("ignored_room",   "The ignored room",          "Six grey silhouettes in DoF, none turn; the room turns at the payoff.", ["dark","social","status"]),
 ("gym_desk",       "Dumbbell, book stack, desk", "The POWER props: ring timer, rep counter, page stack.", ["warm","physical","mind"]),
 ("chessboard",     "The chessboard",            "People as pieces; the hero is a pawn that walks to the last rank; pieces fall in slow-mo.", ["dark","tense","status"]),
 ("dark_staircase", "The staircase in the dark", "Steps light up under the hero's feet; the top is paper-white; falls are real.", ["dark","epic","status"]),
 ("mirror_hall",    "The mirror hall",           "Five reflections, each a version of the hero; one by one they crack until the true one.", ["dark","inner"]),
 ("glass_box",      "The glass box",             "The hero inside a lit box the crowd walks past; the box cracks from inside.", ["tense","social","fear"]),
 ("tug_of_war",     "The rope",                  "A rope between hero and crowd/time/phone; tension is literal; he lets go or pulls.", ["tense","physical"]),
 ("door_corridor",  "The corridor of doors",     "Doors in perspective; most open onto grey; one onto light; 3-D door swings (doors kind).", ["calm","inner","time"]),
 ("pressure_gauge", "The gauge",                 "A big needle meter (anger, stress, trust); the needle is a character.", ["tense","inner","hi"]),
 ("compass",        "The compass",               "A compass needle swings with each bad advice and settles on the rule.", ["calm","mind","lo"]),
 ("tree_roots",     "Tree and roots",            "Roots = habits drawn in ink underground; the canopy grows in the dark half.", ["warm","calm","inner"]),
 ("puppet_strings", "Puppet strings",            "Strings from above (likes, opinions) pull the limbs; the hero cuts them one by one.", ["dark","social","inner"]),
 ("maze_topdown",   "The maze (top-down)",       "God view; the hero a dot; walls rearrange; the exit is where he stops following.", ["mind","calm"]),
 ("hourglass",      "The hourglass",             "Sand = days; the hero stands in the lower bulb; he climbs the stream at the turn.", ["time","epic"]),
 ("iceberg",        "The iceberg",               "Visible 10 % (results) vs underwater 90 % (work); the camera dives.", ["calm","mind","epic"]),
 ("elevator",       "The elevator floors",       "A floor indicator climbs; each floor a chapter; the doors open on a different room.", ["playful","status"]),
 ("arena_ring",     "The arena / ring",          "A boxing ring in a dark hall; the opponent is a habit; bell = chapter.", ["tense","physical","hi"]),
 ("courtroom",      "The courtroom",             "Bench, dock, evidence table; a gavel for every verdict; the hero in the dock then on the bench.", ["tense","social"]),
 ("lighthouse",     "The lighthouse",            "A beam sweeps the dark; what it lights is the chapter; the hero becomes the lamp.", ["calm","epic","inner"]),
 ("magnet",         "The magnet",                "Iron filings (people/money) align to the hero only when he turns; field lines in ink.", ["playful","money","social"]),
 ("domino",         "The domino line",           "Chapters as dominoes; one habit tips the rest; the camera follows the wave.", ["fast","playful","mind"]),
 ("conductor",      "The conductor",             "Hands lead an invisible orchestra of silhouettes; chaos until the baton rises.", ["epic","social","status"]),
 ("mountain_rope",  "The mountain and the rope", "A climb; anchors are rules; a fall caught by the last rule.", ["epic","physical"]),
 ("city_windows",   "The city at night",         "A wall of dark windows; one lights per chapter; the hero at the lit one.", ["dark","calm","money"]),
 ("train_platform", "The train platform",        "Trains = chances; the crowd boards; the hero waits for the right one.", ["calm","time","story"]),
 ("anvil",          "Anvil and hammer",          "Each rule is a strike; sparks are the particle layer; the blade is the result.", ["physical","epic","hi"]),
 ("river_dam",      "The river and the dam",     "Attention/money as water; the dam is discipline; the turbine lights the city.", ["calm","money","mind"]),
 ("xray_blueprint", "X-ray / blueprint",         "The hero as a blueprint; chapters annotate parts (spine, eyes, hands) with dimension lines.", ["mind","calm","lo"]),
 ("scale_plate",    "Scale and the broken plate", "IZZAT props: the balance, the shattered plate, the NA stamp.", ["dark","social","status"]),
 ("desert_well",    "The desert and the well",   "Heat haze, one well; the crowd digs everywhere, the hero digs deep in one spot.", ["warm","epic","mind"]),

 # ── added turn 13 from the reference study (Day One Films · DISCIPLINE) ──
 ("mirror_wrong_reflection", "The mirror with the wrong reflection", "A standing mirror; the reflection is the Shadow and the glass cracks under the insult; later the same mirror shows the hero himself.", ["dark","tense","inner","ref_dayone"]),
 ("insult_bag",              "The punching bag of insults",          "Each insult hangs as red text over the bag; a punch shatters it into letters with speed lines and a 1-frame flash; one cut per insult.", ["fast","hi","physical","inner","ref_dayone"]),
 ("stair_mountain_blocker",  "The staircase-mountain and the blocker", "A black staircase cut into a mountain; the Shadow grows across the top step with 'you can't.'; the hero sprints through it into white.", ["epic","tense","physical","ref_dayone"]),
 ("summit_first_light",      "The summit at first light",            "The first warm, bright frame of the film is the ridge at sunrise; two lines of payoff text, then back to the room at dawn.", ["warm","calm","epic","ref_dayone"]),
 ("calendar_of_x",           "The calendar of X",                    "A wall calendar fills with red X marks as the counter climbs; the one cutaway that proves time.", ["time","mid","ref_dayone"]),
 ("awake_before_alarm",      "Awake before the alarm",               "ECU 4:59 → 5:00; the hero's eyes are already open; the hand comes down from the top of frame and stops it — the inverse of the snooze.", ["tense","time","inner","ref_dayone"]),
]

EDITING_GRAMMARS = [
 ("voice_led_inserts", "Voice-led inserts",          "Picture cuts every 2–3 s to inserts inside long chapters (IZZAT v2: 33 shots/75 s).", ["mid"]),
 ("long_take_internal","Long takes, internal motion","One scene per chapter; the motion is inside (rig, seam, props), few cuts (SHADE v2).", ["calm","lo"]),
 ("match_cut_chain",   "Match-cut chain",            "Each cut matches a shape/motion: ring → clock → coin → eye.", ["playful","mid"]),
 ("split_screen",      "Split-screen comparisons",   "Two states side by side on the seam; the seam is the divider.", ["mind","mid"]),
 ("jump_cut_staccato", "Jump-cut staccato",          "Same framing, 6–8 jump cuts on the beat for a list inside a line.", ["fast","hi"]),
 ("freeze_annotate",   "Freeze-frame annotations",   "Hard freeze, dimension lines + labels draw on, then release with a whip.", ["mind","playful"]),
 ("rewind_replay",     "Rewind / replay",            "Scrub-back glitch to replay a moment with the fix applied.", ["playful","story"]),
 ("speed_ramps",       "Speed ramps",                "Slow-mo into impact, snap to 1.0× on the word; ramps measured against the jerk gates.", ["epic","hi"]),
 ("oner",              "The oner",                   "One continuous camera move through sets (sets slide in/out below the frame).", ["epic","calm"]),
 ("whip_montage",      "Whip-pan montage",           "Chapters joined only by whips; the montage breathes with the VO.", ["fast","hi"]),
 ("dolly_zoom",        "Dolly-zoom moments",         "Background scale breathes against a locked hero at the turn of each chapter.", ["tense","epic"]),
 ("pip_inserts",       "Picture-in-picture inserts", "A paper card with an insert slides over the dark half; the card is a shot.", ["playful","mid"]),
 ("silhouette_cards",  "Silhouette chapter cards",   "Each chapter opens on the hero's silhouette cut-out that fills with the scene.", ["dark","calm"]),
 ("loop_reprise",      "Loop reprise",               "The first shot returns at the end, changed; the edit is a circle.", ["story","calm"]),

 # ── added turn 13 from the reference study (Day One Films · DISCIPLINE) ──
 ("holds_dip_burst",     "Holds + dips-to-black + burst montage", "Bimodal cadence: 7–14 s holds carried by a text line / a light / a music change, scene changes by a 0.25 s dip-to-black, then bursts of 1-beat cuts (1.27 s at 94 BPM) or 0.3 s impact cuts. Measured in the reference: 44 shots / 158 s, 13 dips, 58 % still frames.", ["slow","dark","lo","ref_dayone"]),
 ("beat_locked_montage", "Beat-locked counter montage",          "Every cut exactly on beat 1 of a bar; the HUD counter jumps with the cut; same framing, different day.", ["fast","time","mid","ref_dayone"]),
]

CAMERA_LANGUAGES = [
 ("static_internal", "Static frame, internal motion", "v9/POWER: the camera never moves; everything inside does.", ["calm","lo"]),
 ("push_parallax",   "Push-in + parallax + slow-mo",  "IZZAT cinematic layer: measured push, 3 depth planes, ramps.", ["epic","mid"]),
 ("handheld_micro",  "Handheld micro-shake",          "±2 px Perlin drift + hit-shake on impacts (measured against jerk).", ["tense","hi"]),
 ("crane_reveal",    "Crane / boom reveal",           "Vertical reveal: from the floor to the hero's eyes, or over a crowd.", ["epic","mid"]),
 ("orbit",           "Orbit around the hero",         "The rig turns 90–180° while the set parallaxes; one per chapter at most.", ["epic","hi"]),
 ("top_down",        "Top-down god view",             "Maps, mazes, tables; the hero a small figure; cuts to eye level for the beat.", ["mind","calm"]),
 ("low_angle",       "Low-angle hero",                "Camera at the floor, the hero towering; for turns and payoffs.", ["epic","status"]),
 ("dutch_tilt",      "Dutch tilt tension",            "4–7° roll that levels at the fix; roll measured in the luma trace.", ["tense","dark"]),
 ("rack_focus",      "Rack-focus depth",              "Blur shifts between hero and prop to steer the eye; one per shot max.", ["calm","mind"]),
 ("pov",             "POV",                           "Through the hero's eyes (hands in frame); the crowd looks at the lens.", ["social","tense"]),

 # ── added turn 13 from the reference study (Day One Films · DISCIPLINE) ──
 ("locked_stage_two_ecus", "Locked stage, two close-ups only", "Side-view stage framing for the whole film, ground at 78 % of frame height; exactly two ECUs (the clock, the face) so they land like punches.", ["calm","lo","ref_dayone"]),
]

TRANSITION_KINDS = {
 # existing library (respect2.TRANS) — all 15 were used in IZZAT v2
 "existing": ["cube_h","cube_v","zoom","whip_h","whip_v","iris","slices","ink","wedge","card","spin","sweep","blur","doors","shatter"],
 # families still to build — each new video must add >= 3 of these (or its own), luma-traced before any shard
 "to_build": [
        ("dip_black", "Dip to black 0.25 s — A fades to black on the beat, B fades up (ref DISCIPLINE: the only scene transition, 13×)"),
        ("white_flash_cut", "1-frame white flash cut on an impact — never on a dialogue cut"),
  ("page_curl",     "Page curl — the paper half peels to reveal B"),
  ("paper_tear",    "Paper tear — a ragged edge rips across (soft tear fringe >= 100 px)"),
  ("ink_bloom",     "Ink-drop bloom — radial ink spreads from the hot word"),
  ("shape_wipe",    "Shape wipe along a drawn prop (ring, spine, needle)"),
  ("glitch_rgb",    "Glitch / RGB split — 4–6 frames, tint-not-flood, luma-traced"),
  ("light_leak",    "Light-leak burn — the ray layer overexposes A into B"),
  ("object_morph",  "Match-cut object morph (ring → clock → eye)"),
  ("shadow_pass",   "Shadow pass — the hero's own shadow wipes the frame"),
  ("blinds",        "Venetian blinds — 7 slats rotate"),
  ("clock_wipe",    "Clock wipe from the chapter numeral"),
  ("shutter",       "Shutter — iris blades close/open (not the round iris)"),
  ("film_burn",     "Film burn — paper edge chars inward"),
  ("mirror_fold",   "Mirror fold — A folds on the seam like a card"),
  ("origami",       "Origami fold — three folds, B on the back faces"),
  ("punch_zoom_rot","Punch zoom + rotate 15°"),
  ("mosaic_flip",   "Mosaic tiles flip (24 tiles, staggered)"),
  ("ripple",        "Ripple — a stone dropped at the hot word"),
  ("smoke_pass",    "Smoke / fog pass across the dark half"),
  ("lens_whip",     "Lens whip with anamorphic flare"),
  ("kaleido",       "Kaleidoscope 3-way for a 'confusion' beat only"),
  ("pixel_sort",    "Pixel sort downward — a 'collapse' beat only"),
  ("door_light",    "Door of light — a vertical light slit widens"),
  ("ink_rain",      "Ink rain — drops reveal B where they land"),
  ("depth_pass",    "Depth pass — a foreground prop crosses the lens and B is behind it"),
 ],
}

SONIC_IDENTITIES = [
 ("dminor_pluck_100", "D-minor 100 BPM pluck bed",      "POWER: plucks, pads, 0.6 s grid (grid now banned).", ["warm","mid"]),
 ("cinematic_braam",  "Cinematic braam / swell / heartbeat", "IZZAT v2: braam once, reverse swells, glass, metal, heartbeat in one chapter.", ["dark","epic"]),
 ("tape_lofi",        "Warm tape lo-fi",                "Wow/flutter pad, vinyl-free (no noise floor), soft kick on chapter turns only.", ["warm","calm"]),
 ("strings_tension",  "Orchestral strings tension",     "Sustained strings that rise per chapter and release at the payoff.", ["tense","epic"]),
 ("industrial_metal", "Industrial metal percussion",    "Anvil hits, chains, hiss-free; cues only on visual impacts.", ["dark","hi","physical"]),
 ("glass_mallet",     "Glass / crystal mallet",         "Mallet tones per chapter numeral, shimmer on light events.", ["calm","mind"]),
 ("sub_breath",       "Sub pulse + breath",             "A 40 Hz pulse under the hero's heartbeat; breath sounds in the holes (bed_20_120 gate watched).", ["dark","tense"]),
 ("piano_room",       "Piano single notes + room",      "One note per rule; the room tail is the only reverb.", ["warm","inner"]),
 ("dhol_subtle",      "Subtle dhol / tabla",            "Regional pulse at 25 % under the turn chapters only; never a loop.", ["epic","playful"]),
 ("choir_pad",        "Choir pad",                      "Vowel pad that opens on the payoff; rest of the bed dry.", ["epic","calm"]),
 ("clock_motif",      "Clock-tick motif",               "Tick as the only rhythmic element; it stops at the turn (silence as a weapon).", ["tense","time"]),
 ("paper_foley",      "ASMR paper / pencil foley",      "Every prop appearance has a paper sound; the bed is almost only foley.", ["calm","playful"]),

 # ── added turn 13 from the reference study (Day One Films · DISCIPLINE) ──
 ("sub_drone_94",      "Sub-drone build at 94 BPM, quiet ending", "53 % of the energy under 120 Hz, no air above 8 kHz, pulse 94 BPM, −16.6 LUFS integrated; the loudest minute is the grind, the last 13 s fall to −30 dB RMS.", ["dark","epic","lo","ref_dayone"]),
 ("text_card_silence", "Text-card silence",                       "The bed drops to one held note under every white text card; SFX only on impacts; the room tone is the sub.", ["calm","slow","lo","ref_dayone"]),
]

TYPOGRAPHIC_TWISTS = [
 ("numeral_card_3d",  "3-D numeral card turning in the dark", "IZZAT v2 chapter cards.", ["epic"]),
 ("typewriter_ink",   "Typewriter + ink bleed",              "Letters land one per frame with an ink dot that spreads.", ["calm","mind"]),
 ("word_slam_shake",  "Word slam + hit shake",               "Hot word drops from above; 2-frame camera hit (jerk-gated).", ["hi","tense"]),
 ("text_as_object",   "Text as object",                      "The hero leans on / lifts / breaks the headline (3-D rig contact).", ["playful","physical"]),
 ("light_reveal",     "Text revealed by light",              "The ray layer sweeps and the headline appears only where lit.", ["dark","epic"]),
 ("text_shatter",     "Text cracks and shatters",            "The wrong word breaks (shatter kind) into the right one.", ["hi","playful"]),
 ("text_on_seam",     "Text on the seam",                    "Half paper, half charcoal letters split by the hybrid diagonal.", ["dark","mid"]),
 ("hand_underline",   "Hand-drawn underline / circle",       "Ink draws on under the hot word, slightly wobbly.", ["warm","calm"]),
 ("scale_burst",      "Scale burst keyword",                 "Hot word grows 4× in 4 frames with quintic ease, settles.", ["hi"]),
 ("tracking_whisper", "Tracking-out whisper",                "Letter spacing expands as the voice drops; for confessions.", ["calm","inner"]),
 ("mirror_text",      "Mirror text",                         "Reflected headline below the floor line; the reflection says the opposite.", ["dark","mind"]),
 ("depth_layers",     "Text in depth",                       "Three parallax layers of type; the hero walks between them.", ["epic","mid"]),
 ("counter_live",     "Live counter",                        "A number counts with the voice (3,650 pages) and stops exactly on the word.", ["mind","playful"]),
 ("stamp",            "Stamp",                               "GALAT / NA stamp with a 1-frame white tint flash (not flood).", ["hi","playful"]),

 # ── added turn 13 from the reference study (Day One Films · DISCIPLINE) ──
 ("colour_coded_voices", "Colour-coded voices",            "White small type top-centre = the truth/narrator; red hand type = the critic; both end with a full stop; no labels ever.", ["dark","inner","ref_dayone"]),
 ("hud_counter",         "HUD counter",                    "DAY n (or ₹ / reps / hours) small in the top-left corner on every shot; it is the clock and the plot.", ["time","mid","ref_dayone"]),
 ("insult_shattered",    "Insult text shattered by impact", "The critic's line hangs over the action; the hit breaks it into letters that fly with the speed lines.", ["fast","hi","physical","ref_dayone"]),
 ("full_stop_voice",     "The full stop",                  "Every on-screen line and every thumbnail word ends with a period: calm, final, no exclamation marks.", ["calm","ref_dayone"]),
]

ENDING_DEVICES = [
 ("recap_carousel_card", "Recap carousel + follow/save card", "IZZAT v2.", ["mid"]),
 ("callback_frame1",     "Callback to frame 1, changed",      "The opening shot returns with one difference (the room turns).", ["story","calm"]),
 ("question_back",       "Question returned to the viewer",  "The hero asks the lens; hold 1.0 s; card.", ["inner","calm"]),
 ("silent_word",         "Silent final frame + one word",    "Bed drops to the end bell only; one paper word.", ["dark","calm"]),
 ("open_loop",           "Open loop for the next video",     "'Lekin ek cheez baaki hai…' — a card with the next topic blank.", ["playful","mid"]),
 ("walk_into_light",     "Hero walks into the light",        "The wedge opens fully; the hero exits frame right into paper.", ["epic","warm"]),
 ("counter_completes",   "The counter completes",            "The ring/number that started in the hook reaches 100 % on the CTA.", ["playful","time"]),
 ("mirror_turn",         "The mirror turn",                  "The hero's reflection turns to the camera first.", ["dark","inner"]),
 ("signoff_ritual",      "Sign-off ritual",                  "A fixed gesture (hood up) + the two-action CTA; builds series identity.", ["warm","mid"]),
 ("freeze_hot_word",     "Freeze on the hot word",           "Hard freeze, hot word extrudes, cut to black on the bell.", ["hi"]),

 # ── added turn 13 from the reference study (Day One Films · DISCIPLINE) ──
 ("title_pun_command",  "Title drop + pun + two-word command", "The film's one-word title, a pun line under it ('Day one, or one day.'), then a two-word order in the critic's colour ('You decide.'); fade, no CTA.", ["calm","dark","ref_dayone"]),
 ("villain_left_small", "The villain left small in the room",  "The ending replays the first room at dawn; the hero walks out of frame; the Shadow stays, small, beside the clock.", ["dark","inner","ref_dayone"]),
]

PATTERN_INTERRUPTS = [
 ("tint_flash",     "1-frame tint flash (never a flood)"),
 ("silence_hole",   "Silence hole 0.4–0.9 s (gate: silence < 1.2 s)"),
 ("ecu",            "Extreme close-up (eyes, hands, prop)"),
 ("scale_jump",     "Scale jump 4× (insert, not a scaled scene layer)"),
 ("direction_flip", "Motion direction reversal"),
 ("slowmo_ramp",    "Slow-mo ramp into a hit"),
 ("speed_up",       "Speed-up burst (2×) on a list"),
 ("black_word",     "Two black frames + one word"),
 ("sound_dropout",  "Bed drop-out under one sentence"),
 ("stillness",      "0.4 s of near-stillness (drift only)"),
 ("split",          "Split frame"),
 ("text_slam",      "Text slam"),
 ("flare",          "Anamorphic flare pass"),
 ("hit_shake",      "Hit shake"),
 ("look_at_lens",   "Hero looks at the lens"),
 ("prop_breaks",    "A prop breaks"),

 # ── added turn 13 from the reference study ──
 ("dip_black_025",      "0.25 s dip-to-black between scenes (ref: 13 in 158 s)"),
 ("white_flash_impact", "1-frame white flash on a physical impact only (ref: 3 in the film, all on punches)"),
 ("counter_jump",       "the HUD counter jumps a large number in one cut (DAY 88 → 112 → 150)"),
]

SIGNATURE_MOVES = [
 ("paper_peel",       "The hero steps out of the paper into the dark — a 2.5-D peel, the paper half curls behind him."),
 ("ink_assemble",     "A prop assembles from ink particles that fly in from the dark half."),
 ("orbit_180",        "A 180° orbit around the rig in one shot while the set parallaxes."),
 ("room_rearranges",  "The room rearranges itself — furniture flies to a new layout between two words."),
 ("shadow_detaches",  "The hero's shadow detaches and acts on its own, then is pulled back under his feet."),
 ("numeral_crumbles", "The chapter numeral crumbles and its rubble becomes the next scene's floor."),
 ("time_slice",       "Time-slice: three hero poses in one frame with ghost trails, then they collapse into one."),
 ("line_rope",        "A drawn line becomes a rope the hero actually pulls (rig contact + tension)."),
 ("frame_tear",       "The frame itself tears and the next scene is behind it."),
 ("crowd_to_text",    "A crowd of silhouettes morphs into a wall of text."),
 ("rays_push_dark",   "Light rays physically push the dark half back, pixel by pixel."),
 ("mirror_world",     "Mirror world: the lower half of the frame is a reflection that disagrees."),
 ("multiply_collapse","The hero multiplies into a crowd of himself and collapses to one."),
 ("zoom_into_eye",    "Zoom into the eye → the next scene is inside it."),
 ("ink_rain_scene",   "Ink rain: drops reveal the scene where they land."),
 ("scale_weighs_words","A scale weighs two words; the heavier one drops through the floor."),
 ("domino_chapters",  "Chapters as dominoes knocked over by the hero's finger."),
 ("chess_people",     "People become chess pieces mid-walk."),
 ("hood_light",       "The hood fills with light from inside and projects the next scene on the wall."),
 ("paper_plane",      "A paper plane carries the camera from set to set."),
 ("spine_tower",      "The spine rises as a tower of blocks the camera climbs."),
 ("clock_melts",      "The clock melts into the floor and becomes the path."),
 ("seam_rotates",     "The hybrid seam rotates 90° in one shot and the scene re-gravitates."),
 ("hero_draws_set",   "The hero draws the next set with a pencil in real time."),

 # ── added turn 13 from the reference study ──
 ("alarm_slam_from_top",    "A hand enters from the top edge of frame and slams the alarm at 5:00 — the inverse of the snooze; the digits flare and die."),
 ("punch_through_shadow",   "The hero sprints up the last steps and punches through the giant shadow; the frame goes to white and the red letters of its last word shatter."),
 ("reflection_becomes_you", "The mirror that held the Shadow is revisited; this time the reflection is the hero — one beat late, then in sync."),
 ("walk_out_leave_shadow",  "The hero walks out of the frame he started in; the camera stays on the empty room and the small shadow by the clock."),
]

SFX_VOICES = {
 "used": ["braam","reverse_swell","glass_ting","metal_ring","paper_slide","doppler_whip","impact","heartbeat","glass_burst","click",
          "bell","glass","metal","pluck","glass_hi","low_chime","shimmer","metal_hi","end_bell","pad","swell"],
 "fresh": [
        "alarm_digital_5am", "snooze_slap", "mirror_crack", "bag_punch_thud", "letters_shatter_glass", "shadow_whisper_sub", "stairs_breath", "sunrise_pad_swell","anvil","chain","wood_knock","match_strike","breath","sub_drop","tape_stop","vinyl_scratch_free","piano_note","cello_pull",
           "choir_vowel","water_drop","stone_drop","paper_tear_sfx","pencil_scratch","zipper","coin_spin","gavel","door_creak","wind_gust",
           "bulb_hum_short","camera_shutter","heart_double","footstep_wood","sand_pour","ice_crack","rope_creak","bowed_metal","kalimba","dhol_hit"],
}

SLOTS = ["hook","device","world","grammar","camera","sonic","type","ending"]

def pools():
    return {
        "hook":    HOOK_ARCHETYPES,
        "device":  NARRATIVE_DEVICES,
        "world":   VISUAL_WORLDS,
        "grammar": EDITING_GRAMMARS,
        "camera":  CAMERA_LANGUAGES,
        "sonic":   SONIC_IDENTITIES,
        "type":    TYPOGRAPHIC_TWISTS,
        "ending":  ENDING_DEVICES,
    }

def counts():
    p = pools()
    c = {k: len(v) for k, v in p.items()}
    c["signature_moves"] = len(SIGNATURE_MOVES)
    c["pattern_interrupts"] = len(PATTERN_INTERRUPTS)
    c["transition_kinds"] = len(TRANSITION_KINDS["existing"]) + len(TRANSITION_KINDS["to_build"])
    c["sfx_voices"] = len(SFX_VOICES["used"]) + len(SFX_VOICES["fresh"])
    return c
