import QtQuick
import QtQuick.Controls

ApplicationWindow {
    id: window
    width: 1120
    height: 740
    minimumWidth: 860
    minimumHeight: 600
    visible: true
    title: "AI-English"
    color: "#fff8f1"

    property bool started: false

    Loader {
        id: shellLoader
        anchors.fill: parent
        source: window.started ? "AppShell.qml" : "WelcomePage.qml"

        onLoaded: {
            item.opacity = 0
            fadeInAnim.start()
        }

        NumberAnimation {
            id: fadeInAnim
            target: shellLoader.item
            property: "opacity"
            to: 1
            duration: 260
            easing.type: Easing.OutCubic
        }
    }

    Connections {
        target: shellLoader.item
        ignoreUnknownSignals: true

        function onStartRequested() {
            window.started = true
        }
    }
}
