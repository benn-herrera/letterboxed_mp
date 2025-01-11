set(API_DIR "${CMAKE_CURRENT_SOURCE_DIR}")
set(GEN_API_NAME "bng_api")
set(API_DEF "${API_DIR}/${GEN_API_NAME}.json")

set(GEN_API_H_NAME "${GEN_API_NAME}.h")
set(GEN_API_H "${GEN_OUT_DIR}/${GEN_API_H_NAME}")
add_custom_command(
    OUTPUT "${GEN_API_H}"
    COMMAND "${Python_EXECUTABLE}" "${GenApiSources_SCRIPT}"
        generate-cpp-interface --api-def="${API_DEF}" --out-h="${GEN_API_H}"
    MAIN_DEPENDENCY "${API_DEF}"
    WORKING_DIRECTORY "${PROJECT_BINARY_DIR}"
)

set(ADDITIONAL_HEADERS "${GEN_API_H}")
include("${CMAKE_INCLUDE}/target_lib.cmake")

set_source_files_properties(
  "${GEN_API_H}"
  PROPERTIES
  GENERATED TRUE)

# export to project level
set(API_DIR "${API_DIR}" PARENT_SCOPE)
set(GEN_API_NAME "${GEN_API_NAME}" PARENT_SCOPE)
set(GEN_API_H_NAME "${GEN_API_H_NAME}" PARENT_SCOPE)
set(API_DEF "${API_DEF}" PARENT_SCOPE)
set(API_HEADERS "${HEADERS}" PARENT_SCOPE)
