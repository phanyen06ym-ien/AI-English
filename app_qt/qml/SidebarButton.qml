import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Button {
    id: control
    property bool active: false
    property string hint: ""
    Layout.fillWidth: true
    implicitHeight: 46

    ToolTip.visible: hovered && hint !== ""
    ToolTip.delay: 500
    ToolTip.text: hint

    background: Rectangle {
        radius: 10
        color: control.active ? "#ffedd5"
             : (control.pressed ? "#ffe8d1" : (control.hovered ? "#fff3e4" : "transparent"))
        Behavior on color { ColorAnimation { duration: 120 } }
    }

    contentItem: Text {
        text: control.text
        color: control.active ? "#c2410c" : "#5f5546"
        font.pixelSize: 15
        font.bold: control.active
        leftPadding: 14
        verticalAlignment: Text.AlignVCenter
        Behavior on color { ColorAnimation { duration: 150 } }
    }
}
