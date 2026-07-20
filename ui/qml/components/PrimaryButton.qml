import QtQuick
import QtQuick.Controls

Button {
    id: control
    implicitWidth: 128
    implicitHeight: 40
    padding: 0

    background: Rectangle {
        radius: 10
        color: !control.enabled ? "#EFEFEF" : (control.hovered || control.down ? "#F3A24F" : "#F6B26B")
        border.color: "transparent"
    }

    contentItem: Text {
        text: control.text
        color: control.enabled ? "#222222" : "#999999"
        font.family: "Segoe UI"
        font.pixelSize: 14
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
