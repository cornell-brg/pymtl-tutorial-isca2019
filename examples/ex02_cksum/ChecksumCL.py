"""
==========================================================================
ChecksumCL.py
==========================================================================
Cycle-level implementation of a checksum unit which implements a
simplified version of Fletcher's algorithm. A cycle-level model often
involves an input queue connected to the recv interface to buffer up the
input message and an update block to process each message and send it out
the send interface. In this case, we will simply reuse the checksum
function we developed in ChecksumFL to implement the desired
functionality. To model a latency greater than one, we can add a
DelayPipeDeqCL at the send interface. So instead of sending the result
directly out the send interface we enq the result into the DelayPipeDeqCL
and then wait for the result to appear on the other end of the
DelayPipeDeqCL before sending it out the send interface.

Author : Yanghui Ou
  Date : June 6, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.stdlib.cl.DelayPipeCL import DelayPipeDeqCL
from pymtl3.stdlib.cl.queues import PipeQueueCL

from .ChecksumFL import checksum
from .utils import b128_to_words

#-------------------------------------------------------------------------
# ChecksumCL
#-------------------------------------------------------------------------

class ChecksumCL( Component ):

  def construct( s ):

    s.recv = NonBlockingCalleeIfc( Bits128 )
    s.send = NonBlockingCallerIfc( Bits32  )

    # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''
    # Implement the checksum CL component
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
    # Instantiate a PipeQueueCL with one entry and connect it to the
    # recv interface. Then create an update block which will check if
    # the deq interface is ready and the send interface is ready. If
    # both of these conditions are try, then deq the message, calculate
    # the checksum using the checksum function from ChecksumFL, and
    # send the result through the send interface.

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.send )

