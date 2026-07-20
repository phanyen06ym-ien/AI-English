import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Item {
    id: page
    property string statusText: ""

    Connections {
        target: historyController

        function onStatusChanged(message) {
            page.statusText = message
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 16

        RowLayout {
            Layout.fillWidth: true

            SectionTitle {
                text: "Lịch sử nhận diện"
                Layout.fillWidth: true
            }

            PrimaryButton {
                text: historyController && historyController.loading ? "Đang tải..." : "Làm mới"
                enabled: historyController && !historyController.loading
                onClicked: historyController.refresh()
            }

            PrimaryButton {
                text: "Xóa lịch sử"
                enabled: historyController && !historyController.loading
                onClicked: {
                    historyController.clearHistory()
                    statsController.refresh()
                }
            }
        }

        Card {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 0

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 42

                    Label { text: "English"; color: "#777777"; font.bold: true; Layout.preferredWidth: 180 }
                    Label { text: "Vietnamese"; color: "#777777"; font.bold: true; Layout.fillWidth: true }
                    Label { text: "Confidence"; color: "#777777"; font.bold: true; Layout.preferredWidth: 130 }
                    Label { text: "Time"; color: "#777777"; font.bold: true; Layout.preferredWidth: 170 }
                }

                Divider { Layout.fillWidth: true }

                ListView {
                    id: historyList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: historyController ? historyController.model : null

                    delegate: Rectangle {
                        width: ListView.view.width
                        height: 54
                        color: "transparent"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 4
                            anchors.rightMargin: 4

                            Label { text: english; color: "#222222"; font.bold: true; elide: Text.ElideRight; Layout.preferredWidth: 176 }
                            Label { text: vietnamese; color: "#777777"; elide: Text.ElideRight; Layout.fillWidth: true }
                            Label { text: Number(confidence || 0).toFixed(2); color: "#777777"; Layout.preferredWidth: 130 }
                            Label { text: detectedTime || ""; color: "#777777"; elide: Text.ElideRight; Layout.preferredWidth: 170 }
                        }

                        Divider {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                        }
                    }
                }

                Label {
                    visible: historyList.count === 0 && historyController && !historyController.loading
                    text: "Chưa có dữ liệu"
                    color: "#777777"
                    font.family: "Segoe UI"
                    font.pixelSize: 17
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                    Layout.preferredHeight: 80
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }
    }
}
