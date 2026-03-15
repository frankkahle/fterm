cmake_minimum_required(VERSION 3.16)
project(SOSterm VERSION 2.2.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

find_package(Qt5 REQUIRED COMPONENTS Widgets Network Svg)
find_package(qtermwidget5 REQUIRED)

configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/src/version.h.in
    ${CMAKE_CURRENT_BINARY_DIR}/version.h
)

set(SOURCES
    src/main.cpp
    src/settings.cpp
    src/thememanager.cpp
    src/sessiontabmanager.cpp
    src/mainwindow.cpp
    src/sshsessionstore.cpp
    src/sshsidebar.cpp
    src/sshdialogs.cpp
    src/preferencesdialog.cpp
    src/sessionmanager.cpp
    src/splashscreen.cpp
    src/updatechecker.cpp
)

set(HEADERS
    src/settings.h
    src/thememanager.h
    src/sessiontabmanager.h
    src/mainwindow.h
    src/sshsessionstore.h
    src/sshsidebar.h
    src/sshdialogs.h
    src/preferencesdialog.h
    src/sessionmanager.h
    src/splashscreen.h
    src/updatechecker.h
)

set(RESOURCES
    resources/SOSterm.qrc
)

add_executable(SOSterm ${SOURCES} ${HEADERS} ${RESOURCES})

target_include_directories(SOSterm PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_BINARY_DIR}
)

target_link_libraries(SOSterm PRIVATE
    Qt5::Widgets
    Qt5::Network
    Qt5::Svg
    qtermwidget5
)

# Install targets
install(TARGETS SOSterm DESTINATION /opt/SOSterm)
install(DIRECTORY colorschemes/ DESTINATION /opt/SOSterm/colorschemes)
install(DIRECTORY resources/ DESTINATION /opt/SOSterm/resources
    FILES_MATCHING PATTERN "*.svg" PATTERN "*.png")
install(FILES SOSterm.desktop DESTINATION /usr/share/applications)
install(FILES resources/SOSterm.svg DESTINATION /usr/share/icons/hicolor/scalable/apps)
