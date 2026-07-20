import QtQuick
import QtQuick.Controls

TextField {
    echoMode: TextInput.Password
    selectByMouse: true
    implicitHeight: 42
    leftPadding: 12
    rightPadding: 12
    font.family: "Segoe UI"
    font.pixelSize: 14

    background: Rectangle {
        radius: 10
        color: "#FFFFFF"
        border.color: parent.activeFocus ? "#F6B26B" : "#E8E8E8"
        border.width: 1
    }
}
