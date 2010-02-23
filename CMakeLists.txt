 
cmake_minimum_required(VERSION 2.6)

project(sflvault-qt4)

## cmake includes and plugins
set(CMAKE_MODULE_PATH "${CMAKE_MODULE_PATH}"
                      "${CMAKE_CURRENT_SOURCE_DIR}/cmake/modules")

find_package(PyQt4 REQUIRED)

## Just include the subdirs
add_subdirectory(sflvault_qt)

#Umask workaround
execute_process(COMMAND "umask" "022")

## Install function

function(install_directory dir project_path source_path)
 
# Get the relative path to files
file(GLOB files RELATIVE "${source_path}" "${source_path}/${dir}/*")
foreach(file ${files})
  if(${file} MATCHES "\\.git")
    # No .git dirs
  else(${file} MATCHES "\\.git")
    if(IS_DIRECTORY "${source_path}/${file}")
      # Add recursivly
      install_directory("${file}" ${project_path} ${source_path})
    else(IS_DIRECTORY "${source_path}/${file}")
      # Install file
      if(${file} MATCHES "\\.pyc")
      else(${file} MATCHES "\\.pyc")
        #message(STATUS "FILES ${source_path}/${file} DESTINATION ${project_path}/${dir}")
        install(FILES "${source_path}/${file}" 
                DESTINATION "${project_path}/${dir}"
                PERMISSIONS OWNER_READ OWNER_WRITE
                            GROUP_READ
                            WORLD_READ)
      endif(${file} MATCHES "\\.pyc")
    endif(IS_DIRECTORY "${source_path}/${file}")
  endif(${file} MATCHES "\\.git")
endforeach(file)
endfunction()

##install
set(PROJECT_PATH "lib/python2.6/")

#main app
install_directory("sflvault_qt" ${PROJECT_PATH} 
                                ${CMAKE_CURRENT_SOURCE_DIR})

#images
install_directory("images" "share/sflvault-qt4/"
                           ${CMAKE_CURRENT_SOURCE_DIR})
#patching qicons
execute_process(COMMAND "patch" "-p0" "-o" "${CMAKE_BINARY_DIR}/qicons.py"
  WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/images/"
  INPUT_FILE "${CMAKE_CURRENT_SOURCE_DIR}/cmake/files/qicons.patch")

install(FILES ${CMAKE_BINARY_DIR}/qicons.py
        DESTINATION "share/sflvault-qt4/images/")

install(FILES ${CMAKE_CURRENT_SOURCE_DIR}/images/sflvault.png
        DESTINATION "share/pixmaps/")

#i18n
install_directory("i18n" "share/sflvault-qt4/"
                           ${CMAKE_CURRENT_SOURCE_DIR})

#lib
install_directory("lib" "share/sflvault-qt4/"
                           ${CMAKE_CURRENT_SOURCE_DIR})



#app launcher
install(FILES "cmake/files/sflvault-qt.desktop" 
        DESTINATION "share/applications"
        PERMISSIONS OWNER_READ OWNER_WRITE
                    GROUP_READ
                    WORLD_READ)

#startup script
install(PROGRAMS "sflvault-client-qt4.py"
        DESTINATION ${PROJECT_PATH}/sflvault_qt)

install(PROGRAMS "cmake/files/sflvault-client-qt4"
        DESTINATION "bin")


##Cpack stuff
set(CPACK_PACKAGE_VENDOR "Thibault Cohen")
set(CPACK_PACKAGE_VERSION_MAJOR "0")
set(CPACK_PACKAGE_VERSION_MINOR "9")
set(CPACK_PACKAGE_VERSION_PATCH "0")
set(CPACK_PACKAGE_VERSION "${CPACK_PACKAGE_VERSION_MAJOR}")
set(CPACK_PACKAGE_VERSION "${CPACK_PACKAGE_VERSION}.${CPACK_PACKAGE_VERSION_MINOR}")
set(CPACK_PACKAGE_VERSION "${CPACK_PACKAGE_VERSION}.${CPACK_PACKAGE_VERSION_PATCH}")

#debian related
set(CPACK_DEBIAN_PACKAGE_ARCHITECTURE "all")
set(CPACK_DEBIAN_PACKAGE_DEPENDS "sflvault-common")
set(CPACK_DEBIAN_PACKAGE_DEPENDS "${CPACK_DEBIAN_PACKAGE_DEPENDS}, python-qt4")
set(CPACK_DEBIAN_PACKAGE_MAINTAINER "Arthur Gautier <arthur.gautier@savoirfairelinux.com>")
set(CPACK_DEBIAN_PACKAGE_SECTION "Utils")
set(CPACK_DEBIAN_PACKAGE_VERSION "${CPACK_PACKAGE_VERSION}")

set(CPACK_PACKAGE_NAME "${CMAKE_PROJECT_NAME}")
set(CPACK_PACKAGE_FILE_NAME
"${CPACK_PACKAGE_NAME}-${CPACK_DEBIAN_PACKAGE_VERSION}")


set(CPACK_GENERATOR "DEB")

include(CPack)

