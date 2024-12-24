include_directories(
  "${VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/include"
)

#if(NOT VCPKG_HOST_TRIPLET)
#  message(FATAL_ERROR "WTF, VCPKG?")
#endif()

# centralize third party package finding here.
# remember to src/vcpkg/vcpkg port add <dependency>

# for header-only libraries just adding the find_package statement is enough
find_package(glm REQUIRED CONFIGURE)

# for link libraries will need to add something like
#   bng_add_link_libraries(PRIVATE DEP_NAME::DEP_NAME)
# to the CMakeLists.txt 
find_package(flatbuffers REQUIRED CONFIGURE)


# third party tools
set(BNG_VCPKG_TOOLS_BIN_DIR "${VCPKG_INSTALLED_DIR}/${VCPKG_HOST_TRIPLET}/tools")

set(Flatc_EXECUTABLE "${BNG_VCPKG_TOOLS_BIN_DIR}/flatbuffers/flatc${BNG_HOST_EXE_SUFFIX}")
function(Flatc WORKING_DIR)
  execute_process(COMMAND "${Flatc_EXECUTABLE}" ${ARGN}
    WORKING_DIRECTORY "${WORKING_DIR}" COMMAND_ERROR_IS_FATAL ANY)
endfunction()
if(NOT EXISTS "${Flatc_EXECUTABLE}")
  message(FATAL_ERROR "${Flatc_EXECUTABLE} does not exist.")
endif()
