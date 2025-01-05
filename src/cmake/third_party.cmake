include(cmake/third_party_macros.cmake)

#find_package(flatbuffers REQUIRED CONFIGURE)


# third party tools
#set(Flatc_EXECUTABLE "${BNG_VCPKG_TOOLS_BIN_DIR}/flatbuffers/flatc${BNG_HOST_EXE_SUFFIX}")
#function(Flatc WORKING_DIR)
#  execute_process(COMMAND "${Flatc_EXECUTABLE}" ${ARGN}
#    WORKING_DIRECTORY "${WORKING_DIR}" COMMAND_ERROR_IS_FATAL ANY)
#endfunction()
#if(NOT EXISTS "${Flatc_EXECUTABLE}")
#  message(FATAL_ERROR "${Flatc_EXECUTABLE} does not exist.")
#endif()
