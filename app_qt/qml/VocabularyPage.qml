import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        TextField {
            id: searchField
            Layout.fillWidth: true
            placeholderText: "Tìm từ (tiếng Anh hoặc tiếng Việt)..."
            color: "#3f3628"
            placeholderTextColor: "#b3a696"
            onTextChanged: vocabController.model.setFilter(text)

            background: Rectangle {
                radius: 10
                color: "#ffffff"
                border.color: searchField.activeFocus ? "#f97316" : "#e8dccb"
                border.width: 1
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ListView {
                model: vocabController.model
                spacing: 6

                delegate: Rectangle {
                    width: ListView.view.width
                    height: 48
                    radius: 10
                    color: "#ffffff"
                    border.color: "#f1e3d3"
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10

                        Text {
                            text: "✓"
                            color: "#16a34a"
                            font.pixelSize: 14
                            font.bold: true
                            visible: learned
                        }

                        Text {
                            text: english + " — " + vietnamese + "  ·  " + category + "  ·  " + level
                            color: "#3f3628"
                            font.pixelSize: 14
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }

                        AppButton {
                            text: "🔊"
                            small: true
                            onClicked: vocabController.speak(english)
                        }
                    }
                }
            }
        }
    }
}
