#include "word_db.h"
#include "test_harness/test_harness.h"

using namespace bng::word_db;

static char dict_text[] =
	"ant\nantonym\n"
	"bean\nbearskin\n"
	"cat\n"
	"debating\ndog\n"
	"ear\n"
	"fit\n"
	"gab\n"
	"hah\nheehaw\nhumdinger\n"
	"ion\n"
	"jot\n"
	"kit\n"
	"lag\n"
	"manta\n"
	"nematode\n"
	"octopus\n"
	"penguin\n"
	"quiche\n"
	"ramen\n"
	"s\nsmoked\nsupercalifragilisticexpialidocious\n"
	"tan\n"
	"use\n"
	"vim\n"
	"wit\n"
	"xray\n"
	"yank\n"
	"zebra\nzephyr\nzigzag\n";

// bearskin -> nematode is one possible answer
const char* puzzle_sides[] = {
	"btn", "akd", "oes", "mir"
};

const char* puzzle_sides_2[] = {
	"btn", "akd", "oes", "mig"
};

void write_word_list() {
	File word_list("word_list.txt", "w");
	assert(word_list);
	fwrite(dict_text, sizeof(dict_text) - 1, 1, word_list);
}

BNG_BEGIN_TEST(dict_counts) {
	TextBuf db(sizeof(dict_text) - 1);
	memcpy(db.end(), dict_text, sizeof(dict_text) - 1);
	db.set_size(db.capacity());

	TextStats stats = db.collect_stats();

	BT_CHECK(stats.word_counts['a' - 'a'] == 2);
	BT_CHECK(stats.word_counts['b' - 'a'] == 2);
	BT_CHECK(stats.word_counts['c' - 'a'] == 1);
	BT_CHECK(stats.word_counts['d' - 'a'] == 2);
	BT_CHECK(stats.word_counts['e' - 'a'] == 1);
	BT_CHECK(stats.word_counts['f' - 'a'] == 1);
	BT_CHECK(stats.word_counts['g' - 'a'] == 1);
	BT_CHECK(stats.word_counts['h' - 'a'] == 3);
	BT_CHECK(stats.word_counts['i' - 'a'] == 1);
	BT_CHECK(stats.word_counts['j' - 'a'] == 1);
	BT_CHECK(stats.word_counts['k' - 'a'] == 1);
	BT_CHECK(stats.word_counts['l' - 'a'] == 1);
	BT_CHECK(stats.word_counts['m' - 'a'] == 1);
	BT_CHECK(stats.word_counts['n' - 'a'] == 1);
	BT_CHECK(stats.word_counts['o' - 'a'] == 1);
	BT_CHECK(stats.word_counts['p' - 'a'] == 1);
	BT_CHECK(stats.word_counts['q' - 'a'] == 1);
	BT_CHECK(stats.word_counts['r' - 'a'] == 1);
	BT_CHECK(stats.word_counts['s' - 'a'] == 3);
	BT_CHECK(stats.word_counts['t' - 'a'] == 1);
	BT_CHECK(stats.word_counts['u' - 'a'] == 1);
	BT_CHECK(stats.word_counts['v' - 'a'] == 1);
	BT_CHECK(stats.word_counts['w' - 'a'] == 1);
	BT_CHECK(stats.word_counts['x' - 'a'] == 1);
	BT_CHECK(stats.word_counts['y' - 'a'] == 1);
	BT_CHECK(stats.word_counts['z' - 'a'] == 3);
	BT_CHECK(stats.total_count() == 35);

	BT_CHECK(stats.size_bytes['a' - 'a'] == 12);
	BT_CHECK(stats.size_bytes['b' - 'a'] == 14);
	BT_CHECK(stats.size_bytes['c' - 'a'] == 4);
	BT_CHECK(stats.size_bytes['d' - 'a'] == 13);
	BT_CHECK(stats.size_bytes['e' - 'a'] == 4);
	BT_CHECK(stats.size_bytes['f' - 'a'] == 4);
	BT_CHECK(stats.size_bytes['g' - 'a'] == 4);
	BT_CHECK(stats.size_bytes['h' - 'a'] == 21);
	BT_CHECK(stats.size_bytes['i' - 'a'] == 4);
	BT_CHECK(stats.size_bytes['j' - 'a'] == 4);
	BT_CHECK(stats.size_bytes['k' - 'a'] == 4);
	BT_CHECK(stats.size_bytes['l' - 'a'] == 4);
	BT_CHECK(stats.size_bytes['m' - 'a'] == 6);
	BT_CHECK(stats.size_bytes['n' - 'a'] == 9);
	BT_CHECK(stats.size_bytes['o' - 'a'] == 8);
	BT_CHECK(stats.size_bytes['p' - 'a'] == 8);
	BT_CHECK(stats.size_bytes['q' - 'a'] == 7);
	BT_CHECK(stats.size_bytes['r' - 'a'] == 6);
	BT_CHECK(stats.size_bytes['s' - 'a'] == 44);
	BT_CHECK(stats.size_bytes['t' - 'a'] == 4);
	BT_CHECK(stats.size_bytes['u' - 'a'] == 4);
	BT_CHECK(stats.size_bytes['v' - 'a'] == 4);
	BT_CHECK(stats.size_bytes['w' - 'a'] == 4);
	BT_CHECK(stats.size_bytes['x' - 'a'] == 5);
	BT_CHECK(stats.size_bytes['y' - 'a'] == 5);
	BT_CHECK(stats.size_bytes['z' - 'a'] == 20);
	BT_CHECK(stats.total_size_bytes() == uint32_t(sizeof(dict_text) - 1));
}
BNG_END_TEST()

BNG_BEGIN_TEST(load_and_solve) {
	write_word_list();
	{
		WordDB db;
		BT_CHECK(!db);
		BT_CHECK(!db.load("foo.txt"));
		BT_CHECK(!db);
		BT_CHECK(!db.load("foo.pre"));
		BT_CHECK(!db);

		WordDB db2("foo.txt");
		BT_CHECK(!db2);

		WordDB db3("foo.pre");
		BT_CHECK(!db3);
	}

	{
		WordDB db("word_list.txt");
		BT_CHECK(db);

		for (uint32_t i = 0; i < 26; ++i) {
			if (db.get_text_stats().word_counts[i]) {
				BT_CHECK(db.first_letter_idx(*db.first_word(i)) == i);
				BT_CHECK(db.first_letter_idx(*db.last_word(i)) == i);
			}
			else {
				BT_CHECK(!db.first_word(i));
			}
		}

		db.save("words.pre");
		BT_CHECK(File("words.pre", "rb"));
		WordDB db2("words.pre");
		BT_CHECK(db2);
		BT_CHECK(db.is_equivalent(db2));
	}
	{
		WordDB db;
		BT_CHECK(db.load("words.pre"));
		(void)unlink("words.pre");

		for (uint32_t i = 0; i < 26; ++i) {
			if (db.get_text_stats().word_counts[i]) {
				BT_CHECK(db.first_letter_idx(*db.first_word(i)) == i);
				BT_CHECK(db.first_letter_idx(*db.last_word(i)) == i);
			}
			else {
				BT_CHECK(!db.first_word(i));
			}
		}

		const WordDB::SideSet sides_1 = {
			Word(puzzle_sides[0]),
			Word(puzzle_sides[1]),
			Word(puzzle_sides[2]),
			Word(puzzle_sides[3])
		};

		const WordDB::SideSet sides_2 = {
			Word(puzzle_sides_2[0]),
			Word(puzzle_sides_2[1]),
			Word(puzzle_sides_2[2]),
			Word(puzzle_sides_2[3])
		};

		const auto puzzle_letters_1 = uint32_t(sides_1[0].letters | sides_1[1].letters | sides_1[2].letters | sides_1[3].letters);
		const auto puzzle_letters_2 = uint32_t(sides_2[0].letters | sides_2[1].letters | sides_2[2].letters | sides_2[3].letters);
		const auto dict_letters = []() {
			uint32_t bits = 0;
			for (auto c : dict_text) {
				bits |= uint32_t(1u << uint32_t(c - 'a'));
			}
			return bits;
		}();
		// verify that the test data dictionary has all the letters needed to solve the puzzles
		assert((dict_letters & puzzle_letters_1) == puzzle_letters_1);
		assert((dict_letters & puzzle_letters_2) == puzzle_letters_2);

		// verify the dictionary preprocessing did not eliminate words it should not have
		// and that they are sufficient to solve the puzzle
		{
			const uint32_t live_count = db.get_text_stats().total_count();
			// 3 less than the 35 in the dictionary. culled:
			// s - too short
			// heehaw - double letter
			// supercalifragilisticexpialidocious - more than 12 unique letters
			BT_CHECK(live_count == 32);

			uint32_t live_letters = 0;
			for (uint32_t i = 0, li = 0; li < live_count; ++i) {
				const auto& w = *db.word(WordIdx(i));
				if (!w) {
					continue;
				}
				BT_CHECK(!w.is_dead);
				live_letters |= uint32_t(w.letters);
				++li;
				// printf("%.*s\n", uint32_t(w.length), db.get_text_buf().ptr(w));
			}
			BT_CHECK((live_letters & puzzle_letters_1) == puzzle_letters_1);
			BT_CHECK((live_letters & puzzle_letters_2) == puzzle_letters_2);
		}

		{
			auto db_culled = db.culled(sides_1);

			SolutionSet solutions = db_culled.solve(sides_1);

			BT_CHECK(solutions.size() == 1);

			const auto& ps = solutions.front();
			auto& a = *db_culled.word(ps.a);
			auto& b = *db_culled.word(ps.b);
			auto sa = db_culled.str(a); (void)sa;
			auto sb = db_culled.str(b); (void)sb;

			BT_CHECK(!strncmp(sa, "bearskin", a.length));
			BT_CHECK(!strncmp(sb, "nematode", b.length));
		}

		// test re-use of word db
		{
			auto db_culled = db.culled(sides_2);

			SolutionSet solutions = db_culled.solve(sides_2);

			BT_CHECK(solutions.size() == 1);

			const auto& ps = solutions.front();
			auto& a = *db_culled.word(ps.a);
			auto& b = *db_culled.word(ps.b);
			auto sa = db_culled.str(a); (void)sa;
			auto sb = db_culled.str(b); (void)sb;

			BT_CHECK(!strncmp(sa, "smoked", a.length));
			BT_CHECK(!strncmp(sb, "debating", b.length));
		}
	}
	unlink("word_list.txt");
}

BNG_END_TEST()

