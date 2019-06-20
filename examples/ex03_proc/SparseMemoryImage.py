#=========================================================================
# SparseMemoryImage
#=========================================================================
# This is a basic class representing a sparse memory image using
# "sections" and "symbols". Sections are tuples of <name,addr,data> where
# the addr specifies where the data lives in a flat memory space. Symbols
# are simply name to address mappings.
#
# Author : Christopher Batten
# Date   : May 20, 2014

from __future__ import absolute_import, division, print_function

import binascii
import struct


class SparseMemoryImage (object):

  #-----------------------------------------------------------------------
  # Nested Class: Section
  #-----------------------------------------------------------------------

  class Section (object):

    def __init__( self, name="", addr=0x00000000, data=bytearray() ):
      self.name = name
      self.addr = addr
      self.data = data

    def __str__( self ):
      return "{}: addr={} data={}" \
        .format( self.name, hex(self.addr), binascii.hexlify(self.data) )

    def __eq__( self, other ):
      return     self.name == other.name \
             and self.addr == other.addr \
             and self.data == other.data

  #-----------------------------------------------------------------------
  # Constructor
  #-----------------------------------------------------------------------

  def __init__( self ):
    self.sections = []
    self.symbols  = {}

  #-----------------------------------------------------------------------
  # add/get sections
  #-----------------------------------------------------------------------

  def add_section( self, section, addr=None, data=None ):
    if isinstance( section, SparseMemoryImage.Section ):
      self.sections.append( section )
    else:
      sec = SparseMemoryImage.Section( section, addr, data )
      self.sections.append( sec )

  def get_section( self, section_name ):
    for section in self.sections:
      if section_name == section.name:
        return section
    raise KeyError( "Could not find section {}!", section_name )

  def get_sections( self ):
    return self.sections

  #-----------------------------------------------------------------------
  # print_section_table
  #-----------------------------------------------------------------------

  def print_section_table( self ):
    idx = 0
    print( "Idx Name           Addr     Size" )
    for section in self.sections:
      print( "{:>3} {:<14} {:0>8x} {}" \
        .format( idx, section.name, section.addr, len(section.data) ) )
      idx += 1

  #-----------------------------------------------------------------------
  # add/get symbols
  #-----------------------------------------------------------------------

  def add_symbol( self, symbol_name, symbol_addr ):
    self.symbols[ symbol_name ] = symbol_addr

  def get_symbol( self, symbol_name ):
    return self.symbols[ symbol_name ]

  #-----------------------------------------------------------------------
  # equality
  #-----------------------------------------------------------------------

  def __eq__( self, other ):
    return     self.sections == other.sections \
           and self.symbols  == other.symbols

  #-----------------------------------------------------------------------
  # print_symbol_table
  #-----------------------------------------------------------------------

  def print_symbol_table( self ):
    for key,value in self.symbols.iteritems():
      print( " {:0>8x} {}".format( value, key ) )

#-------------------------------------------------------------------------
# mk_section
#-------------------------------------------------------------------------
# Helper function to make a section from a list of words.

def mk_section( name, addr, words ):
  data = bytearray()
  for word in words:
    data.extend(struct.pack("<I",word))

  return SparseMemoryImage.Section( name, addr, data )
