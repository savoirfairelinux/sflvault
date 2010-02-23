# Try to find PyQt4 utilities, pyuic4 and pyrcc4:
# PYUIC4BINARY - Location of pyuic4 executable
# PYRCC4BINARY - Location of pyrcc4 executable
# PyQt4_FOUND - PyQt4 utilities found.

# Also provides macro similar to FindQt4.cmake's WRAP_UI and WRAP_RC,
# for the automatic generation of Python code from Qt4's user interface
# ('.ui') and resource ('.qrc') files. These macros are called:
# - PYQT4_WRAP_UI
# - PYQT4_WRAP_RC

IF(PYUIC4BINARY AND PYRCC4BINARY)
  # Already in cache, be silent
  set(PyQt4_FIND_QUIETLY TRUE)
ENDIF(PYUIC4BINARY AND PYRCC4BINARY)

FIND_PROGRAM(PYUIC4BINARY pyuic4)
FIND_PROGRAM(PYRCC4BINARY pyrcc4)

MACRO(PYQT4_WRAP_UI outfiles)
  FOREACH(it ${ARGN})
    GET_FILENAME_COMPONENT(outfile ${it} NAME_WE)
    GET_FILENAME_COMPONENT(infile ${it} ABSOLUTE)
    SET(outfile ${CMAKE_CURRENT_BINARY_DIR}/ui_${outfile}.py)
    ADD_CUSTOM_TARGET(${it} ALL
      DEPENDS ${outfile}
    )
    ADD_CUSTOM_COMMAND(OUTPUT ${outfile}
      COMMAND ${PYUIC4BINARY} ${infile} -o ${outfile}
      MAIN_DEPENDENCY ${infile}
    )
    SET(${outfiles} ${${outfiles}} ${outfile})
  ENDFOREACH(it)
ENDMACRO (PYQT4_WRAP_UI)

MACRO(PYQT4_WRAP_RC outfiles)
  FOREACH(it ${ARGN})
    GET_FILENAME_COMPONENT(outfile ${it} NAME_WE)
    GET_FILENAME_COMPONENT(infile ${it} ABSOLUTE)
    SET(outfile ${CMAKE_CURRENT_BINARY_DIR}/${outfile}_rc.py)
    ADD_CUSTOM_TARGET(${it} ALL
      DEPENDS ${outfile}
    )
    ADD_CUSTOM_COMMAND(OUTPUT ${outfile}
      COMMAND ${PYRCC4BINARY} ${infile} -o ${outfile}
      MAIN_DEPENDENCY ${infile}
    )
    SET(${outfiles} ${${outfiles}} ${outfile})
  ENDFOREACH(it)
ENDMACRO (PYQT4_WRAP_RC)

IF(EXISTS ${PYUIC4BINARY} AND EXISTS ${PYRCC4BINARY})
   set(PyQt4_FOUND TRUE)
ENDIF(EXISTS ${PYUIC4BINARY} AND EXISTS ${PYRCC4BINARY})

if(PyQt4_FOUND)
  if(NOT PyQt4_FIND_QUIETLY)
    message(STATUS "Found PyQt4: ${PYUIC4BINARY}, ${PYRCC4BINARY}")
  endif(NOT PyQt4_FIND_QUIETLY)
endif(PyQt4_FOUND)
