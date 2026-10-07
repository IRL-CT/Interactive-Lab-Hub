import unittest
from cooking_assistant import Conversation


class ConversationTest(unittest.TestCase):
    def setUp(self):
        self.bot = Conversation()

    def test_start_and_next(self):
        self.assertIn("chop", self.bot.respond("start")[0].lower())
        self.assertIn("heat", self.bot.respond("next")[0].lower())

    def test_repeat(self):
        first = self.bot.respond("start")[0]
        self.assertEqual(self.bot.respond("repeat that")[0], first)

    def test_substitution(self):
        self.assertIn("vegetable oil", self.bot.respond("I do not have olive oil")[0].lower())

    def test_multiple_ingredient_substitutions(self):
        examples = {
            "I don't have onions": "shallot",
            "We are out of butter": "olive oil",
            "Can I make this without milk?": "oat milk",
            "I have no eggs": "flax egg",
            "I don't have garlic": "garlic powder",
        }
        for request, expected in examples.items():
            with self.subTest(request=request):
                self.assertIn(expected, self.bot.respond(request)[0].lower())

    def test_unknown_missing_ingredient(self):
        reply, _ = self.bot.respond("I don't have basil")
        self.assertIn("which ingredient", reply.lower())

    def test_stop(self):
        self.assertTrue(self.bot.respond("stop cooking")[1])

    def test_timer_confirmation(self):
        self.assertIn("7 minutes", self.bot.respond("set a timer for seven minutes")[0])
        self.assertIn("started", self.bot.respond("yes")[0])
        self.assertEqual(self.bot.timer_action, ("start", 7))

    def test_numeric_timer_and_cancel(self):
        self.bot.respond("set a timer for 12 minutes")
        self.bot.respond("yes")
        self.bot.respond("cancel the timer")
        self.assertEqual(self.bot.timer_action, ("cancel", None))

    def test_timer_remaining(self):
        reply, _ = self.bot.respond("how much time is left on the timer", 125)
        self.assertIn("2 minutes and 5 seconds", reply)

    def test_timer_range(self):
        reply, _ = self.bot.respond("set a timer for 99 minutes")
        self.assertIn("between one and sixty", reply)


if __name__ == "__main__":
    unittest.main()
