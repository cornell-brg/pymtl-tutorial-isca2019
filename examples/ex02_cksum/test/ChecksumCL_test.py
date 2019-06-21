"""
==========================================================================
 ChecksumCL_test.py
==========================================================================
Test cases for CL checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""
from __future__ import absolute_import, division, print_function

import hypothesis
from hypothesis import strategies as st
from pymtl3.datatypes import strategies as pm_st

from pymtl3 import *
from pymtl3.stdlib.cl.queues import BypassQueueCL
from pymtl3.stdlib.test import TestSinkCL, TestSrcCL

from ..ChecksumCL import ChecksumCL
from ..ChecksumFL import checksum
from ..utils import b128_to_words, words_to_b128

#-------------------------------------------------------------------------
# WrappedChecksumCL
#-------------------------------------------------------------------------
# WrappedChecksumCL is a simple wrapper around the CL checksum unit. It
# simply appends an output queue to the send side of the checksum unit.
# In this way it only exposes callee interfaces which can be directly
# called by the outside world.

class WrappedChecksumCL( Component ):

  def construct( s, DutType=ChecksumCL ):
    s.recv = NonBlockingCalleeIfc( Bits128 )
    s.give = NonBlockingCalleeIfc( Bits32  )

    s.checksum_unit = DutType()
    s.out_q = BypassQueueCL( num_entries=1 )

    s.connect( s.recv,               s.checksum_unit.recv )
    s.connect( s.checksum_unit.send, s.out_q.enq          )
    s.connect( s.out_q.deq,          s.give               )

#-------------------------------------------------------------------------
# Wrap CL component into a function
#-------------------------------------------------------------------------
# [checksum_cl] takes a list of 16-bit words, converts it to bits, creates
# a checksum unit instance and feed in the input. It then ticks the
# checksum unit until the output is ready to be taken.

def checksum_cl( words ):

  # Create a simulator
  dut = WrappedChecksumCL()
  dut.elaborate()
  dut.apply( SimulationPass )

  # Wait until recv ready
  while not dut.recv.rdy():
    dut.tick()

  # Call recv on dut
  dut.recv( words_to_b128( words ) )
  dut.tick()

  # Wait until dut is ready to give result
  while not dut.give.rdy():
    dut.tick()

  return dut.give()

#-------------------------------------------------------------------------
# Reuse FL tests
#-------------------------------------------------------------------------
# By directly inhering from the FL test class, we can easily reuse all the
# FL tests. We only need to overwrite the cksum_func that is used in all
# test cases. Here we also extend the test case by adding a hypothesis
# test that compares the CL implementation against the FL as reference.

from .ChecksumFL_test import ChecksumFL_Tests as BaseTests

class ChecksumCL_Tests( BaseTests ):
  def cksum_func( s, words ):
    return checksum_cl( words )

  # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''
  # Use Hypothesis to test Checksum CL
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
  # Use Hypothesis to verify that ChecksumCL has the same behavior as
  # ChecksumFL. Simply uncomment the following test_hypothesis method
  # and rerun pytest. Make sure that you fix the indentation so that
  # this new test_hypothesis method is correctly indented with respect
  # to the class ChecksumCL_Tests
  #
  #   @hypothesis.given(
  #     words = st.lists( pm_st.bits(16), min_size=8, max_size=8 )
  #   )
  #   @hypothesis.settings( deadline=None )
  #   def test_hypothesis( s, words ):
  #     print( [ int(x) for x in words ] )
  #     assert s.cksum_func( words ) == checksum( words )
  #
  # This new test uses Hypothesis to generate random inputs, then uses
  # the checksum_cl to run a little simulation and compares the output to
  # the checksum function from ChecksumFL.
  #
  # To really see Hypothesis in action, go back to ChecksumCL and
  # corrupt one word of the input by forcing it to always be zero. For
  # example, change the update block in the CL implementation to be
  # something like this:
  #
  #   @s.update
  #   def up_checksum_cl():
  #     if s.pipe.enq.rdy() and s.in_q.deq.rdy():
  #       bits = s.in_q.deq()
  #       words = b128_to_words( bits )
  #       words[5] = b16(0) # <--- INJECT A BUG!
  #       result = checksum( words )
  #       s.pipe.enq( result ) !\vspace{0.07in}!
  #     if s.send.rdy() and s.pipe.deq.rdy():
  #       s.send( s.pipe.deq() )

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------
# TestHarness is used for more advanced source/sink based testing. It
# hooks a test source to the input of the design under test and a test
# sink to the output of the DUT. Test source feeds data into the DUT
# while test sink drains data from the DUT and verifies it.

class TestHarness( Component ):
  def construct( s, DutType, src_msgs, sink_msgs ):

    s.src  = TestSrcCL( Bits128, src_msgs )
    s.dut  = DutType()
    s.sink = TestSinkCL( Bits32, sink_msgs )

    s.connect_pairs(
      s.src.send, s.dut.recv,
      s.dut.send, s.sink.recv,
    )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{}>{}>{}".format(
      s.src.line_trace(), s.dut.line_trace(), s.sink.line_trace()
    )

#=========================================================================
# Src/sink based tests
#=========================================================================
# We use source/sink based tests to stress test the checksum unit.

class ChecksumCLSrcSink_Tests( object ):

  #-----------------------------------------------------------------------
  # setup_class
  #-----------------------------------------------------------------------
  # Will be called by pytest before running all the tests in the test
  # class. Here we specify the type of the design under test that is used
  # in all test cases. We can easily reuse all the tests in this class
  # simply by creating a new test class that inherits from this class and
  # overwrite the setup_class to provide a different DUT type.

  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumCL

  #-----------------------------------------------------------------------
  # run_sim
  #-----------------------------------------------------------------------
  # A helper function in the test suite that creates a simulator and
  # runs test. We can overwrite this function when inheriting from the
  # test class to apply different passes to the DUT.

  def run_sim( s, th, max_cycles=1000 ):

    # Create a simulator
    th.elaborate()
    th.apply( SimulationPass )
    ncycles = 0
    th.sim_reset()
    print( "" )

    # Tick the simulator
    print("{:3}: {}".format( ncycles, th.line_trace() ))
    while not th.done() and ncycles < max_cycles:
      th.tick()
      ncycles += 1
      print("{:3}: {}".format( ncycles, th.line_trace() ))

    # Check timeout
    assert ncycles < max_cycles

  #-----------------------------------------------------------------------
  # test_simple
  #-----------------------------------------------------------------------
  # is a simple test case with only 1 input.

  def test_srcsink_simple( s ):
    words = [ b16(x) for x in [ 1, 2, 3, 4, 5, 6, 7, 8 ] ]
    bits  = words_to_b128( words )

    result = b32( 0x00780024 )

    src_msgs  = [ bits   ]
    sink_msgs = [ result ]

    th = TestHarness( s.DutType, src_msgs, sink_msgs )
    s.run_sim( th )

  #-----------------------------------------------------------------------
  # test_pipeline
  #-----------------------------------------------------------------------
  # test the checksum unit with a sequence of inputs.

  def test_srcsink_pipeline( s ):
    words0  = [ b16(x) for x in [ 1, 2, 3, 4, 5, 6, 7, 8 ] ]
    words1  = [ b16(x) for x in [ 8, 7, 6, 5, 4, 3, 2, 1 ] ]
    bits0   = words_to_b128( words0 )
    bits1   = words_to_b128( words1 )

    result0 = b32( 0x00780024 )
    result1 = b32( 0x00cc0024 )

    src_msgs  = [ bits0, bits1, bits0, bits1 ]
    sink_msgs = [ result0, result1, result0, result1 ]

    th = TestHarness( s.DutType, src_msgs, sink_msgs )
    s.run_sim( th )

  #-----------------------------------------------------------------------
  # test_backpressure
  #-----------------------------------------------------------------------
  # test the checksum unit with a large sink delay.

  def test_srcsink_backpressure( s ):
    words0  = [ b16(x) for x in [ 1, 2, 3, 4, 5, 6, 7, 8 ] ]
    words1  = [ b16(x) for x in [ 8, 7, 6, 5, 4, 3, 2, 1 ] ]
    result0 = b32( 0x00780024 )
    result1 = b32( 0x00cc0024 )

    bits0 = words_to_b128( words0 )
    bits1 = words_to_b128( words1 )

    src_msgs  = [ bits0, bits1, bits0, bits1 ]
    sink_msgs = [ result0, result1, result0, result1 ]

    th = TestHarness( s.DutType, src_msgs, sink_msgs )
    th.set_param( "top.sink.construct", initial_delay=10 )
    s.run_sim( th )


