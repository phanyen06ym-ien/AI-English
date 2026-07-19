import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        RowLayout {
            Layout.fillWidth: true

            Text {
                text: "Lịch sử nhận diện"
                color: "#3f3628"
                font.pixelSize: 18
                font.bold: true
                Layout.fillWidth: true
            }

            LoadingSpinner {
                implicitWidth: 22
                implicitHeight: 22
                running: historyController.loading
                visible: historyController.loading
            }

            AppButton {
                text: "Xóa lịch sử"
                enabled: !historyController.loading
                onClicked: historyController.clearHistory()
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ListView {
                id: historyListView
                model: historyController.model
                spacing: 6

                populate: Transition {
                    SequentialAnimation {
                        PauseAnimation { duration: Math.min(ViewTransition.index, 12) * 18 }
                        ParallelAnimation {
                            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 220; easing.type: Easing.OutCubic }
                            NumberAnimation { property: "scale"; from: 0.96; to: 1; duration: 220; easing.type: Easing.OutCubic }
                        }
                    }
                }

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
                            text: english + " — " + vietnamese + "  ·  " + category + "  ·  " + detectedTime
                            color: "#3f3628"
                            font.pixelSize: 14
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }

                        AppButton {
                            text: "🔊"
                            small: true
                            onClicked: historyController.speak(english)
                        }
                    }
                }

                Text {
                    anchors.centerIn: parent
                    visible: historyListView.count === 0 && !historyController.loading
                    text: "Chưa có lịch sử nhận diện nào."
                    color: "#a4988a"
                }

                Text {
                    anchors.centerIn: parent
                    visible: historyListView.count === 0 && historyController.loading
                    text: "Đang tải lịch sử..."
                    color: "#a4988a"
                }
            }
        }
    }
}
