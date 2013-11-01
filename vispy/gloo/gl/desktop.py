# -*- coding: utf-8 -*-
# Copyright (c) 2013, Vispy Development Team.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

""" vispy.gloo.gl.desktop: namespace for OpenGL ES 2.0 API based on the
desktop OpenGL implementation.
"""

from __future__ import print_function, division, absolute_import

from OpenGL import GL as _GL
import OpenGL.GL.framebufferobjects as FBO

from . import _desktop, _desktop_ext

# Prepare namespace with constants and ext
from ._constants import *
ext = _desktop_ext



def _make_unavailable_func(funcname):
    def cb(*args, **kwds):
       raise RuntimeError('OpenGL API call "%s" is not available.' % funcname)
    return cb


def _get_function_from_pyopengl(funcname):
    """ Try getting the given function from PyOpenGL, return
    a dummy function (that prints a warning when called) if it 
    could not be found.
    """
    func = None
    # Get function from GL
    try:
        func = getattr(_GL, funcname)
    except AttributeError:
        # Get function from FBO

        try:
            func = getattr(FBO, funcname)
        except AttributeError:
            # Some functions are known by a slightly different name
            # e.g. glDepthRangef, glDepthRangef
            if funcname.endswith('f'):
                try:
                    func = getattr(_GL, funcname[:-1])
                except AttributeError:
                    pass
    
    # Set dummy function if we could not find it
    if func is None:
        func = _make_unavailable_func(funcname)
        if True or show_warnings:  
            print('warning: %s not available' % funcname )
    return func


def _inject():
    """ Get GL functions from pyopengl. Inject in *this* namespace
    and the ext namespace.
    Note the similatity with vispy.gloo.gl.use().
    """
    import vispy
    show_warnings = vispy.config['show_warnings']
    import OpenGL.GL.framebufferobjects as FBO
    
    # Import functions here
    NS = globals()
    funcnames = _desktop._glfunctions
    for name in funcnames:
        func = _get_function_from_pyopengl(name)
        NS[name] = func
    
    # Import functions in ext
    NS = ext.__dict__
    funcnames = _desktop_ext._glfunctions
    for name in funcnames:
        func = _get_function_from_pyopengl(name)
        NS[name] = func


def _fix():
    """ Apply some fixes and patches.
    """
    NS = globals()
    # Fix glGetActiveAttrib, since if its just the ctypes function
    if (    'glGetActiveAttrib' in NS and 
            hasattr(NS['glGetActiveAttrib'], 'restype') ):
        import ctypes
        def new_glGetActiveAttrib(program, index):
            # Prepare
            bufsize = 32
            length = ctypes.c_int()
            size = ctypes.c_int()
            type = ctypes.c_int()
            name = ctypes.create_string_buffer(bufsize)
            # Call
            _GL.glGetActiveAttrib(program, index, 
                    bufsize, ctypes.byref(length), ctypes.byref(size), 
                    ctypes.byref(type), name)
            # Return Python objects
            #return name.value.decode('utf-8'), size.value, type.value
            return name.value, size.value, type.value
        
        # Patch
        NS['glGetActiveAttrib'] = new_glGetActiveAttrib
    
    
    # Monkey-patch pyopengl to fix a bug in glBufferSubData
    import sys
    if sys.version_info > (3,):
        buffersubdatafunc = NS['glBufferSubData']
        if hasattr(buffersubdatafunc, 'wrapperFunction'):
            buffersubdatafunc = buffersubdatafunc.wrapperFunction
        _m = sys.modules[buffersubdatafunc.__module__]
        _m.long = int


# Apply
_inject()
_fix()
