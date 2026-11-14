import unittest
from sensor_triggers import CycleTrigger, GestureTrigger, is_food

class TriggerTests(unittest.TestCase):
    def test_food(self):
        self.assertTrue(is_food(70,25,5,100))
        self.assertTrue(is_food(700,250,50,1000))
        for data in [(1,0,0,1),(10,70,20,100),(0,0,0,0)]: self.assertFalse(is_food(*data))
    def test_stable_release(self):
        t = CycleTrigger()
        self.assertFalse(t.update(True,False,0))
        self.assertFalse(t.update(True,False,.1))
        self.assertTrue(t.update(True,False,.2))
        self.assertFalse(t.update(True,False,9))
        t.update(False,True,10)
        t.update(True,False,11)
        self.assertFalse(t.update(True,False,12))
        for n in range(3): t.update(False,True,13+n*.1)
        for n in range(2): self.assertFalse(t.update(True,False,14+n*.1))
        self.assertTrue(t.update(True,False,14.2))
    def test_hold_hysteresis(self):
        t = CycleTrigger(hold=2)
        for n in range(20): self.assertFalse(t.update(True,False,n*.1))
        self.assertTrue(t.update(True,False,2))
        for n in range(3,6): t.update(False,False,n)
        self.assertFalse(t.update(True,False,10))
        self.assertFalse(t.update(True,False,13))
    def test_cooldown_consumes_cycle(self):
        t = CycleTrigger(stable=1,release_samples=1)
        self.assertTrue(t.update(True,False,0))
        t.update(False,True,1)
        self.assertFalse(t.update(True,False,2))
        self.assertFalse(t.update(True,False,5))
        t.update(False,True,6)
        self.assertTrue(t.update(True,False,7))
    def test_gesture(self):
        t = GestureTrigger()
        self.assertFalse(t.update(1,0))
        self.assertTrue(t.update(3,0))
        self.assertFalse(t.update(4,1))
        self.assertTrue(t.update(4,3))
