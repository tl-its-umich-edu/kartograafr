import unittest
import util
import re

import main
#from cssutils.helper import string

FIVE = ['BACH','DYLAN','BROWN','SIMON','SMALTZ']

class MembershipTestCase(unittest.TestCase):

#     def test_simple(self):
#         self.assertEqual("a","a")

    ############# Methods that demonstrate the required behavior
    # trim off the first underscore and anything after that.
    def trimTail(self,abba):
        return re.sub('_\S+$','',abba)
    
    # test list comprehension 
    def trimTailList(self,string_list):
        print "string_list: "+",".join(string_list)
        #stuff = [u.lower() for u in string_list]
        stuff = [re.sub('_\S+$','',u) for u in string_list]
        print "made list: "+",".join(stuff)
        return stuff
    
    #### helper
    def assertListUnorderedEqual(self,list_A,list_B):
        return self.assertSetEqual(set(list_A),set(list_B))

    #################  

    def test_HOWDY_ho(self):
        s1 = "HOWDY_ho"
        right = "HOWDY"
        s = self.trimTail(s1)
        self.assertEquals(right,s)

    def test_HOWDY_ho_twice(self):
        s1 = "HOWDY_ho"
        s1 = s1+'_'+s1
        right = "HOWDY"
        s = self.trimTail(s1)
        self.assertEquals(right,s)
        
    def test_HOWDY(self):
        s1 = "HOWDY"
        s = self.trimTail(s1)
        self.assertEquals(s1,s)

    def test_empty(self):
        s1 = ""
        s = self.trimTail(s1)
        self.assertEquals(s1,s)
        
    def test_listOfTwo(self):
        s1 = ["HOWDY_A","DUTY_B"]
        right = ['HOWDY','DUTY']
        s = self.trimTailList(s1)
        self.assertEquals(right,s)

    ############# verify getting list differences
        
    def test_list_diffs_unshared(self):
        l1 = ['ONE','TWO']
        l2 = ['TWO','THREE']
        
        r1,r2,r3 = main.listDifferences(l1,l2)
        #assertListUnorderedEqual
        self.assertListUnorderedEqual(r1,['ONE'])
        self.assertListUnorderedEqual(r2,['THREE'])
        self.assertListUnorderedEqual(r3,['TWO'])
    
    def test_list_diffs_share_one_value(self):
        l1 = ['ONE','TWO','FIVE']
        l2 = ['TWO','THREE','FOUR']
        
        r1,r2,r3 = main.listDifferences(l1,l2)
        self.assertListUnorderedEqual(r1,['ONE','FIVE'])
        self.assertListUnorderedEqual(r2,['FOUR','THREE'])
        self.assertListUnorderedEqual(r3,['TWO'])
        
    def test_list_diffs_share_TWO(self):
        l1 = ['ONE','TWO','THREE']
        l2 = ['TWO','THREE','FOUR']
        
        r1,r2,r3 = main.listDifferences(l1,l2)
        self.assertListUnorderedEqual(r1,['ONE'])
        self.assertListUnorderedEqual(r2,['FOUR'])
        self.assertListUnorderedEqual(r3,['TWO','THREE'])
        
    def test_list_diffs_ignore_dups(self):
        l1 = ['TWO','THREE','FOUR','FIVE','TWO','FOUR']
        l2 = ['FOUR','THREE','FOUR']

        r1,r2,r3 = main.listDifferences(l1,l2)

        self.assertListUnorderedEqual(r1,['TWO','FIVE'])
        self.assertListUnorderedEqual(r2,[])
        self.assertListUnorderedEqual(r3,['THREE','FOUR'])
        
    def test_list_diffs_subset(self):
        l1 = ['TWO','THREE','FOUR','FIVE']
        l2 = ['FOUR','THREE']

        r1,r2,r3 = main.listDifferences(l1,l2)

        self.assertListUnorderedEqual(r1,['TWO','FIVE'])
        self.assertListUnorderedEqual(r2,[])
        self.assertListUnorderedEqual(r3,['THREE','FOUR'])
        
    def test_list_diffs_identical(self):
        l1 = ['TWO','THREE']
        l2 = ['TWO','THREE']

        r1,r2,r3 = main.listDifferences(l1,l2)

        self.assertListUnorderedEqual(r1,[])
        self.assertListUnorderedEqual(r2,[])
        self.assertListUnorderedEqual(r3,['TWO','THREE'])
        
#end