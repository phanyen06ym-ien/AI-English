import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Button {
    id: control
    property bool selected: false

    Layout.fillWidth: true
    implicitHeight: 44
    padding: 0

    background: Rectangle {
        radius: 10
        color: control.selected ? "#FBE4CA" : (control.hovered ? "#FFF4E8" : "transparent")
    }

    contentItem: Text {
        text: control.text
        color: control.enabled ? "#222222" : "#AAAAAA"
        font.family: "Segoe UI"
        font.pixelSize: 15
        font.bold: control.selected
        verticalAlignment: Text.AlignVCenter
        leftPadding: 14
        rightPadding: 10
        elide: Text.ElideRight
    }
}
