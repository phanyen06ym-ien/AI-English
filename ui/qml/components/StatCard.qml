import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Card {
    id: card
    property string title: ""
    property string value: ""
    property string helper: ""

    Layout.preferredHeight: 118

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 6

        Label {
            text: card.title
            color: "#777777"
            font.family: "Segoe UI"
            font.pixelSize: 13
            elide: Text.ElideRight
            Layout.fillWidth: true
        }

        Label {
            text: card.value
            color: "#222222"
            font.family: "Segoe UI"
            font.pixelSize: 25
            font.bold: true
            elide: Text.ElideRight
            Layout.fillWidth: true
        }

        Label {
            text: card.helper
            visible: card.helper.length > 0
            color: "#777777"
            font.family: "Segoe UI"
            font.pixelSize: 12
            elide: Text.ElideRight
            Layout.fillWidth: true
        }
    }
}
