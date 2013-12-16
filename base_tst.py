
import time
import logging
l = logging.getLogger('selenium.webdriver.remote.remote_connection')
l.setLevel(logging.INFO)

import imaplib
import email.parser
import traceback
import sys
import gc
import pprint

from nose.tools import eq_, ok_
from nose.plugins.skip import SkipTest

from selenium.common.exceptions import WebDriverException,StaleElementReferenceException

class TestCaseBase(object):
  TIME_TO_WAIT = 10  # TODO factor out all the constants and delays and retries.
  POLLING_DELAY = 0.1  # TODO factor out all the constants and delays and retries.
  __test__ = True  # needed for nose matching without inheriting from unittest.TestCase
  def XFAIL(self, msg, f, args):
    try:
      f(*args)
    except AssertionError, exc:
      raise SkipTest("XFail: %s: %s" % (msg, exc))
    raise AssertionError("Test was expected to fail but passed: %s" % msg)

  def skip_tst(self, msg):
    raise SkipTest(msg)

  # You shouldn't call sleep() in a test.  So call this so it is logged with a reason
  # You should be using events for syncronization to avoid flakey tests
  def wait(self, seconds, comment):
    print "     !!! waiting %d second(s) because %s !!!" % (seconds, comment)
    time.sleep(seconds)

  def print_pass(self, msg):
    print "PASS: %s" % msg

  def is_op(self, a, op, sym, g, msg, only_if):
    try:
      g_b = g()
    except TypeError:
      g_b = g  # if it isn't callable that is OK
    #
    try:
      b = g_b.next()
    except AttributeError:  # must just be a value
      b = g_b
    #
    print "  %r: %r ?%s %r" % (op(a,b), a, sym, b)
    ret = ok_(op(a,b), "FAIL: %r not %s %r" % (a, sym, b))
    if msg == '':
      msg = "%r %s %r" % (a, sym, b)
    self.print_pass(msg)
    return ret

  # The try_is asserts are polling due to ajax.  Imagine clicking on the Follow
  # button in twitter, then the # of followers should increment but the page won't reload.
  # Also sometimes the element doesn't exist in the DOM yet.  So you have to wait for it to
  # appear and then make sure it is correct.
  # ag and bg can be values, function, iterators, or generators and they will be
  # evaluated correctly no matter what type comes in.
  def try_is(self, ag, op, sym, bg, msg, only_if):
    if not only_if:
      print "  Skipping ?%s because only_if=%r\n" % (sym,only_if,)
      return

    start = time.time()
    while time.time() - start < self.TIME_TO_WAIT:
      try:
        try:
          g_a = ag()
        except TypeError:
          g_a = ag  # if it isn't callable that is OK
        #
        try:
          g_b = bg()
        except TypeError:
          g_b = bg  # if it isn't callable that is OK
        #
        try:
          a = g_a.next()
        except AttributeError:  # must just be a value
          a = g_a
        #
        try:
          b = g_b.next()
        except AttributeError:  # must just be a value
          b = g_b
        #
        print "  %r: %r ?%s %r" % (op(a,b), a, sym, b)
        ret = ok_(op(a,b), "FAIL: %r not %s %r" % (a, sym, b))

        if msg == '':
          msg = "%r %s %r" % (a, sym, b)
        self.print_pass(msg)
        #
        return ret
      except WebDriverException, exc:
        print "  Waiting for element(s): %5.2fsecs" % (time.time() - start)
        time.sleep(self.POLLING_DELAY)
      except StaleElementReferenceException, exc:
        print "  Stale element Exception: %5.2fsecs - %s" % ((time.time() - start), exc)
        time.sleep(self.POLLING_DELAY)
      except AssertionError, exc:
        print "  Waiting for try_is(%s): %5.2fsecs" % (sym, time.time() - start)
        time.sleep(self.POLLING_DELAY)
      except StopIteration, exc:
        # once a generator raises an exception you can't call it again, so fail.
        print "  Strange Exception broke a generator"
        raise
      except SkipTest:
        print "  Skipping test from try_is()"
        raise
      except Exception, exc:
        # catchall for any other things that might go wrong
        print "  General Exception: %5.2fsecs - %s" % ((time.time() - start), exc)
        time.sleep(self.POLLING_DELAY)
      #
    # end while
    raise exc

  def is_equal(self, a, b, msg='', only_if=True):
    self.is_op(a, lambda a,b: a==b, '==', b, msg, only_if)

  def is_not_equal(self, a, b, msg='', only_if=True):
    self.is_op(a, lambda a,b: a!=b, '!=', b, msg, only_if)

  def is_lt(self, a, b, msg='', only_if=True):
    self.is_op(a, lambda a,b: a<b, '<', b, msg, only_if)

  def is_le(self, a, b, msg='', only_if=True):
    self.is_op(a, lambda a,b: a<=b, '<=', b, msg, only_if)

  def is_gt(self, a, b, msg='', only_if=True):
    self.is_op(a, lambda a,b: a>b, '>', b, msg, only_if)

  def is_ge(self, a, b, msg='', only_if=True):
    self.is_op(a, lambda a,b: a>=b, '>=', b, msg, only_if)

  def is_in(self, a, b, msg='', only_if=True):
    self.is_op(a, lambda a,b: a in b, 'in', b, msg, only_if)

  def try_is_equal(self, a, b, msg='', only_if=True):
    self.try_is(a, lambda a,b: a==b, '==', b, msg, only_if)

  def try_is_lt(self, a, b, msg='', only_if=True):
    self.try_is(a, lambda a,b: a<b, '<', b, msg, only_if)

  def try_is_le(self, a, b, msg='', only_if=True):
    self.try_is(a, lambda a,b: a<=b, '<=', b, msg, only_if)

  def try_is_gt(self, a, b, msg='', only_if=True):
    self.try_is(a, lambda a,b: a>b, '>', b, msg, only_if)

  def try_is_ge(self, a, b, msg='', only_if=True):
    self.try_is(a, lambda a,b: a>=b, '>=', b, msg, only_if)

  def try_is_in(self, a, b, msg='', only_if=True):
    self.try_is(a, lambda a,b: a in b, 'in', b, msg, only_if)

  def warn_is_equal(self, a, b, msg='', only_if=True):
    try:
      self.try_is(a, lambda a,b: a==b, '==', b, msg, only_if)
      return True
    except Exception, exc:
      traceback.print_exc()
      print "\nERROR: assertion error\n"
      return False
    #

  def warn_is_contained(self, a, b, msg='', only_if=True):
    try:
      self.try_is(a, lambda a,b: a in b, 'contained in', b, msg, only_if)
      return True
    except Exception, exc:
      traceback.print_exc()
      print "\nERROR: assertion error\n"
      return False
    #

  def __str__(self):
      full = self.find_tst_name()
      runner,middle,test_name = full.split('.')
      klass_name = middle.split('_')[-1]
      return "%s.%s" % (klass_name,test_name)
  def find_tst_name(self):
    frame = sys._getframe()
    for frame in iter(lambda: frame.f_back, None):
      tn = frame.f_locals.get('testMethod',None)
      if tn:
          return str(tn.im_self)
    assert False, "Could not determine test name"


class GuiTestCaseBase(TestCaseBase):
  TIME_TO_WAIT = 10  # TODO factor out all the constants and delays and retries.
