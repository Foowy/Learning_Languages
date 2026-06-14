"""Generate ASL lesson JSON files into lessons/asl/."""
import json
from pathlib import Path

OUT = Path(__file__).parent.parent / "lessons" / "asl"

LESSONS = [
    # ── Unit 1: Manual Alphabet ────────────────────────────────────────────────
    {
        "unit": 1, "lesson": 1,
        "title": "Manual Alphabet: A – E",
        "cards": [
            {"type": "fingerspelling", "character": "A", "romaji": "A", "meaning": "letter A", "video": "fs_a.mp4"},
            {"type": "fingerspelling", "character": "B", "romaji": "B", "meaning": "letter B", "video": "fs_b.mp4"},
            {"type": "fingerspelling", "character": "C", "romaji": "C", "meaning": "letter C", "video": "fs_c.mp4"},
            {"type": "fingerspelling", "character": "D", "romaji": "D", "meaning": "letter D", "video": "fs_d.mp4"},
            {"type": "fingerspelling", "character": "E", "romaji": "E", "meaning": "letter E", "video": "fs_e.mp4"},
        ],
    },
    {
        "unit": 1, "lesson": 2,
        "title": "Manual Alphabet: F – J",
        "cards": [
            {"type": "fingerspelling", "character": "F", "romaji": "F", "meaning": "letter F", "video": "fs_f.mp4"},
            {"type": "fingerspelling", "character": "G", "romaji": "G", "meaning": "letter G", "video": "fs_g.mp4"},
            {"type": "fingerspelling", "character": "H", "romaji": "H", "meaning": "letter H", "video": "fs_h.mp4"},
            {"type": "fingerspelling", "character": "I", "romaji": "I", "meaning": "letter I", "video": "fs_i.mp4"},
            {"type": "fingerspelling", "character": "J", "romaji": "J", "meaning": "letter J", "video": "fs_j.mp4"},
        ],
    },
    {
        "unit": 1, "lesson": 3,
        "title": "Manual Alphabet: K – O",
        "cards": [
            {"type": "fingerspelling", "character": "K", "romaji": "K", "meaning": "letter K", "video": "fs_k.mp4"},
            {"type": "fingerspelling", "character": "L", "romaji": "L", "meaning": "letter L", "video": "fs_l.mp4"},
            {"type": "fingerspelling", "character": "M", "romaji": "M", "meaning": "letter M", "video": "fs_m.mp4"},
            {"type": "fingerspelling", "character": "N", "romaji": "N", "meaning": "letter N", "video": "fs_n.mp4"},
            {"type": "fingerspelling", "character": "O", "romaji": "O", "meaning": "letter O", "video": "fs_o.mp4"},
        ],
    },
    {
        "unit": 1, "lesson": 4,
        "title": "Manual Alphabet: P – T",
        "cards": [
            {"type": "fingerspelling", "character": "P", "romaji": "P", "meaning": "letter P", "video": "fs_p.mp4"},
            {"type": "fingerspelling", "character": "Q", "romaji": "Q", "meaning": "letter Q", "video": "fs_q.mp4"},
            {"type": "fingerspelling", "character": "R", "romaji": "R", "meaning": "letter R", "video": "fs_r.mp4"},
            {"type": "fingerspelling", "character": "S", "romaji": "S", "meaning": "letter S", "video": "fs_s.mp4"},
            {"type": "fingerspelling", "character": "T", "romaji": "T", "meaning": "letter T", "video": "fs_t.mp4"},
        ],
    },
    {
        "unit": 1, "lesson": 5,
        "title": "Manual Alphabet: U – Z",
        "cards": [
            {"type": "fingerspelling", "character": "U", "romaji": "U", "meaning": "letter U", "video": "fs_u.mp4"},
            {"type": "fingerspelling", "character": "V", "romaji": "V", "meaning": "letter V", "video": "fs_v.mp4"},
            {"type": "fingerspelling", "character": "W", "romaji": "W", "meaning": "letter W", "video": "fs_w.mp4"},
            {"type": "fingerspelling", "character": "X", "romaji": "X", "meaning": "letter X", "video": "fs_x.mp4"},
            {"type": "fingerspelling", "character": "Y", "romaji": "Y", "meaning": "letter Y", "video": "fs_y.mp4"},
            {"type": "fingerspelling", "character": "Z", "romaji": "Z", "meaning": "letter Z", "video": "fs_z.mp4"},
        ],
    },

    # ── Unit 2: Numbers ────────────────────────────────────────────────────────
    {
        "unit": 2, "lesson": 1,
        "title": "Numbers: 1 – 5",
        "cards": [
            {"type": "number", "character": "1", "romaji": "one",   "meaning": "one",   "video": "num_1.mp4"},
            {"type": "number", "character": "2", "romaji": "two",   "meaning": "two",   "video": "num_2.mp4"},
            {"type": "number", "character": "3", "romaji": "three", "meaning": "three", "video": "num_3.mp4"},
            {"type": "number", "character": "4", "romaji": "four",  "meaning": "four",  "video": "num_4.mp4"},
            {"type": "number", "character": "5", "romaji": "five",  "meaning": "five",  "video": "num_5.mp4"},
        ],
    },
    {
        "unit": 2, "lesson": 2,
        "title": "Numbers: 6 – 10",
        "cards": [
            {"type": "number", "character": "6",  "romaji": "six",   "meaning": "six",   "video": "num_6.mp4"},
            {"type": "number", "character": "7",  "romaji": "seven", "meaning": "seven", "video": "num_7.mp4"},
            {"type": "number", "character": "8",  "romaji": "eight", "meaning": "eight", "video": "num_8.mp4"},
            {"type": "number", "character": "9",  "romaji": "nine",  "meaning": "nine",  "video": "num_9.mp4"},
            {"type": "number", "character": "10", "romaji": "ten",   "meaning": "ten",   "video": "num_10.mp4"},
        ],
    },
    {
        "unit": 2, "lesson": 3,
        "title": "Numbers: 11 – 15",
        "cards": [
            {"type": "number", "character": "11", "romaji": "eleven",   "meaning": "eleven",   "video": "num_11.mp4"},
            {"type": "number", "character": "12", "romaji": "twelve",   "meaning": "twelve",   "video": "num_12.mp4"},
            {"type": "number", "character": "13", "romaji": "thirteen", "meaning": "thirteen", "video": "num_13.mp4"},
            {"type": "number", "character": "14", "romaji": "fourteen", "meaning": "fourteen", "video": "num_14.mp4"},
            {"type": "number", "character": "15", "romaji": "fifteen",  "meaning": "fifteen",  "video": "num_15.mp4"},
        ],
    },
    {
        "unit": 2, "lesson": 4,
        "title": "Numbers: 16 – 20",
        "cards": [
            {"type": "number", "character": "16", "romaji": "sixteen",   "meaning": "sixteen",   "video": "num_16.mp4"},
            {"type": "number", "character": "17", "romaji": "seventeen", "meaning": "seventeen", "video": "num_17.mp4"},
            {"type": "number", "character": "18", "romaji": "eighteen",  "meaning": "eighteen",  "video": "num_18.mp4"},
            {"type": "number", "character": "19", "romaji": "nineteen",  "meaning": "nineteen",  "video": "num_19.mp4"},
            {"type": "number", "character": "20", "romaji": "twenty",    "meaning": "twenty",    "video": "num_20.mp4"},
        ],
    },

    # ── Unit 3: Greetings & Basics ─────────────────────────────────────────────
    {
        "unit": 3, "lesson": 1,
        "title": "Greetings",
        "cards": [
            {"type": "sign", "character": "HELLO",    "romaji": "hello",     "meaning": "hello / greetings",  "video": "sign_hello.mp4"},
            {"type": "sign", "character": "GOODBYE",  "romaji": "goodbye",   "meaning": "goodbye / bye",      "video": "sign_goodbye.mp4"},
            {"type": "sign", "character": "PLEASE",   "romaji": "please",    "meaning": "please",             "video": "sign_please.mp4"},
            {"type": "sign", "character": "THANK YOU","romaji": "thank you", "meaning": "thank you",          "video": "sign_thank_you.mp4"},
            {"type": "sign", "character": "SORRY",    "romaji": "sorry",     "meaning": "sorry / excuse me",  "video": "sign_sorry.mp4"},
        ],
    },
    {
        "unit": 3, "lesson": 2,
        "title": "Essential Signs",
        "cards": [
            {"type": "sign", "character": "YES",  "romaji": "yes",  "meaning": "yes",      "video": "sign_yes.mp4"},
            {"type": "sign", "character": "NO",   "romaji": "no",   "meaning": "no",       "video": "sign_no.mp4"},
            {"type": "sign", "character": "HELP", "romaji": "help", "meaning": "help",     "video": "sign_help.mp4"},
            {"type": "sign", "character": "STOP", "romaji": "stop", "meaning": "stop",     "video": "sign_stop.mp4"},
            {"type": "sign", "character": "MORE", "romaji": "more", "meaning": "more",     "video": "sign_more.mp4"},
        ],
    },
    {
        "unit": 3, "lesson": 3,
        "title": "Question Words",
        "cards": [
            {"type": "sign", "character": "WHAT",  "romaji": "what",  "meaning": "what",  "video": "sign_what.mp4"},
            {"type": "sign", "character": "WHERE", "romaji": "where", "meaning": "where", "video": "sign_where.mp4"},
            {"type": "sign", "character": "WHEN",  "romaji": "when",  "meaning": "when",  "video": "sign_when.mp4"},
            {"type": "sign", "character": "WHO",   "romaji": "who",   "meaning": "who",   "video": "sign_who.mp4"},
            {"type": "sign", "character": "HOW",   "romaji": "how",   "meaning": "how",   "video": "sign_how.mp4"},
        ],
    },
    {
        "unit": 3, "lesson": 4,
        "title": "Introductions",
        "cards": [
            {"type": "sign", "character": "MY NAME",  "romaji": "my name",  "meaning": "my name is",   "video": "sign_my_name.mp4"},
            {"type": "sign", "character": "YOUR NAME", "romaji": "your name", "meaning": "what is your name", "video": "sign_your_name.mp4"},
            {"type": "sign", "character": "NICE TO MEET YOU", "romaji": "nice to meet you", "meaning": "nice to meet you", "video": "sign_nice_to_meet_you.mp4"},
            {"type": "sign", "character": "I LOVE YOU", "romaji": "I love you", "meaning": "I love you", "video": "sign_i_love_you.mp4"},
            {"type": "sign", "character": "UNDERSTAND", "romaji": "understand", "meaning": "understand / I understand", "video": "sign_understand.mp4"},
        ],
    },

    # ── Unit 4: Family ─────────────────────────────────────────────────────────
    {
        "unit": 4, "lesson": 1,
        "title": "Immediate Family",
        "cards": [
            {"type": "sign", "character": "MOTHER",  "romaji": "mother",  "meaning": "mother / mom",   "video": "sign_mother.mp4"},
            {"type": "sign", "character": "FATHER",  "romaji": "father",  "meaning": "father / dad",   "video": "sign_father.mp4"},
            {"type": "sign", "character": "SISTER",  "romaji": "sister",  "meaning": "sister",         "video": "sign_sister.mp4"},
            {"type": "sign", "character": "BROTHER", "romaji": "brother", "meaning": "brother",        "video": "sign_brother.mp4"},
            {"type": "sign", "character": "BABY",    "romaji": "baby",    "meaning": "baby",           "video": "sign_baby.mp4"},
        ],
    },
    {
        "unit": 4, "lesson": 2,
        "title": "Extended Family",
        "cards": [
            {"type": "sign", "character": "GRANDMOTHER", "romaji": "grandmother", "meaning": "grandmother", "video": "sign_grandmother.mp4"},
            {"type": "sign", "character": "GRANDFATHER", "romaji": "grandfather", "meaning": "grandfather", "video": "sign_grandfather.mp4"},
            {"type": "sign", "character": "AUNT",        "romaji": "aunt",        "meaning": "aunt",        "video": "sign_aunt.mp4"},
            {"type": "sign", "character": "UNCLE",       "romaji": "uncle",       "meaning": "uncle",       "video": "sign_uncle.mp4"},
            {"type": "sign", "character": "FAMILY",      "romaji": "family",      "meaning": "family",      "video": "sign_family.mp4"},
        ],
    },

    # ── Unit 5: Everyday Signs ─────────────────────────────────────────────────
    {
        "unit": 5, "lesson": 1,
        "title": "Action Verbs",
        "cards": [
            {"type": "sign", "character": "EAT",   "romaji": "eat",   "meaning": "eat / food",  "video": "sign_eat.mp4"},
            {"type": "sign", "character": "DRINK", "romaji": "drink", "meaning": "drink",        "video": "sign_drink.mp4"},
            {"type": "sign", "character": "SLEEP", "romaji": "sleep", "meaning": "sleep",        "video": "sign_sleep.mp4"},
            {"type": "sign", "character": "WALK",  "romaji": "walk",  "meaning": "walk",         "video": "sign_walk.mp4"},
            {"type": "sign", "character": "PLAY",  "romaji": "play",  "meaning": "play",         "video": "sign_play.mp4"},
        ],
    },
    {
        "unit": 5, "lesson": 2,
        "title": "Places",
        "cards": [
            {"type": "sign", "character": "HOME",     "romaji": "home",     "meaning": "home / house",   "video": "sign_home.mp4"},
            {"type": "sign", "character": "SCHOOL",   "romaji": "school",   "meaning": "school",         "video": "sign_school.mp4"},
            {"type": "sign", "character": "WORK",     "romaji": "work",     "meaning": "work / job",     "video": "sign_work.mp4"},
            {"type": "sign", "character": "STORE",    "romaji": "store",    "meaning": "store / shop",   "video": "sign_store.mp4"},
            {"type": "sign", "character": "HOSPITAL", "romaji": "hospital", "meaning": "hospital",       "video": "sign_hospital.mp4"},
        ],
    },
    {
        "unit": 5, "lesson": 3,
        "title": "Descriptors",
        "cards": [
            {"type": "sign", "character": "GOOD",  "romaji": "good",  "meaning": "good",  "video": "sign_good.mp4"},
            {"type": "sign", "character": "BAD",   "romaji": "bad",   "meaning": "bad",   "video": "sign_bad.mp4"},
            {"type": "sign", "character": "BIG",   "romaji": "big",   "meaning": "big",   "video": "sign_big.mp4"},
            {"type": "sign", "character": "SMALL", "romaji": "small", "meaning": "small", "video": "sign_small.mp4"},
            {"type": "sign", "character": "HOT",   "romaji": "hot",   "meaning": "hot",   "video": "sign_hot.mp4"},
        ],
    },
]


def main():
    for lesson in LESSONS:
        unit_dir = OUT / f"unit{lesson['unit']}"
        unit_dir.mkdir(parents=True, exist_ok=True)
        path = unit_dir / f"lesson{lesson['lesson']:02d}.json"
        path.write_text(json.dumps(lesson, ensure_ascii=False, indent=2))
        print(f"wrote {path.relative_to(OUT.parent.parent)}")


if __name__ == "__main__":
    main()
