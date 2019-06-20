"""
=========================================================================
 ProcVRTL_test.py
=========================================================================
 Includes test cases for the translated TinyRV0 processor.

Author : Shunning Jiang, Yanghui Ou
  Date : June 15, 2019
"""
import pytest
import random
random.seed(0xdeadbeef)

from pymtl3  import *
from harness import asm_test, assemble 
from examples.ex03_proc.ProcRTL import ProcRTL

#-------------------------------------------------------------------------
# ProcVRTL_Tests
#-------------------------------------------------------------------------
# It is as simple as inheriting from RTL tests and overwrite [run_sim]
# function to apply the translation and import pass.

from .ProcRTL_test import ProcRTL_Tests as BaseTests

class ProcVRTL_Tests( BaseTests ):

  def run_sim( s, th, gen_test, max_cycles=10000 ):

    th.elaborate()

    # Assemble the program
    mem_image = assemble( gen_test() )

    # Load the program into memory
    th.load( mem_image )

    # Translate the processor and import it back in
    from pymtl3.passes.yosys import TranslationPass, ImportPass

    th.proc.yosys_translate = True
    th.proc.yosys_import = True
    th.apply( TranslationPass() )
    th = ImportPass()( th )

    # Create a simulator and run simulation
    th.apply( SimulationPass )
    th.sim_reset()

    print()
    ncycles = 0
    while not th.done() and ncycles < max_cycles:
      th.tick()
      print("{:3}: {}".format( ncycles, th.line_trace() ))
      ncycles += 1

    # Force a test failure if we timed out
    assert ncycles < max_cycles

