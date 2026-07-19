import QtQuick
import QtQuick.Controls

BusyIndicator {
    id: spinner
    property color tint: "#f97316"
    implicitWidth: 36
    implicitHeight: 36

    contentItem: Item {
        implicitWidth: 36
        implicitHeight: 36

        Repeater {
            model: 8

            delegate: Rectangle {
                width: 4
                height: 4
                radius: 2
                color: spinner.tint
                opacity: 0.25 + 0.75 * (index / 7)
                x: parent.width / 2 - width / 2
                    + Math.cos(index / 8 * 2 * Math.PI) * (parent.width / 2 - 4)
                y: parent.height / 2 - height / 2
                    + Math.sin(index / 8 * 2 * Math.PI) * (parent.height / 2 - 4)
            }
        }

        RotationAnimation on rotation {
            running: spinner.running
            loops: Animation.Infinite
            from: 0
            to: 360
            duration: 900
        }
    }
}
