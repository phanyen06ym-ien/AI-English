import QtQuick
import QtQuick.Controls

Button {
    id: control
    property bool small: false
    implicitHeight: small ? 34 : 42
    implicitWidth: small ? 42 : implicitContentWidth + 36
    scale: control.pressed ? 0.96 : 1.0
    opacity: control.enabled ? 1.0 : 0.5

    Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutQuad } }
    Behavior on opacity { NumberAnimation { duration: 120 } }

    background: Rectangle {
        radius: 8
        color: control.pressed ? "#ea580c" : (control.hovered ? "#fb923c" : "#f97316")
        Behavior on color { ColorAnimation { duration: 120 } }
    }

    contentItem: Text {
        text: control.text
        color: "white"
        font.pixelSize: small ? 16 : 14
        font.bold: !small
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
